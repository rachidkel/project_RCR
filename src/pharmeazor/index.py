import json

from .config import INDEX_DIR
from .embeddings import embed_passages
from .textnorm import norm


FAISS_FILE = INDEX_DIR / "faiss.index"
FAISS_IDS_FILE = INDEX_DIR / "faiss_chunk_ids.json"
BM25_DIR = INDEX_DIR / "bm25"
BM25_IDS_FILE = INDEX_DIR / "bm25_chunk_ids.json"

# Le Thésaurus est une base structurée : on le sert par lookup exact
# (`src/pharmeazor/thesaurus.py`), pas par similarité vectorielle. Il reste
# dans BM25 pour permettre la comparaison demandée (exact vs lexical).
DENSE_EXCLUDED_SOURCES = {"S_ANSM_THESAURUS"}


def _ids_path(index_dir, filename):
    return index_dir / filename


def build_faiss(corpus, index_dir=INDEX_DIR):
    import faiss

    index_dir.mkdir(parents=True, exist_ok=True)
    dense_corpus = [
        record for record in corpus if record["source_id"] not in DENSE_EXCLUDED_SOURCES
    ]
    texts = [record["text"] for record in dense_corpus]
    vectors = embed_passages(texts)

    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    faiss.write_index(index, str(index_dir / FAISS_FILE.name))

    with open(_ids_path(index_dir, FAISS_IDS_FILE.name), "w", encoding="utf-8") as f:
        json.dump([record["chunk_id"] for record in dense_corpus], f, ensure_ascii=False)

    return vectors.shape


def build_bm25(corpus, index_dir=INDEX_DIR):
    import bm25s

    index_dir.mkdir(parents=True, exist_ok=True)
    texts = [norm(record["text"]) for record in corpus]
    tokens = bm25s.tokenize(texts, stopwords="french", show_progress=False)

    retriever = bm25s.BM25()
    retriever.index(tokens)
    retriever.save(str(index_dir / BM25_DIR.name), show_progress=False)

    with open(_ids_path(index_dir, BM25_IDS_FILE.name), "w", encoding="utf-8") as f:
        json.dump([record["chunk_id"] for record in corpus], f, ensure_ascii=False)

    return retriever


def load_faiss(index_dir=INDEX_DIR):
    import faiss

    index = faiss.read_index(str(index_dir / FAISS_FILE.name))
    with open(_ids_path(index_dir, FAISS_IDS_FILE.name), encoding="utf-8") as f:
        chunk_ids = json.load(f)
    return index, chunk_ids


def load_bm25(index_dir=INDEX_DIR):
    import bm25s

    return bm25s.BM25.load(str(index_dir / BM25_DIR.name), load_corpus=False)


def load_bm25_ids(index_dir=INDEX_DIR):
    with open(_ids_path(index_dir, BM25_IDS_FILE.name), encoding="utf-8") as f:
        return json.load(f)
