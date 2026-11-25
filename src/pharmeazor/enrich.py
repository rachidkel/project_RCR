"""Recherche enrichie (Semaine 3, L4) : variantes de requête, boost et graphe.

Trois signaux s'ajoutent à la recherche brute de la semaine 2, sans la modifier :

1. Variantes de requête (``normalize=True``) : la question brute, sa réécriture
   canonique (DCI) et sa réécriture par classes (AINS, IEC...), issues de
   ``query.analyze_query`` (L2). Chaque variante est classée, puis les listes
   sont fusionnées par RRF.
2. Boost par métadonnées (``normalize=True``) : un chunk dont les métadonnées
   citent une entité de la question remonte (fiche DCI d'un registre, paire
   substance/cible du Thésaurus).
3. Expansion par le graphe (``expand=True``) : les interactions du graphe (L3)
   reliant les entités de la question sont converties en ``chunk_id`` du corpus
   et injectées comme une liste classée supplémentaire.

Chaque résultat porte ses ``signals`` : on sait toujours pourquoi un passage est
remonté. Une preuve indirecte (classe voisine) est marquée ``related_class`` et
ne doit jamais être présentée comme une interaction directe.
"""
from __future__ import annotations

import json
import math
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

from .config import CORPUS_PATH, PROCESSED
from .textnorm import norm

GRAPH_JSON = PROCESSED / "week_3" / "knowledge_graph.json"

# Termes d'intention ajoutés par L2 : utiles pour BM25 sur la question brute,
# mais ils noient les variantes canoniques.
INTENT_TERMS = {"POSOLOGIE", "DOSAGE", "CONTRE-INDICATION", "EFFETS INDESIRABLES",
                "INTERACTION MEDICAMENTEUSE"}

# Classes trop larges pour servir de preuve « voisine » (des centaines de membres).
GENERIC_CLASSES = {
    "MEDICAMENTS ABAISSANT LA PRESSION ARTERIELLE",
    "HYPERKALIEMIANTS",
}

# Valeurs de boost, à l'échelle d'un score RRF (1/(60+1) ≈ 0,016 au rang 1).
BOOST = {
    "registry_exact": 0.020,     # fiche DCI du registre = DCI de la question
    "registry_partial": 0.003,   # association contenant la DCI
    "thesaurus_pair": 0.030,     # substance ET cible = deux entités distinctes
    "thesaurus_side": 0.004,     # la DCI de la question est d'un seul côté
    "anpp_section": 0.020,       # RCP ANPP de la DCI, section demandée
    "anpp_product": 0.010,       # RCP du produit dont la marque est citée
    "graph_direct": 0.030,       # interaction du graphe entre les entités
    "graph_class": 0.025,        # même chose, via une classe
    "graph_related_class": 0.015,  # preuve indirecte (classe voisine) : à signaler
}

# Poids RRF des variantes : la question brute reste la référence.
VARIANT_WEIGHT = {"raw": 1.0, "canonical": 0.6, "classes": 0.4}

# Les fiches des registres répondent aux questions d'identité (marques, formes,
# dosages), pas aux questions d'interaction.
NO_REGISTRY_INTENTS = {"interaction", "contraindication"}
REGISTRY_PREFIXES = ("nomenclature", "nomenclature_dz", "pharmnet", "dwa")
# Mots qui signalent une question d'identité (ce que les registres savent dire).
REGISTRY_WORDS = ("marque", "nom commercial", "forme", "dosage", "dci", "enregistr",
                  "equivalent", "rupture", "generique", "disponible", "classe", "commercialise",
                  "laboratoire", "posologie", "dose")


def wants_registry(analysis) -> bool:
    if analysis is None or analysis.intent in NO_REGISTRY_INTENTS:
        return False
    qn = norm(analysis.raw)
    return analysis.intent == "dosage" or any(w in qn for w in REGISTRY_WORDS)

