"""Évalue BM25 / dense / hybride sur les 30 questions de test.

Usage :
    python scripts/13_eval_testset.py              # 3 méthodes (modèle d'embedding requis)
    python scripts/13_eval_testset.py --bm25-only  # BM25 seul, sans modèle ni index FAISS

Sorties : data/processed/week_2/testset_results.md et testset_results.json
"""
import json
import sys
import time
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, "src")

from pharmeazor.config import CORPUS_PATH, INDEX_DIR, PROCESSED  # noqa: E402
from pharmeazor.evaluation import MAX_K, _hit_at, _mrr, _ndcg_at, _recall_at  # noqa: E402

TESTSET = PROCESSED / "week_2" / "test_questions.json"
OUT_MD = PROCESSED / "week_2" / "testset_results.md"
OUT_JSON = PROCESSED / "week_2" / "testset_results.json"
BM25_ONLY = "--bm25-only" in sys.argv
METHODS = ("bm25",) if BM25_ONLY else ("bm25", "dense", "hybrid")
METRICS = ("hit@10", "recall@10", "recall@50", "mrr", "ndcg@10")


def make_retriever():
    from pharmeazor.retrieval import Retriever
    if not BM25_ONLY:
        return Retriever()
    # Mode rapide : pas de FAISS ni de modèle d'embedding
    from pharmeazor.corpus import load_corpus
    from pharmeazor.index import load_bm25, load_bm25_ids
    from pharmeazor.thesaurus import load_lookup
    r = Retriever.__new__(Retriever)
    r.records = load_corpus(CORPUS_PATH)
    r.by_id = {x["chunk_id"]: x for x in r.records}
    r.bm25 = load_bm25(INDEX_DIR)
    r.bm25_ids = load_bm25_ids(INDEX_DIR)
    r.thesaurus = load_lookup()
    return r


def ranked_ids(retriever, question, method):
    fn = {"bm25": retriever.search_bm25, "dense": getattr(retriever, "search_dense", None),
          "hybrid": lambda q, k: retriever.search_hybrid(q, k, pool=k)}[method]
    return [cid for cid, _ in fn(question, MAX_K)]


