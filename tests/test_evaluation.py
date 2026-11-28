"""Tests L5 : métriques d'évaluation et modes raw/normalized/graph.

Les tests de métriques sont purs (aucun index, aucun modèle). Les tests de
``run_evaluation`` utilisent un faux retriever pour rester rapides et
déterministes ; l'intégration réelle est couverte par ``14_eval_week3.py``.
"""
import json

import pytest

from pharmeazor.config import CORPUS_PATH
from pharmeazor.evaluation import (
    QUERIES,
    _hit_at,
    _labels,
    _mrr,
    _ndcg_at,
    _recall_at,
    analysis_metrics,
    entity_prf,
    run_evaluation,
    run_week3_evaluation,
)
from pharmeazor.query import analyze_query


class FakeRetriever:
    """Retriever minimal : renvoie tous les chunks gold dans l'ordre."""

    def __init__(self):
        gold_ids = sorted({g for query in QUERIES for g in query["gold"]})
        if not gold_ids:
            gold_ids = ["dummy:1"]
        self.records = [
            {"chunk_id": cid, "source_id": cid.split(":", 1)[0]} for cid in gold_ids
        ]
        self.by_id = {record["chunk_id"]: record for record in self.records}

    def _ids(self, k):
        return [record["chunk_id"] for record in self.records[:k]]

    def search_bm25(self, query, k=10):
        return [(cid, 1.0) for cid in self._ids(k)]

    def search_dense(self, query, k=10, vector=None):
        return [(cid, 1.0) for cid in self._ids(k)]

    def search_hybrid(self, query, k=10, pool=50, rrf_k=60):
        return [(cid, 1.0) for cid in self._ids(k)]

    def search(self, query, k=10, method="hybrid", normalize=False, expand=False,
               graph=None, return_trace=False):
        results = [
            {
                "chunk_id": cid,
                "score": 1.0,
                "source_id": self.by_id[cid]["source_id"],
                "text": "",
                "metadata": {},
            }
            for cid in self._ids(k)
        ]
        return (results, {"mode": "fake"}) if return_trace else results


# ------------------------------------------------------------------ métriques
def test_recall_at():
    assert _recall_at(["a", "b", "c"], ["b", "d"], 10) == 0.5
    assert _recall_at(["a", "b"], [], 10) is None
    assert _recall_at(["a"], ["a"], 1) == 1.0


def test_hit_at():
    assert _hit_at(["a", "b"], ["b"], 10) == 1.0
    assert _hit_at(["a", "b"], ["b"], 1) == 0.0


def test_mrr():
    assert _mrr(["x", "a", "b"], ["a", "b"]) == 0.5
    assert _mrr(["a"], ["b"]) == 0.0


def test_ndcg_at_perfect_and_partial():
    assert _ndcg_at(["a", "b"], ["a", "b"], 2) == 1.0
    assert _ndcg_at(["x", "a"], ["a"], 2) < 1.0
    assert _ndcg_at(["a"], [], 2) is None


def test_labels_split_combination():
    assert _labels(["AMOXICILLINE + ACIDE CLAVULANIQUE"]) == {
        "amoxicilline",
        "acide clavulanique",
    }


def test_entity_prf_perfect_partial_and_empty():
    assert entity_prf({"a", "b"}, {"a", "b"}) == (1.0, 1.0, 1.0)
    precision, recall, f1 = entity_prf({"a"}, {"a", "b"})
    assert precision == 1.0 and recall == 0.5 and f1 == pytest.approx(2 / 3)
    assert entity_prf(set(), set()) == (1.0, 1.0, 1.0)
    assert entity_prf({"x"}, set())[2] == 0.0


def test_analysis_metrics_on_brand():
    analysis = analyze_query("Doliprane 1000")
    metrics = analysis_metrics(
        analysis,
        {"gold_entities": ["PARACETAMOL"], "gold_intent": "unknown",
         "should_abstain": False},
    )
    assert metrics["entity_f1"] == 1.0
    assert metrics["intent_correct"] is True
    assert metrics["abstention_correct"] is True


# --------------------------------------------------------------- modes L5
def test_run_evaluation_legacy_shape_is_preserved():
    results = run_evaluation(retriever=FakeRetriever())
    assert set(results["aggregate"]) == {"bm25", "dense", "hybrid"}
    assert "Q1" in results["per_query"]
    assert "sources@10" in results["per_query"]["Q1"]["bm25"]


@pytest.mark.parametrize("mode", ["raw", "normalized", "graph", "normalized+graph"])
def test_run_evaluation_single_mode(mode):
    results = run_evaluation(
        retriever=FakeRetriever(), mode=mode, method="bm25", queries=QUERIES[:1]
    )
    assert results["mode"] == mode
    assert results["method"] == "bm25"
    assert "analysis" in results and "analysis_aggregate" in results
    assert "latency_ms" in results["per_query"]["Q1"]


def test_run_week3_evaluation_covers_all_modes():
    report = run_week3_evaluation(
        retriever=FakeRetriever(),
        methods=("bm25",),
        modes=("raw", "normalized", "graph"),
        queries=QUERIES[:2],
    )
    assert set(report["results"]) == {
        ("raw", "bm25"), ("normalized", "bm25"), ("graph", "bm25")
    }
    assert set(report["analysis_aggregate"]) == {
        "entity_f1", "intent_accuracy", "abstention_accuracy"
    }


# --------------------------------------------------------------- jeu de données
def test_all_queries_have_analysis_metadata():
    for query in QUERIES:
        assert "gold_entities" in query, query["id"]
        assert "gold_intent" in query, query["id"]
        assert "should_abstain" in query, query["id"]


def test_new_week3_questions_are_present():
    ids = {query["id"] for query in QUERIES}
    assert {"Q18", "Q19", "Q20", "Q21", "Q22"} <= ids


def test_out_of_scope_question_expects_abstention():
    query = next(q for q in QUERIES if q["id"] == "Q21")
    assert query["should_abstain"] is True
    assert query["gold"] == []


def test_conflict_question_has_three_registries():
    query = next(q for q in QUERIES if q["id"] == "Q22")
    prefixes = {gold.split(":", 1)[0] for gold in query["gold"]}
    assert {"nomenclature", "nomenclature_dz", "pharmnet"} <= prefixes


def test_all_gold_ids_exist_in_corpus():
    if not CORPUS_PATH.exists():
        pytest.skip("corpus absent")
    ids = set()
    with open(CORPUS_PATH, encoding="utf-8") as handle:
        for line in handle:
            ids.add(json.loads(line)["chunk_id"])
    missing = [
        (query["id"], gold)
        for query in QUERIES
        for gold in query["gold"]
        if gold not in ids
    ]
    assert not missing, missing
