"""Normalisation des noms de médicaments (nom commercial, DCI, faute de frappe).

Le dictionnaire n'est **jamais** codé en dur : il est reconstruit depuis les
données du dépôt (`nomenclature_active.csv` + `produits_enregistres.csv`), ce
qui évite l'évaluation circulaire où les entrées de test sortent du même
dictionnaire que celui utilisé pour répondre.

Trois responsabilités :

1. `canonical_key()` : ramène une DCI à une forme comparable. Les sels et les
   mentions « exprimé en » désignent la même molécule (« PERINDOPRIL ERBUMINE »
   et « PERINDOPRIL TER-BUTYLAMINE ») et doivent être fusionnés, pas signalés
   comme ambigus. Les associations (« A/B ») sont triées pour que l'ordre
   d'écriture ne crée pas deux entrées.
2. `build_dictionary()` : marque normalisée -> ensemble de DCI canoniques.
   Un ensemble de cardinal > 1 signale une **vraie** ambiguïté (une marque
   vendue sous deux molécules différentes).
3. `normalize_drug()` : résout une saisie libre et renvoie le candidat retenu
   avec sa méthode, son score et, le cas échéant, les alternatives proches.
   Une ambiguïté est signalée, jamais tranchée en silence.
"""

from __future__ import annotations

import csv
import re
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache

from rapidfuzz import fuzz, process

from .config import PROCESSED
from .textnorm import norm

MIPH_CSV = PROCESSED / "nomenclature" / "nomenclature_active.csv"
PHARMNET_CSV = PROCESSED / "pharmnet" / "produits_enregistres.csv"

# Sels, esters, hydrates et qualités galéniques : même molécule, donc fusionnés.
SALT_TOKENS = frozenset(
    """chlorhydrate dichlorhydrate hydrochloride bromhydrate besilate besylate
    mesilate arginine erbumine butylamine maleate tartrate fumarate succinate
    citrate phosphate sulfate nitrate bromure calcique calcium sodique sodium
    potassique potassium magnesien anhydre base ter micronisee micronise
    micronized micronisee micronises""".split()
)

# Mots de liaison propres aux noms chimiques (« VALPROATE DE SODIUM »).
CONNECTOR_TOKENS = frozenset("de du des d sous forme pour a".split())

# Mots de forme galénique / dosage / termes usagers : bruit dans une saisie, jamais une DCI.
FORM_TOKENS = frozenset(
    """comprime comprimes cp cachet cachets gelule gelules gellule sirop sachet sachets
    ampoule ampoules solution buvable injectable injectables creme pommade
    collyre suspension suppositoire suppositoires boite bte flacon tube gel
    lp secable pellicule pellicule secable effervescent effervescente lyoc
    mg ml g ui pour cent de du des la le les un une et sous forme voie orale
    iv im enfant adulte nourrisson bebe bebes
    mg ml gr gramme grammes dose dosettes""".split()
)

# Noms usuels qui ne sont ni la DCI ni une marque du catalogue.
# Volontairement court et explicite : chaque entrée est une décision assumée.
ALIASES = {
    "aspirine": "ACIDE ACETYLSALICYLIQUE",
    "aspegic": "ACIDE ACETYLSALICYLIQUE",
    "vitamine c": "ACIDE ASCORBIQUE",
    "paracet": "PARACETAMOL",
    "paracétamol codéine": "PARACETAMOL + CODEINE",
}

_EXPRIME_RE = re.compile(r"exprimes?\s+en|exprim[eé]e?s?\s+en", re.IGNORECASE)
_PARENS_RE = re.compile(r"\([^)]*\)")
_SEP_RE = re.compile(r"[/+]")
_HYDRATE_RE = re.compile(r"^(tri|mono|di|hemi|sesqui)?hydrat")

# Synonymes de DCI : le même produit sous deux écritures officielles.
# Le cotrimoxazole est l'association sulfaméthoxazole + triméthoprime.
KEY_SYNONYMS = {
    "SULFAMETHOXAZOLE + TRIMETHOPRIME": "COTRIMOXAZOLE",
}


def _ascii_upper(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text))
    return text.encode("ascii", "ignore").decode().upper()


def _component(text: str) -> str:
    """Une substance seule : sans sel, sans hydratation, sans mots de liaison."""
    chunk = _PARENS_RE.sub(" ", text)
    parts = _EXPRIME_RE.split(chunk)
    if len(parts) > 1:  # « ... EXPRIME EN <substance de référence> »
        chunk = parts[-1]
    tokens = []
    for token in norm(chunk).split():
        if token in SALT_TOKENS or token in CONNECTOR_TOKENS:
            continue
        if _HYDRATE_RE.match(token):  # trihydratee, monohydrate...
            continue
        tokens.append(token)
    return " ".join(dict.fromkeys(tokens)).upper()  # « GLUCOSE GLUCOSE » -> « GLUCOSE »


