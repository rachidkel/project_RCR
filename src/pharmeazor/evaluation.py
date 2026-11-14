import math
from collections import Counter

from .retrieval import Retriever


QUERIES = [
    {
        "id": "Q1",
        "type": "positive",
        "question": "Quel est le dosage disponible du paracétamol ?",
        "gold": ["nomenclature:paracetamol"],
    },
    {
        "id": "Q2",
        "type": "positive",
        "question": "Peut-on associer l'ibuprofène et l'aspirine ? Quel est le niveau d'interaction ?",
        "gold": [
            "thesaurus:anti inflammatoires non steroidiens:56:1",
            "thesaurus:acide acetylsalicylique:5:3",
        ],
    },
    {
        "id": "Q3",
        "type": "positive",
        "question": (
            "Pour un patient hypertendu âgé qui prend déjà régulièrement de "
            "l'Amlodipine, est-il possible de lui associer de l'Ibuprofène pour "
            "traiter des douleurs articulaires ? Quel est le niveau d'interaction "
            "documenté, quelles sont les précautions ou contre-indications "
            "spécifiques, quelle est la posologie maximale recommandée, et que "
            "disent les sources officielles à ce sujet ?"
        ),
        "gold": [
            "thesaurus:anti inflammatoires non steroidiens:56:2",
            "thesaurus:anti inflammatoires non steroidiens:56:5",
            "thesaurus:anti inflammatoires non steroidiens:56:9",
            "thesaurus:anti inflammatoires non steroidiens:56:13",
        ],
    },
    {
        "id": "Q3f",
        "type": "positive",
        "variant": True,
        "question": "interaction anti-inflammatoires non stéroïdiens et antihypertenseurs",
        "gold": [
            "thesaurus:anti inflammatoires non steroidiens:56:2",
            "thesaurus:anti inflammatoires non steroidiens:56:5",
            "thesaurus:anti inflammatoires non steroidiens:56:9",
            "thesaurus:anti inflammatoires non steroidiens:56:13",
        ],
    },
    {
        "id": "Q4",
        "type": "meta",
        "question": "Deux sources donnent une dose maximale différente : que doit répondre le système ?",
        "gold": [],
    },
    {
        "id": "Q5",
        "type": "negative",
        "question": "Quel médicament prendre pour mes douleurs dentaires ?",
        "gold": [],
    },
]

METHODS = ("bm25", "dense", "hybrid")
MAX_K = 100


def _recall_at(ranked, gold, k):
    if not gold:
        return None
    return len(set(ranked[:k]) & set(gold)) / len(gold)


def _hit_at(ranked, gold, k):
    return 1.0 if set(ranked[:k]) & set(gold) else 0.0


def _mrr(ranked, gold, max_k=MAX_K):
    gold_set = set(gold)
    for rank, chunk_id in enumerate(ranked[:max_k], start=1):
        if chunk_id in gold_set:
            return 1.0 / rank
    return 0.0


def _ndcg_at(ranked, gold, k):
    gold_set = set(gold)
    if not gold_set:
        return None
    dcg = sum(
        1.0 / math.log2(rank + 2)
        for rank, chunk_id in enumerate(ranked[:k])
        if chunk_id in gold_set
    )
    idcg = sum(1.0 / math.log2(rank + 2) for rank in range(min(len(gold_set), k)))
    return dcg / idcg if idcg else 0.0


def _ranked(retriever, question, method, k=MAX_K):
    if method == "dense":
        return [chunk_id for chunk_id, _ in retriever.search_dense(question, k)]
    if method == "bm25":
        return [chunk_id for chunk_id, _ in retriever.search_bm25(question, k)]
    return [chunk_id for chunk_id, _ in retriever.search_hybrid(question, k, pool=k)]


def run_evaluation(retriever=None):
    retriever = retriever or Retriever()
    per_query = {}

    for query in QUERIES:
        per_query[query["id"]] = {}
        for method in METHODS:
            ranked = _ranked(retriever, query["question"], method)
            per_query[query["id"]][method] = {
                "ranked": ranked,
                "recall@10": _recall_at(ranked, query["gold"], 10),
                "recall@50": _recall_at(ranked, query["gold"], 50),
                "hit@10": _hit_at(ranked, query["gold"], 10),
                "mrr": _mrr(ranked, query["gold"]),
                "ndcg@10": _ndcg_at(ranked, query["gold"], 10),
                "sources@10": Counter(
                    retriever.by_id[cid]["source_id"]
                    for cid in ranked[:10]
                    if cid in retriever.by_id
                ),
            }

    aggregate = {}
    positives = [
        q for q in QUERIES if q["type"] == "positive" and not q.get("variant")
    ]
    for method in METHODS:
        aggregate[method] = {
            metric: sum(per_query[q["id"]][method][metric] for q in positives) / len(positives)
            for metric in ("recall@10", "recall@50", "hit@10", "mrr", "ndcg@10")
        }

    return {"queries": QUERIES, "per_query": per_query, "aggregate": aggregate}


def render_markdown(results):
    lines = []
    lines.append("# Comparaison BM25 vs recherche sémantique — Semaine 2\n")
    lines.append(f"Corpus : 7 000 chunks (ANSM Thésaurus, MIPH, EMA, DWA). Top-{MAX_K} évalué.\n")
    lines.append("## Résultats agrégés (questions réelles Q1, Q2, Q3)\n")
    lines.append("| Méthode | Recall@10 | Recall@50 | Hit@10 | MRR@100 | nDCG@10 |")
    lines.append("|---|---|---|---|---|---|")
    for method in METHODS:
        agg = results["aggregate"][method]
        lines.append(
            f"| {method} | {agg['recall@10']:.3f} | {agg['recall@50']:.3f} | "
            f"{agg['hit@10']:.3f} | {agg['mrr']:.3f} | {agg['ndcg@10']:.3f} |"
        )

    lines.append("\n## Détail par question\n")
    lines.append("| Question | Méthode | Recall@10 | Recall@50 | MRR | nDCG@10 |")
    lines.append("|---|---|---|---|---|---|")
    for query in results["queries"]:
        if query["type"] != "positive":
            continue
        label = query["id"] + (" (variante)" if query.get("variant") else "")
        for method in METHODS:
            row = results["per_query"][query["id"]][method]
            lines.append(
                f"| {label} | {method} | {row['recall@10']:.3f} | "
                f"{row['recall@50']:.3f} | {row['mrr']:.3f} | {row['ndcg@10']:.3f} |"
            )

    lines.append(
        "\n*Q3f est une variante diagnostique de Q3 (requête courte et ciblée) : "
        "elle n'entre pas dans l'agrégat et sert à isoler l'effet de la formulation.*"
    )

    lines.append("\n## Composition des sources dans le top-10\n")
    for query in results["queries"]:
        if query["type"] != "positive":
            continue
        lines.append(f"### {query['id']}\n")
        for method in METHODS:
            sources = results["per_query"][query["id"]][method]["sources@10"]
            pretty = ", ".join(f"{sid} ({n})" for sid, n in sources.most_common())
            lines.append(f"- **{method}** : {pretty}")
        lines.append("")

    lines.append("## Requêtes méta / hors périmètre\n")
    for query in results["queries"]:
        if query["type"] == "positive":
            continue
        lines.append(f"### {query['id']} ({query['type']})\n")
        lines.append(f"> {query['question']}\n")
        for method in METHODS:
            ranked = results["per_query"][query["id"]][method]["ranked"]
            top = ranked[:3]
            lines.append(f"- **{method}** top-3 : {', '.join(top)}")
        lines.append("")

    return "\n".join(lines)
