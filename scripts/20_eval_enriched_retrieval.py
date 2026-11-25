"""L4 — Recherche enrichie : comparaison brut / normalisé / graphe + latence.

Questions : evaluation.py (Q1-Q17, sauf variantes) + jeu de test (questions avec gold).

Usage :
    python scripts/20_eval_enriched_retrieval.py              # bm25, dense, hybride
    python scripts/20_eval_enriched_retrieval.py --bm25-only  # sans FAISS ni modèle

Sortie : data/processed/week_3/l4_enriched_retrieval.md
"""
import json
import statistics
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, "src")

from pharmeazor.config import PROCESSED  # noqa: E402
from pharmeazor.evaluation import QUERIES, _hit_at, _mrr  # noqa: E402
from pharmeazor.retrieval import Retriever  # noqa: E402

BM25_ONLY = "--bm25-only" in sys.argv
METHODS = ("bm25",) if BM25_ONLY else ("bm25", "dense", "hybrid")
MODES = {
    "brut (sem. 2)": {},
    "normalisé": {"normalize": True},
    "graphe": {"expand": True},
    "normalisé + graphe": {"normalize": True, "expand": True},
}
TESTSET = PROCESSED / "week_2" / "test_questions.json"
OUT = PROCESSED / "week_3" / "l4_enriched_retrieval.md"
WATCH = ("Q1", "Q2", "Q3", "Q16")  # critères d'acceptation du plan L4


def load_questions():
    qs = [(q["id"], q["type"], q["question"], q["gold"])
          for q in QUERIES if q["gold"] and not q.get("variant")]
    for q in json.load(open(TESTSET, encoding="utf-8")):
        if q["gold"]:
            qs.append((q["id"], q["type"], q["question"], q["gold"]))
    return qs


def main():
    qs = load_questions()
    r = Retriever(load_dense=not BM25_ONLY)
    for m in METHODS:  # chauffe : modèle, graphe, caches
        r.search(qs[0][2], 10, method=m, normalize=True, expand=True)

    table, per_q = {}, {}
    for method in METHODS:
        for mode, kw in MODES.items():
            mrr = hit = 0.0
            lat = []
            for qid, _, question, gold in qs:
                t = time.perf_counter()
                ranked = [x["chunk_id"] for x in r.search(question, 100, method=method, **kw)]
                lat.append((time.perf_counter() - t) * 1000)
                m, h = _mrr(ranked, gold), _hit_at(ranked, gold, 10)
                mrr += m
                hit += h
                per_q[(qid, method, mode)] = m
            lat.sort()
            table[(method, mode)] = (mrr / len(qs), hit / len(qs), statistics.median(lat),
                                     lat[int(0.95 * (len(lat) - 1))])

    lines = ["# L4 — Recherche enrichie : brut vs normalisé vs graphe\n",
             f"{len(qs)} questions avec passage gold (evaluation.py Q1-Q17 + jeu de test). "
             f"Méthodes : {', '.join(METHODS)}" + (" (mode BM25 seul)" if BM25_ONLY else "") + ".\n",
             "**Attention :** les poids (boosts, poids des variantes) ont été réglés sur ces mêmes "
             "questions ; les gains sont donc optimistes. Une évaluation sur des questions "
             "non vues (L5) est nécessaire.\n",
             "## Résultats et latence\n",
             "| Méthode | Mode | MRR | Hit@10 | Latence médiane (ms) | Latence p95 (ms) |",
             "|---|---|---:|---:|---:|---:|"]
    for (method, mode), (mrr, hit, med, p95) in table.items():
        lines.append(f"| {method} | {mode} | {mrr:.3f} | {hit:.3f} | {med:.1f} | {p95:.1f} |")

    lines += ["\n## Questions du critère d'acceptation (MRR)\n",
              "| Question | Méthode | " + " | ".join(MODES) + " |",
              "|---|---|" + "---:|" * len(MODES)]
    for qid in WATCH:
        for method in METHODS:
            if (qid, method, "brut (sem. 2)") in per_q:
                cells = " | ".join(f"{per_q[(qid, method, mode)]:.2f}" for mode in MODES)
                lines.append(f"| {qid} | {method} | {cells} |")

    best = "normalisé + graphe"
    lines += [f"\n## Régressions ({best} < brut, MRR)\n"]
    regress = [(qid, method, per_q[(qid, method, 'brut (sem. 2)')], per_q[(qid, method, best)])
               for qid, *_ in qs for method in METHODS
               if per_q[(qid, method, best)] + 1e-9 < per_q[(qid, method, "brut (sem. 2)")]]
    if regress:
        lines += ["| Question | Méthode | Brut | Enrichi |", "|---|---|---:|---:|"]
        lines += [f"| {q} | {m} | {a:.2f} | {b:.2f} |" for q, m, a, b in regress]
    else:
        lines.append("Aucune.")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\nÉcrit : {OUT}")


if __name__ == "__main__":
    main()
