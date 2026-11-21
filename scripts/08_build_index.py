import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, "src")
from pharmeazor.config import CORPUS_PATH, EMBEDDING_MODEL, INDEX_DIR
from pharmeazor.corpus import load_corpus
from pharmeazor.index import build_bm25, build_faiss


BM25_ONLY = "--bm25-only" in sys.argv

corpus = load_corpus()
print(f"Corpus    : {len(corpus)} chunks ({CORPUS_PATH})")
print(f"Modèle    : {EMBEDDING_MODEL}")
print(f"Index dir : {INDEX_DIR}\n")

if not BM25_ONLY:
    start = time.time()
    shape = build_faiss(corpus)
    print(f"[ok] FAISS  : {shape[0]} vecteurs de dimension {shape[1]} en {time.time() - start:.1f}s")
else:
    print("[skip] FAISS ignoré (--bm25-only)")

start = time.time()
build_bm25(corpus)
print(f"[ok] BM25   : index construit en {time.time() - start:.1f}s")

print(f"\nIndex sauvegardés dans : {INDEX_DIR}")
