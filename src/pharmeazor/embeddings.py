from functools import lru_cache

import numpy as np

from .config import EMBEDDING_MODEL


def _is_e5(model_name):
    return "e5" in model_name.lower()


@lru_cache(maxsize=1)
def get_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBEDDING_MODEL)


def embed_passages(texts, batch_size=64):
    model = get_model()
    texts = list(texts)
    if _is_e5(EMBEDDING_MODEL):
        texts = ["passage: " + t for t in texts]
    vectors = model.encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=True,
        convert_to_numpy=True,
    )
    return np.asarray(vectors, dtype="float32")


def embed_query(text):
    model = get_model()
    if _is_e5(EMBEDDING_MODEL):
        text = "query: " + text
    vector = model.encode(
        [text],
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return np.asarray(vector, dtype="float32")[0]