# Mot de la question -> sections du RCP (numérotation ANPP).
SECTION_KEYWORDS = {
    "indication": ("4.1",),
    "posologie": ("4.2",), "dose": ("4.2",), "dosage": ("4.2", "1.1"),
    "administration": ("4.2",),
    "contre indi": ("4.3",),
    "mise en garde": ("4.4",), "mises en garde": ("4.4",), "precaution": ("4.4",),
    "interaction": ("4.5",), "associer": ("4.5",),
    "grossesse": ("4.6",), "enceinte": ("4.6",), "allaitement": ("4.6",),
    "effet indesirable": ("4.8",), "effets indesirables": ("4.8",),
    "effets secondaires": ("4.8",),
    "surdosage": ("4.9",),
}
INTENT_SECTIONS = {"dosage": ("4.2",), "contraindication": ("4.3",), "interaction": ("4.5",)}


def wanted_sections(query_norm: str, intent: str) -> set[str]:
    found = {sec for kw, secs in SECTION_KEYWORDS.items() if kw in query_norm for sec in secs}
    return found or set(INTENT_SECTIONS.get(intent, ()))


LEVEL_RANK = {"contre indication": 0, "association deconseillee": 1,
              "precaution d emploi": 2, "a prendre en compte": 3}


def _level_rank(level: str) -> int:
    key = norm(level)
    return min((r for name, r in LEVEL_RANK.items() if name in key), default=4)


# ---------------------------------------------------------------- variantes
def build_variants(raw: str, analysis) -> list[tuple[str, str]]:
    """Renvoie [(nom, texte)] : brute, canonique (DCI), classes."""
    variants = [("raw", raw)]
    if analysis is None or not analysis.entities:
        return variants
    dcis = [ent.dci for ent in analysis.entities if ent.dci]
    classes = [t for t in analysis.expanded_terms
               if t not in INTENT_TERMS and t not in dcis and t not in GENERIC_CLASSES]
    qn = norm(raw)
    section_words = [kw for kw in SECTION_KEYWORDS if kw in qn]
    if dcis:
        variants.append(("canonical", " ".join(dcis + section_words)))
    if classes:
        variants.append(("classes", " ".join(classes)))
    return variants


# ---------------------------------------------------------------- boost
# Mots de sel / de forme ignorés pour décider qu'une fiche registre est « la » DCI.
SALT_WORDS = {"besilate", "besylate", "fumarate", "potassique", "sodique", "chlorhydrate",
              "exprime", "exprimee", "en", "sous", "forme", "de", "d", "dihydrate",
              "dihydratee", "trihydrate", "trihydratee", "maleate", "tartrate", "anhydre"}


def registry_match(dci_value: str, ent_dci: str) -> str | None:
    """'exact' si la fiche ne contient que la DCI (+ sel), 'partial' si association."""
    tokens, ent_tokens = set(norm(dci_value).split()), set(norm(ent_dci).split())
    if not ent_tokens or not ent_tokens <= tokens:
        return None
    return "exact" if not (tokens - ent_tokens - SALT_WORDS) else "partial"


_REGISTRY_INDEX: dict[int, list[tuple[str, frozenset]]] = {}


def registry_candidates(records, analysis) -> list[str]:
    """Fiches registre « exactes » des DCI de la question (injectées dans le pool)."""
    if not wants_registry(analysis):
        return []
    wanted = [set(norm(e.dci).split()) for e in analysis.entities if e.dci]
    if not wanted:
        return []
    key = id(records)
    if key not in _REGISTRY_INDEX:  # une seule normalisation du corpus, puis cache
        _REGISTRY_INDEX[key] = [
            (r["chunk_id"], frozenset(norm(r["metadata"].get("dci") or r["metadata"].get("inn") or "").split()))
            for r in records if r["chunk_id"].split(":", 1)[0] in REGISTRY_PREFIXES
        ]
    return [cid for cid, tokens in _REGISTRY_INDEX[key]
            if any(w <= tokens and not (tokens - w - SALT_WORDS) for w in wanted)]


def _entity_keys(analysis):
    """Clés normalisées par entité : {index: {'dci': ..., 'classes': set}}."""
    out = []
    for ent in analysis.entities:
        names = set()
        if ent.dci:
            names.add(norm(ent.dci))
        names.update(norm(c) for c in ent.classes if c not in GENERIC_CLASSES)
        if names:
            out.append({"dci": norm(ent.dci) if ent.dci else None, "names": names})
    return out


