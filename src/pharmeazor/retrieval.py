import bm25s

from .config import CORPUS_PATH, INDEX_DIR
from .corpus import load_corpus
from .embeddings import embed_query
from .index import load_bm25, load_faiss
from .textnorm import norm


class Retriever:
    def __init__(self, corpus_path=CORPUS_PATH, index_dir=INDEX_DIR):
        self.records = load_corpus(corpus_path)
        self.by_id = {record["chunk_id"]: record for record in self.records}
        self.faiss_index, self.chunk_ids = load_faiss(index_dir)
        self.bm25 = load_bm25(index_dir)

    def search_dense(self, query, k=10):
        vector = embed_query(query).reshape(1, -1)
        scores, indices = self.faiss_index.search(vector, k)
        hits = []
        for score, idx in zip(scores[0], indices[0]):
            if 0 <= idx < len(self.chunk_ids):
                hits.append((self.chunk_ids[idx], float(score)))
        return hits

    def search_bm25(self, query, k=10):
        tokens = bm25s.tokenize([norm(query)], stopwords="french", show_progress=False)
        results, scores = self.bm25.retrieve(tokens, k=k, show_progress=False)
        hits = []
        for score, idx in zip(scores[0], results[0]):
            if 0 <= idx < len(self.chunk_ids):
                hits.append((self.chunk_ids[int(idx)], float(score)))
        return hits

    def search_hybrid(self, query, k=10, pool=50, rrf_k=60):
        fused = {}
        for ranked in (self.search_dense(query, pool), self.search_bm25(query, pool)):
            for rank, (chunk_id, _) in enumerate(ranked):
                fused[chunk_id] = fused.get(chunk_id, 0.0) + 1.0 / (rrf_k + rank + 1)
        return sorted(fused.items(), key=lambda item: -item[1])[:k]

    def search(self, query, k=10, method="hybrid"):
        if method == "dense":
            ranked = self.search_dense(query, k)
        elif method == "bm25":
            ranked = self.search_bm25(query, k)
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
    
        import pandas as pd
        from .config import PROCESSED
        
        
        drugs_path = PROCESSED / "drugs_verified.csv"
        if drugs_path.exists():
            df = pd.read_csv(drugs_path, encoding="utf-8-sig")
            query_norm = norm(query)
            found = False
            for _, row in df.iterrows():
                dci = norm(str(row.get("DCI", "")))
                if dci and dci in query_norm:
                    found = True
                    break
            if not found:
                return True, "Aucun médicament de la liste détecté."
        
        
        bm25_hits = self.search_bm25(query, k=1)
        dense_hits = self.search_dense(query, k=1)
        bm25_score = bm25_hits[0][1] if bm25_hits else 0
        dense_score = dense_hits[0][1] if dense_hits else 0
        
        if bm25_score < threshold_bm25 and dense_score < threshold_dense:
            return True, f"Scores trop faibles (BM25={bm25_score:.2f}, dense={dense_score:.2f})."
        
        return False, "Requête dans le périmètre."