import re
from pathlib import Path

import bm25s

from .config import CORPUS_PATH, INDEX_DIR, PROCESSED
from .corpus import load_corpus
from .embeddings import embed_queries, embed_query
from .index import load_bm25, load_bm25_ids, load_faiss
from .textnorm import norm
from .thesaurus import load_lookup


# Refus systématique : demande de conseil médical personnalisé, d'ordonnance
# ou de diagnostic. Un médicament du périmètre peut apparaître dans la phrase
# (« mon père prend du ramipril... ») : la présence d'une DCI ne suffit donc
# pas à déclarer la question dans le périmètre.
MEDICAL_ADVICE_PATTERNS = [
    r"\b(mon|ma|mes|notre|son|sa|ses)\s+"
    r"(fils|fille|enfant|bebe|nourrisson|pere|mere|voisin|voisine|frere|soeur|"
    r"epoux|epouse|patient|patiente|ami|amie)\b",
    r"\b(ordonnance|prescription|prescrire|rediger une ordonnance)\b",
    r"\b(dois[- ]je|doit[- ]il|doit[- ]elle|que doit|que faire|que dois)\b",
    r"\b(diagnostic|est[- ]ce (une|un)|est[- ]ce grave|est[- ]ce dangereux)\b",
    r"\b(dose|posologie|combien)\b.{0,40}\b(enfant|fils|fille|bebe|nourrisson)\b",
    r"\b(j ai|j'ai)\b.{0,30}\b(fievre|mal|douleur|vertige)\b",
]