def _matches(value: str, names: set[str]) -> bool:
    v = norm(value)
    return bool(v) and any(v == n or v.startswith(n + " ") for n in names)


def metadata_boost(record: dict, analysis) -> tuple[float, list[str]]:
    """Boost d'un chunk selon ses métadonnées et les entités de la question."""
    if analysis is None or not analysis.entities:
        return 0.0, []
    meta = record.get("metadata") or {}
    entities = _entity_keys(analysis)
    prefix = record["chunk_id"].split(":", 1)[0]
    boost, why = 0.0, []

    if prefix in REGISTRY_PREFIXES:
        if not wants_registry(analysis):
            return 0.0, []
        value = meta.get("dci") or meta.get("inn") or ""
        for ent in entities:
            kind = registry_match(value, ent["dci"]) if ent["dci"] else None
            if kind:
                boost += BOOST[f"registry_{kind}"]; why.append(f"registry_{kind}")

    elif prefix == "thesaurus":
        sub, cib = meta.get("substance", ""), meta.get("cible", "")
        sides = [i for i, e in enumerate(entities) if _matches(sub, e["names"])]
        targets = [i for i, e in enumerate(entities) if _matches(cib, e["names"])]
        if any(a != b for a in sides for b in targets):
            boost += BOOST["thesaurus_pair"]; why.append("thesaurus_pair")
        elif any(e["dci"] and (_matches(sub, {e["dci"]}) or _matches(cib, {e["dci"]})) for e in entities):
            boost += BOOST["thesaurus_side"]; why.append("thesaurus_side")

    elif prefix == "anpp":
        dci = norm(meta.get("dci") or meta.get("requested_dci") or "")
        product = norm(meta.get("product") or "")
        wanted = wanted_sections(norm(analysis.raw), analysis.intent)
        same_drug = any((e["dci"] and e["dci"] in dci) for e in entities) or any(
            norm(ent.term) and norm(ent.term) in product for ent in analysis.entities)
        if same_drug and meta.get("section") in wanted:
            boost += BOOST["anpp_section"]; why.append("anpp_section")
        # Marque citée dans la question = ce produit précis (pas un autre RCP de la DCI).
        brands = [norm(e.term) for e in analysis.entities
                  if e.dci and norm(e.term) and norm(e.term) != norm(e.dci)]
        if any(b in product for b in brands):
            boost += BOOST["anpp_product"]; why.append("anpp_product")

    return boost, why


