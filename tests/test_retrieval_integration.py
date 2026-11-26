"""Tests L4 : recherche enrichie (variantes, boost, graphe).

Ils tournent sans FAISS ni modèle d'embedding (Retriever(load_dense=False)).
Ils sont ignorés si l'index BM25 n'existe pas : lancer d'abord
`python scripts/08_build_index.py --bm25-only`.
Les tests dense/hybride sont ignorés si l'index FAISS est absent.
"""
import statistics
import time

import pytest

from pharmeazor.config import INDEX_DIR
from pharmeazor.corpus import split_long_chunks
from pharmeazor.enrich import build_variants, registry_match
from pharmeazor.query import analyze_query

HAS_BM25 = (INDEX_DIR / "bm25").exists() and (INDEX_DIR / "bm25_chunk_ids.json").exists()
HAS_FAISS = (INDEX_DIR / "faiss.index").exists() and (INDEX_DIR / "faiss_chunk_ids.json").exists()
needs_bm25 = pytest.mark.skipif(not HAS_BM25, reason="index BM25 absent (scripts/08_build_index.py)")
needs_faiss = pytest.mark.skipif(not HAS_FAISS, reason="index FAISS absent (scripts/08_build_index.py)")

QUESTIONS = [
    "Quel est le dosage disponible du paracétamol ?",
    "Peut-on associer l'ibuprofène et l'aspirine ? Quel est le niveau d'interaction ?",
    "Peut-on associer l'amlodipine avec les AINS ?",
    "Quelle est la DCI du médicament TRIATEC ?",
    "Peut-on prendre des sels de calcium avec la ciprofloxacine ?",
]


@pytest.fixture(scope="module")
def retriever():
    from pharmeazor.retrieval import Retriever
    return Retriever(load_dense=False)


def ids(results):
    return [r["chunk_id"] for r in results]


# ---------------------------------------------------------------- fonctions pures
def test_variants_raw_only_without_entities():
    a = analyze_query("Quelle est la capitale de l'Algérie ?")
    assert build_variants("Quelle est la capitale de l'Algérie ?", a) == [
        ("raw", "Quelle est la capitale de l'Algérie ?")]


def test_variants_add_canonical_and_classes():
    q = "Peut-on associer l'ibuprofène et le ramipril ?"
    names = dict(build_variants(q, analyze_query(q)))
    assert "IBUPROFENE" in names["canonical"] and "RAMIPRIL" in names["canonical"]
    assert "AINS" in names["classes"] and "IEC" in names["classes"]


def test_registry_match_exact_vs_combination():
    assert registry_match("AMLODIPINE BESILATE EXPRIME EN AMLODIPINE", "AMLODIPINE") == "exact"
    assert registry_match("AMLODIPINE VALSARTAN HYDROCHLOROTHIAZIDE", "AMLODIPINE") == "partial"
    assert registry_match("PARACETAMOL", "IBUPROFENE") is None


def test_split_long_chunks_still_works():
    long = {"chunk_id": "x:1", "text": "Phrase. " * 600, "metadata": {}}
    out = split_long_chunks([long], max_tokens=100)
    assert len(out) > 1
    assert len({c["chunk_id"] for c in out}) == len(out)
    assert all(c["metadata"]["parent_chunk"] == "x:1" for c in out)


# ---------------------------------------------------------------- mode brut
@needs_bm25
@pytest.mark.parametrize("q", QUESTIONS)
def test_raw_mode_reproduces_week2(retriever, q):
    expected = [cid for cid, _ in retriever.search_bm25(q, 10)]
    got = retriever.search(q, 10, method="bm25")
    assert ids(got) == expected
    assert all("signals" not in r for r in got)  # format semaine 2 inchangé


# ---------------------------------------------------------------- mode enrichi
@needs_bm25
def test_empty_query_does_not_crash(retriever):
    results, trace = retriever.search("   ", method="bm25", normalize=True, expand=True,
                                      return_trace=True)
    assert results == [] and trace["variants"] == []


@needs_bm25
def test_normalized_finds_ibuprofen_aspirin(retriever):
    gold = {"thesaurus:anti inflammatoires non steroidiens:56:1",
            "thesaurus:acide acetylsalicylique:5:3",
            "thesaurus:antiagregants plaquettaires:45:2"}
    q = QUESTIONS[1]
    assert not gold & set(ids(retriever.search(q, 10, method="bm25")))  # échec brut connu
    enriched = retriever.search(q, 10, method="bm25", normalize=True, expand=True)
    assert gold & set(ids(enriched))


@needs_bm25
def test_graph_absence_uses_related_classes_and_says_so(retriever):
    results, trace = retriever.search(QUESTIONS[2], 10, method="bm25", expand=True,
                                      return_trace=True)
    assert trace["graph"]["absence"], "amlodipine + AINS n'a pas d'entrée directe"
    graph_signals = [s for r in results for s in r["signals"] if s.startswith("graph:")]
    assert graph_signals and all("related_class" in s for s in graph_signals)
    assert "thesaurus:anti inflammatoires non steroidiens:56:13" in ids(results)  # AINS + IEC


@needs_bm25
def test_every_enriched_result_explains_itself(retriever):
    for q in QUESTIONS:
        for r in retriever.search(q, 10, method="bm25", normalize=True, expand=True):
            assert r["signals"], r["chunk_id"]


@needs_bm25
def test_latency_bm25_enriched_under_50ms(retriever):
    retriever.search(QUESTIONS[2], method="bm25", normalize=True, expand=True)  # chauffe
    times = []
    for q in QUESTIONS * 3:
        t = time.perf_counter()
        retriever.search(q, 10, method="bm25", normalize=True, expand=True)
        times.append((time.perf_counter() - t) * 1000)
    assert statistics.median(times) < 50


# ---------------------------------------------------------------- dense / hybride
@needs_faiss
def test_hybrid_enriched_runs_and_keeps_raw_mode():
    from pharmeazor.retrieval import Retriever
    r = Retriever()
    q = QUESTIONS[2]
    raw = r.search(q, 10, method="hybrid")
    assert ids(raw) == [cid for cid, _ in r.search_hybrid(q, 10)]
    enriched = r.search(q, 10, method="hybrid", normalize=True, expand=True)
    assert len(enriched) == 10