def _split_components(text: str) -> list[str]:
    """Découpe une association, mais jamais à l'intérieur d'une parenthèse.

    « cotrimoxazole (sulfaméthoxazole + triméthoprime) » est une seule
    substance : on retire d'abord le contenu parenthésé, puis on découpe sur
    « / » et « + ».
    """
    cleaned = _PARENS_RE.sub(" ", text)
    return [part for part in _SEP_RE.split(cleaned) if part.strip()]


def canonical_key(name: str) -> str:
    """Clé comparable et stable pour une DCI (ou une association)."""
    text = _ascii_upper(name).replace("*", " ")
    components = [_component(c) for c in _split_components(text)]
    components = [c for c in components if c]
    if not components:
        return ""
    # Tri des composants : « A/B » et « B/A » sont la même association.
    return KEY_SYNONYMS.get(" + ".join(sorted(components)), " + ".join(sorted(components)))


def canonical_label(name: str) -> str:
    """Forme lisible : ordre d'écriture d'origine, sels retirés."""
    text = _ascii_upper(name).replace("*", " ")
    components = [_component(c) for c in _split_components(text)]
    components = [c for c in components if c]
    return " + ".join(components)


@dataclass(frozen=True)
class Match:
    """Résultat d'une normalisation."""

    key: str | None = None
    label: str | None = None
    method: str = "aucune"  # alias | marque | dci | contient | flou | aucune
    score: float = 0.0
    ambiguous: bool = False
    alternatives: tuple[str, ...] = ()

    @property
    def found(self) -> bool:
        return self.key is not None


@dataclass
class Dictionary:
    """Index marque -> DCI et DCI -> DCI, construit depuis les CSV du dépôt."""

    brand_to_keys: dict[str, set[str]] = field(default_factory=dict)
    brand_loose: dict[str, set[str]] = field(default_factory=dict)
    brand_collapsed: dict[str, set[str]] = field(default_factory=dict)
    phrase_to_keys: dict[str, set[str]] = field(default_factory=dict)
    labels: dict[str, str] = field(default_factory=dict)
    stats: dict[str, int] = field(default_factory=dict)

    def _as_match(self, keys: set[str], method: str, score: float) -> Match:
        ordered = sorted(keys)
        label = ordered[0]
        return Match(
            key=label,
            label=self.labels.get(label, label),
            method=method,
            score=score,
            ambiguous=len(ordered) > 1,
            alternatives=tuple(self.labels.get(k, k) for k in ordered[1:]),
        )

    def contained(self, query: str) -> set[str]:
        """Clés présentes mot pour mot dans la saisie ; la plus longue gagne.

        Les associations sont traitées à part : « AMOXICILLINE + ACIDE
        CLAVULANIQUE » doit l'emporter sur « AMOXICILLINE » seul, même si
        l'ordre des composants diffère de celui de la saisie.
        """
        padding = f" {query} "
        best_len, hits = 0, set()

        def _claim(length: int, keys) -> None:
            nonlocal best_len, hits
            if length > best_len:
                best_len, hits = length, set(keys)
            elif length == best_len:
                hits |= set(keys)

        for phrase, keys in self.phrase_to_keys.items():
            if len(phrase) >= 4 and f" {phrase} " in padding:
                _claim(len(phrase), keys)

        for key in self.labels:
            if " + " not in key:
                continue
            components = [norm(c) for c in key.split(" + ")]
            if components and all(f" {c} " in padding for c in components if len(c) >= 4):
                _claim(sum(len(c) for c in components), {key})

        return hits


def _read_rows(path, brand_col: str, dci_col: str):
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            yield row.get(brand_col), row.get(dci_col)


@lru_cache(maxsize=1)
def build_dictionary(
    miph_path: str | None = None, pharmnet_path: str | None = None
) -> Dictionary:
    """Construit l'index. Mise en cache : un seul passage disque par processus."""
    miph = miph_path or str(MIPH_CSV)
    pharmnet = pharmnet_path or str(PHARMNET_CSV)

    dictionary = Dictionary()
    sources = {
        "MIPH (nomenclature nationale)": (miph, "NOM DE MARQUE", "DENOMINATION COMMUNE INTERNATIONALE"),
        "Pharm'Net (catalogue)": (pharmnet, "nom_commercial", "dci"),
    }

    rows_used = 0
    for _name, (path, brand_col, dci_col) in sources.items():
        for brand, dci in _read_rows(path, brand_col, dci_col):
            brand_key = norm(brand)
            dci_key = canonical_key(dci or "")
            if not brand_key or not dci_key:
                continue
            rows_used += 1
            dictionary.brand_to_keys.setdefault(brand_key, set()).add(dci_key)
            dictionary.phrase_to_keys.setdefault(brand_key, set()).add(dci_key)
            dictionary.phrase_to_keys.setdefault(norm(dci_key), set()).add(dci_key)
            dictionary.labels.setdefault(dci_key, canonical_label(dci))
            loose = loose_key(brand_key)
            if loose:
                dictionary.brand_loose.setdefault(loose, set()).add(dci_key)
            dictionary.brand_collapsed.setdefault(collapse(brand_key), set()).add(dci_key)

    dictionary.stats = {
        "lignes_utilisees": rows_used,
        "marques": len(dictionary.brand_to_keys),
        "dci": len(dictionary.labels),
        "marques_ambigues": sum(1 for v in dictionary.brand_to_keys.values() if len(v) > 1),
    }
    return dictionary


