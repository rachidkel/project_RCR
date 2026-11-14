import json

from .config import INDEX_DIR
from .corpus import load_corpus
from .embeddings import embed_passages
from .textnorm import norm


FAISS_FILE = INDEX_DIR / "faiss.index"
IDS_FILE = INDEX_DIR / "chunk_ids.json"
BM25_DIR = INDEX_DIR / "bm25"


def build_faiss(corpus, index_dir=INDEX_DIR):
    import faiss

    index_dir.mkdir(parents=True, exist_ok=True)
    texts = [record["text"] for record in corpus]
    vectors = embed_passages(texts)

    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    faiss.write_index(index, str(index_dir / FAISS_FILE.name))

    with open(index_dir / IDS_FILE.name, "w", encoding="utf-8") as f:
        json.dump([record["chunk_id"] for record in corpus], f, ensure_ascii=False)

    return vectors.shape


def build_bm25(corpus, index_dir=INDEX_DIR):
    import bm25s

    index_dir.mkdir(parents=True, exist_ok=True)
    texts = [norm(record["text"]) for record in corpus]
    tokens = bm25s.tokenize(texts, stopwords="french", show_progress=False)

    retriever = bm25s.BM25()
    retriever.index(tokens)
    retriever.save(str(index_dir / BM25_DIR.name), show_progress=False)

    return retriever


def load_faiss(index_dir=INDEX_DIR):
    import faiss

    index = faiss.read_index(str(index_dir / FAISS_FILE.name))
    with open(index_dir / IDS_FILE.name, encoding="utf-8") as f:
        chunk_ids = json.load(f)
    return index, chunk_ids


def load_bm25(index_dir=INDEX_DIR):
    import bm25s

    return bm25s.BM25.load(str(index_dir / BM25_DIR.name), load_corpus=False)