def main():
    questions = json.load(open(TESTSET, encoding="utf-8"))
    retriever = make_retriever()
    scored = [q for q in questions if q["gold"]]
    results = {m: {} for m in METHODS}

    for method in METHODS:
        for q in scored:
            ranked = ranked_ids(retriever, q["question"], method)
            results[method][q["id"]] = {
                "hit@10": _hit_at(ranked, q["gold"], 10),
                "recall@10": _recall_at(ranked, q["gold"], 10),
                "recall@50": _recall_at(ranked, q["gold"], 50),
                "mrr": _mrr(ranked, q["gold"]),
                "ndcg@10": _ndcg_at(ranked, q["gold"], 10),
                "top3": ranked[:3],
            }

    def mean(method, ids, metric):
        vals = [results[method][i][metric] for i in ids]
        return sum(vals) / len(vals) if vals else float("nan")

    all_ids = [q["id"] for q in scored]
    by_type = defaultdict(list)
    for q in scored:
        by_type[q["type"]].append(q["id"])

    # Détection hors périmètre (filtre actuel de Retriever.is_out_of_scope)
    oos = [q for q in questions if q["behavior"] == "refuse"]
    oos_rows = []
    for q in oos:
        try:
            flagged, why = retriever.is_out_of_scope(q["question"])
        except Exception as e:  # mode --bm25-only : le filtre a besoin du modèle dense
            flagged, why = None, f"non évalué ({type(e).__name__})"
        oos_rows.append((q["id"], q["question"], flagged, why))

    # Lookup exact du Thésaurus vs BM25 sur les questions d'interaction.
    exact_rows = []
    for q in scored:
        if not any(cid.startswith("thesaurus:") for cid in q["gold"]):
            continue
        exact = [cid for cid, _ in retriever.search_exact(q["question"], MAX_K)]
        bm25 = [cid for cid, _ in retriever.search_bm25(q["question"], MAX_K)]
        exact_rows.append({
            "id": q["id"],
            "question": q["question"],
            "exact_hit": _hit_at(exact, q["gold"], 10),
            "bm25_hit": _hit_at(bm25, q["gold"], 10),
            "exact_mrr": _mrr(exact, q["gold"]),
            "bm25_mrr": _mrr(bm25, q["gold"]),
            "exact_top1": exact[0] if exact else "—",
        })

    lines = [f"# Évaluation sur le jeu de test ({len(questions)} questions) — Semaine 2\n"]
    lines.append(f"Corpus : {len(retriever.records)} chunks. {len(scored)} questions avec passage gold "
                 f"sur {len(questions)}. Méthodes : {', '.join(METHODS)}"
                 + (" (mode BM25 seul)" if BM25_ONLY else "") + ".\n")
    lines.append("Hit@10 = au moins un chunk gold dans le top 10. Recall@k = part des chunks gold retrouvés. "
                 "Les questions à gold multiple (C07, T02) ont un Recall structurellement bas : "
                 "Hit@10 et MRR sont les métriques principales.\n")
    lines.append("## Résultats globaux\n")
    lines.append("| Méthode | " + " | ".join(METRICS) + " |")
    lines.append("|---|" + "---|" * len(METRICS))
    for m in METHODS:
        lines.append(f"| {m} | " + " | ".join(f"{mean(m, all_ids, k):.3f}" for k in METRICS) + " |")

    lines.append("\n## Par type de question (Hit@10 / MRR)\n")
    lines.append("| Type | n | " + " | ".join(f"{m} Hit@10 | {m} MRR" for m in METHODS) + " |")
    lines.append("|---|---|" + "---|---|" * len(METHODS))
    for t, ids in by_type.items():
        cells = " | ".join(f"{mean(m, ids, 'hit@10'):.2f} | {mean(m, ids, 'mrr'):.2f}" for m in METHODS)
        lines.append(f"| {t} | {len(ids)} | {cells} |")

    lines.append("\n## Détail par question\n")
    lines.append("| Id | Type | Question | " + " | ".join(f"{m} rang MRR" for m in METHODS) + " |")
    lines.append("|---|---|---|" + "---|" * len(METHODS))
    for q in scored:
        short = q["question"][:60] + ("…" if len(q["question"]) > 60 else "")
        cells = " | ".join(f"{results[m][q['id']]['mrr']:.2f}" for m in METHODS)
        lines.append(f"| {q['id']} | {q['type']} | {short} | {cells} |")

    lines.append("\n## Lookup exact du Thésaurus vs BM25 (questions d'interaction)\n")
    lines.append("| Id | Exact Hit@10 | BM25 Hit@10 | Exact MRR | BM25 MRR | Top-1 exact |")
    lines.append("|---|---:|---:|---:|---:|---|")
    for row in exact_rows:
        lines.append(
            f"| {row['id']} | {row['exact_hit']:.0f} | {row['bm25_hit']:.0f} | "
            f"{row['exact_mrr']:.2f} | {row['bm25_mrr']:.2f} | `{row['exact_top1']}` |"
        )
    if exact_rows:
        lines.append(
            f"\nExact Hit@10 moyen : {sum(r['exact_hit'] for r in exact_rows) / len(exact_rows):.2f} — "
            f"BM25 Hit@10 moyen : {sum(r['bm25_hit'] for r in exact_rows) / len(exact_rows):.2f}."
        )

    lines.append("\n## Questions hors périmètre (filtre actuel `is_out_of_scope`)\n")
    lines.append("| Id | Question | Refusée ? | Raison |")
    lines.append("|---|---|---|---|")
    for qid, qq, flagged, why in oos_rows:
        mark = "oui" if flagged else ("NON (erreur)" if flagged is False else "n/a")
        lines.append(f"| {qid} | {qq[:60]} | {mark} | {why} |")
    known = [r for r in oos_rows if r[2] is not None]
    if known:
        lines.append(f"\nRefus corrects : {sum(1 for r in known if r[2])}/{len(known)} évaluées ({len(oos_rows)} questions hors périmètre au total).")

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    OUT_JSON.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n".join(lines[:14]))
    print(f"\nÉcrit : {OUT_MD}")


if __name__ == "__main__":
    t0 = time.time()
    main()
    print(f"({time.time() - t0:.1f}s)")