class Retriever:
    def __init__(self, corpus_path=CORPUS_PATH, index_dir=INDEX_DIR, load_dense=True):
        self.records = load_corpus(corpus_path)
        self.by_id = {record["chunk_id"]: record for record in self.records}
        # load_dense=False : BM25 seul, sans FAISS ni modèle (tests, machines lentes).
        self.faiss_index, self.faiss_ids = (
            load_faiss(index_dir) if load_dense else (None, [])
        )
        self._expander = None
        self._expander_graph = None
        self.bm25 = load_bm25(index_dir)
        self.bm25_ids = load_bm25_ids(index_dir)
        self.thesaurus = load_lookup()

    def search_dense(self, query, k=10, vector=None):
        if self.faiss_index is None:
            raise RuntimeError("Index dense non chargé (Retriever(load_dense=False)).")
        if vector is None:
            vector = embed_query(query)
        scores, indices = self.faiss_index.search(vector.reshape(1, -1), k)
        hits = []
        for score, idx in zip(scores[0], indices[0]):
            if 0 <= idx < len(self.faiss_ids):
                hits.append((self.faiss_ids[idx], float(score)))
        return hits

    def search_bm25(self, query, k=10):
        tokens = bm25s.tokenize([norm(query)], stopwords="french", show_progress=False)
        results, scores = self.bm25.retrieve(tokens, k=k, show_progress=False)
        hits = []
        for score, idx in zip(scores[0], results[0]):
            if 0 <= idx < len(self.bm25_ids):
                hits.append((self.bm25_ids[int(idx)], float(score)))
        return hits

    def search_exact(self, query, k=10):
        """Lookup exact dans le Thésaurus (substance/classe ↔ substance/classe)."""
        hits = []
        for rank, interaction in enumerate(self.thesaurus.lookup(query)[:k]):
            hits.append((interaction.chunk_id, 1.0 - rank * 1e-6))
        return hits

    def search_hybrid(self, query, k=10, pool=50, rrf_k=60):
        fused = {}
        for ranked in (self.search_dense(query, pool), self.search_bm25(query, pool)):
            for rank, (chunk_id, _) in enumerate(ranked):
                fused[chunk_id] = fused.get(chunk_id, 0.0) + 1.0 / (rrf_k + rank + 1)
        return sorted(fused.items(), key=lambda item: -item[1])[:k]

    def search(self, query, k=10, method="hybrid", normalize=False, expand=False,
               graph=None, return_trace=False):
        """Recherche brute (semaine 2) ou enrichie (semaine 3, L4).

        normalize : variantes de requête (brute + DCI + classes) fusionnées par RRF,
                    plus un boost par métadonnées (entités de la question).
        expand    : injecte les interactions du graphe L3 reliant les entités.
        graph     : KnowledgeGraph (ou chemin JSON) ; chargé par défaut si expand.
        Sans normalize ni expand, le comportement est strictement celui de la
        semaine 2 (mêmes classements, mêmes scores).
        """
        if normalize or expand:
            results, trace = self._search_enriched(query, k, method, normalize, expand, graph)
            return (results, trace) if return_trace else results
        results = self._search_raw(query, k, method)
        return (results, {"mode": "raw"}) if return_trace else results

    def _search_raw(self, query, k, method):
        if method == "dense":
            ranked = self.search_dense(query, k)
        elif method == "bm25":
            ranked = self.search_bm25(query, k)
        elif method == "exact":
            ranked = self.search_exact(query, k)
        elif method == "hybrid":
            ranked = self.search_hybrid(query, k)
        else:
            raise ValueError(f"Méthode inconnue : {method}")

        results = []
        for chunk_id, score in ranked[:k]:
            record = self.by_id.get(chunk_id)
            if record is None:
                continue
            results.append({
                "chunk_id": chunk_id,
                "score": score,
                "source_id": record["source_id"],
                "text": record["text"],
                "metadata": record["metadata"],
            })
        return results

    def is_out_of_scope(self, query, threshold_bm25=1.5, threshold_dense=0.55):
        query_norm = norm(query)

        for pattern in MEDICAL_ADVICE_PATTERNS:
            if re.search(pattern, query_norm):
                return True, "Demande de conseil médical personnalisé, d'ordonnance ou de diagnostic."

        drugs_path = PROCESSED / "drugs_verified.csv"
        found = False
        if drugs_path.exists():
            import pandas as pd

            df = pd.read_csv(drugs_path, encoding="utf-8-sig")
            for _, row in df.iterrows():
                dci = norm(str(row.get("DCI", "")))
                if dci and re.search(rf"\b{re.escape(dci)}\b", query_norm):
                    found = True
                    break
            # Une classe ou un nom commercial du Thésaurus compte aussi comme
            # médicament du périmètre (ex. « aspirine »).
            if not found and self.thesaurus.find_mentions(query):
                found = True
            if not found:
                return True, "Aucun médicament de la liste détecté."

        bm25_hits = self.search_bm25(query, k=1)
        bm25_score = bm25_hits[0][1] if bm25_hits else 0
        dense_score = 0.0
        if self.faiss_index is not None:
            dense_hits = self.search_dense(query, k=1)
            dense_score = dense_hits[0][1] if dense_hits else 0

        if bm25_score < threshold_bm25 and dense_score < threshold_dense:
            return True, f"Scores trop faibles (BM25={bm25_score:.2f}, dense={dense_score:.2f})."

        return False, "Requête dans le périmètre."

    # ------------------------------------------------------------ L4 : enrichi
    def _ranked(self, text, method, pool, vector=None):
        if method == "bm25":
            return self.search_bm25(text, pool)
        if method == "dense":
            return self.search_dense(text, pool, vector=vector)
        if method == "exact":
            return self.search_exact(text, pool)
        if method == "hybrid":
            fused = {}
            for ranked in (self.search_dense(text, pool, vector=vector), self.search_bm25(text, pool)):
                for rank, (cid, _) in enumerate(ranked):
                    fused[cid] = fused.get(cid, 0.0) + 1.0 / (60 + rank + 1)
            return sorted(fused.items(), key=lambda item: -item[1])
        raise ValueError(f"Méthode inconnue : {method}")

    def _search_enriched(self, query, k, method, normalize, expand, graph, pool=50, rrf_k=60):
        from .enrich import BOOST, VARIANT_WEIGHT, build_variants, metadata_boost, registry_candidates
        from .query import analyze_query

        analysis = analyze_query(query or "")
        trace = {
            "mode": "+".join(m for m, on in (("normalize", normalize), ("expand", expand)) if on),
            "intent": analysis.intent,
            "out_of_scope": analysis.out_of_scope,
            "entities": [(e.term, e.dci, list(e.classes)) for e in analysis.entities],
        }
        if not (query or "").strip():
            trace["variants"] = []
            return [], trace

        variants = build_variants(query, analysis) if normalize else [("raw", query)]
        trace["variants"] = variants

        vectors = [None] * len(variants)
        if method in ("dense", "hybrid"):
            vectors = list(embed_queries([text for _, text in variants]))

        fused, signals = {}, {}
        for (name, text), vec in zip(variants, vectors):
            weight = VARIANT_WEIGHT.get(name, 1.0)
            for rank, (cid, _) in enumerate(self._ranked(text, method, pool, vec)):
                fused[cid] = fused.get(cid, 0.0) + weight / (rrf_k + rank + 1)
                signals.setdefault(cid, []).append(f"{name}@{rank + 1}")

        if normalize:
            # Les fiches de la DCI entrent dans le pool même si la formulation
            # de la question ne les a pas fait remonter (ex. « marques de... »).
            for rank, cid in enumerate(registry_candidates(self.records, analysis)):
                fused[cid] = fused.get(cid, 0.0) + 0.5 / (rrf_k + rank + 1)
                signals.setdefault(cid, []).append(f"entity@{rank + 1}")

        # [L4-GRAPH] expansion par le graphe : ajoutée à l'étape suivante

        if normalize:
            for cid in list(fused):
                bonus, why = metadata_boost(self.by_id[cid], analysis) if cid in self.by_id else (0.0, [])
                if bonus:
                    fused[cid] += bonus
                    signals[cid].extend(f"boost:{w}" for w in why)

        ranked = sorted(fused.items(), key=lambda item: (-item[1], item[0]))[:k]
        results = []
        for cid, score in ranked:
            record = self.by_id.get(cid)
            if record is None:
                continue
            results.append({
                "chunk_id": cid,
                "score": score,
                "source_id": record["source_id"],
                "text": record["text"],
                "metadata": record["metadata"],
                "signals": signals.get(cid, []),
            })
        return results, trace