# ---------------------------------------------------------------- graphe
class GraphExpander:
    """Index du graphe L3 orienté recherche : interaction -> chunk_id du corpus."""

    def __init__(self, graph, corpus_records):
        g = graph.graph if hasattr(graph, "graph") else graph
        self.g = g
        # Correspondance libellé du graphe -> chunk du Thésaurus.
        key2chunks = defaultdict(list)
        for r in corpus_records:
            if r["source_id"] == "S_ANSM_THESAURUS":
                m = r["metadata"]
                key2chunks[norm(f"{m.get('substance', '')} {m.get('cible', '')}")].append(r["chunk_id"])
        self.chunks_of: dict[str, list[str]] = {}
        self.involved: dict[str, set[str]] = defaultdict(set)
        self.by_node: dict[str, set[str]] = defaultdict(set)
        self.classes_of: dict[str, set[str]] = defaultdict(set)
        self.members_of: dict[str, set[str]] = defaultdict(set)
        self.level: dict[str, str] = {}
        unmapped = 0
        for n, d in g.nodes(data=True):
            if d.get("type") == "interaction":
                ids = key2chunks.get(norm(d.get("label", "")), [])
                self.chunks_of[n] = ids
                self.level[n] = d.get("level", "")
                unmapped += not ids
        for s, t, d in g.edges(data=True):
            rel = d.get("relation")
            if rel == "involves":
                self.involved[s].add(t)
                self.by_node[t].add(s)
            elif rel == "member_of":
                self.classes_of[s].add(t)
                if g.nodes[s].get("type") == "dci":
                    self.members_of[t].add(s)
        self.unmapped = unmapped

    def _side(self, ent) -> set[str]:
        nodes = set()
        if ent.dci and ent.dci in self.g:
            nodes.add(ent.dci)
            nodes |= self.classes_of.get(ent.dci, set())
        nodes |= {c for c in ent.classes if c in self.g}
        return nodes - GENERIC_CLASSES

    def _specificity(self, node: str) -> float:
        size = max(1, len(self.members_of.get(node, ())))
        return 1.0 / (1.0 + math.log(size))

    def _related(self, cls: str, side: set[str]) -> str | None:
        """Classe voisine : >= 50 % de ses membres appartiennent à une classe du côté."""
        members = self.members_of.get(cls)
        if not members or cls in side:
            return None
        for parent in sorted(side):
            pm = self.members_of.get(parent)
            if pm and parent not in GENERIC_CLASSES and len(members & pm) / len(members) >= 0.5:
                return parent
        return None

    def expand(self, analysis, limit: int = 30) -> tuple[list[str], dict]:
        """Chunk_ids classés + trace. Paires d'entités d'abord, puis classes voisines."""
        trace = {"pairs": [], "absence": [], "related": [], "single": []}
        ents = [e for e in (analysis.entities if analysis else []) if self._side(e)]
        scored: dict[str, tuple] = {}

        def add(inter, scope, score):
            for cid in self.chunks_of.get(inter, []):
                key = (score, -_level_rank(self.level.get(inter, "")))
                if cid not in scored or key > scored[cid][0]:
                    scored[cid] = (key, scope)

        if len(ents) >= 2:
            for i in range(len(ents)):
                for j in range(i + 1, len(ents)):
                    a, b = self._side(ents[i]), self._side(ents[j])
                    found = 0
                    for inter in sorted(set().union(*(self.by_node[n] for n in a))):
                        inv = self.involved[inter]
                        la, lb = inv & a, inv & b
                        # Il faut deux nœuds distincts : un côté A, un côté B.
                        if not any(x != y for x in la for y in lb):
                            continue
                        spec = max(self._specificity(x) for x in la) + max(self._specificity(y) for y in lb)
                        direct = ents[i].dci in la and ents[j].dci in lb
                        add(inter, "direct" if direct else "class", 2 + spec)
                        found += 1
                    label = f"{ents[i].term} + {ents[j].term}"
                    trace["pairs"].append({"pair": label, "interactions": found})
                    if found:
                        continue
                    # Absence : aucune entrée pour la paire -> preuve par classes voisines.
                    trace["absence"].append(label)
                    for side_x, side_y in ((a, b), (b, a)):
                        for inter in sorted(set().union(*(self.by_node[n] for n in side_x))):
                            for other in sorted(self.involved[inter] - side_x):
                                parent = self._related(other, side_y)
                                if parent:
                                    add(inter, "related_class", 1 + self._specificity(other))
                                    trace["related"].append({"via": parent, "class": other})
        elif len(ents) == 1 and analysis.intent == "interaction":
            ent = ents[0]
            for node in sorted(self._side(ent)):
                for inter in sorted(self.by_node[node]):
                    add(inter, "direct" if node == ent.dci else "class", self._specificity(node))
            trace["single"].append(ent.term)

        # Tri déterministe : score, puis chunk_id (les ensembles Python changent d'ordre
        # d'un processus à l'autre).
        ranked = sorted(scored.items(), key=lambda kv: (-kv[1][0][0], -kv[1][0][1], kv[0]))[:limit]
        scopes = {cid: scope for cid, (_, scope) in ranked}
        return [cid for cid, _ in ranked], {**trace, "scopes": scopes}


@lru_cache(maxsize=1)
def load_default_graph(path: str = str(GRAPH_JSON)):
    from .graph import KnowledgeGraph
    return KnowledgeGraph.load(Path(path))


def corpus_from_disk(path=CORPUS_PATH):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]