def clean_query(saisie: str) -> str:
    """Retire dosage, forme galénique et symboles d'une saisie libre."""
    tokens = [
        t
        for t in norm(saisie).split()
        if t not in FORM_TOKENS and not any(ch.isdigit() for ch in t)
    ]
    return " ".join(tokens)


def loose_key(brand: str) -> str:
    """Marque sans les nombres : « CLARIDAR 500 » et « CLARIDAR 250 » -> « claridar »."""
    return " ".join(t for t in brand.split() if not any(ch.isdigit() for ch in t))


def collapse(text: str) -> str:
    """Réduit les lettres doublées : « cozaar » et « cozzar » -> « cozar »."""
    return re.sub(r"(.)\1+", r"\1", text)


@lru_cache(maxsize=1)
def scope_keys(path: str | None = None) -> frozenset[str]:
    """Les 40 médicaments du périmètre, en clés canoniques (CDC : 30 à 50)."""
    source = path or str(PROCESSED / "drugs_verified.csv")
    keys = set()
    with open(source, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            key = canonical_key(row.get("DCI") or "")
            if key:
                keys.add(key)
    return frozenset(keys)


def normalize_drug(
    saisie: str,
    dictionary: Dictionary | None = None,
    threshold: float = 85.0,
    margin: float = 3.0,
) -> Match:
    """Relie une saisie libre à une DCI, en signalant les ambiguïtés.

    threshold : score fuzzy minimal pour accepter un candidat.
    margin    : deux DCI à moins de `margin` points de la meilleure sont
                considérées comme une ambiguïté à signaler. La marge est
                élargie sur les saisies très courtes (« amox », « clari »),
                où le risque de confondre deux familles est maximal.
    """
    dictionary = dictionary or build_dictionary()
    query = clean_query(saisie)
    if not query:
        return Match()
    if len(query) <= 6:
        margin = max(margin, 8.0)

    if query in ALIASES:
        key = ALIASES[query]
        return Match(key=key, label=dictionary.labels.get(key, key), method="alias", score=100.0)

    if query in dictionary.brand_to_keys:
        return dictionary._as_match(dictionary.brand_to_keys[query], "marque", 100.0)

    if query in dictionary.brand_loose:
        return dictionary._as_match(dictionary.brand_loose[query], "marque", 98.0)

    collapsed = collapse(query)
    if collapsed in dictionary.brand_collapsed:
        return dictionary._as_match(dictionary.brand_collapsed[collapsed], "marque", 97.0)

    if query in dictionary.phrase_to_keys:
        return dictionary._as_match(dictionary.phrase_to_keys[query], "dci", 100.0)

    hits = dictionary.contained(query)
    if hits:
        return dictionary._as_match(hits, "contient", 95.0)

    choices = list(dictionary.phrase_to_keys)
    results = process.extract(
        query, choices, scorer=fuzz.WRatio, limit=12, score_cutoff=threshold - 8
    )
    if not results:
        return Match()

    scores: dict[str, float] = {}
    support: dict[str, int] = {}
    for choice, score, _index in results:
        score = float(score)
        # Une marque qui *commence* par la saisie est un bien meilleur candidat
        # qu'une marque seulement proche (« amox » -> AMOXYPEN, pas TAMOXIFENE).
        if choice.startswith(query) or any(t.startswith(query) for t in choice.split()):
            score = max(score, 96.0)
        for key in dictionary.phrase_to_keys[choice]:
            if score > scores.get(key, 0.0):
                scores[key] = score
                support[key] = 1
            elif score == scores.get(key):
                support[key] = support.get(key, 1) + 1
    # À score égal, la DCI soutenue par le plus de marques l'emporte
    # (« clari » : cinq marques clarithromycine contre un clariscan).
    best_key = max(scores, key=lambda key: (scores[key], support.get(key, 0)))
    best_score = scores[best_key]
    if best_score < threshold:
        return Match()

    close = [k for k, s in scores.items() if k != best_key and s >= best_score - margin]
    return Match(
        key=best_key,
        label=dictionary.labels.get(best_key, best_key),
        method="flou",
        score=best_score,
        ambiguous=bool(close),
        alternatives=tuple(dictionary.labels.get(k, k) for k in sorted(close)),
    )
