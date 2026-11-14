import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pharmeazor.config import PROCESSED  # noqa: E402
from pharmeazor.evaluation import render_markdown, run_evaluation  # noqa: E402

OUTPUT = PROCESSED / "week_2" / "retrieval_comparison.md"


def main():
    print("Évaluation BM25 / dense / hybride en cours...")
    results = run_evaluation()

    markdown = render_markdown(results)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(markdown, encoding="utf-8")

    print("\nRésultats agrégés (questions réelles Q1, Q2, Q3) :")
    print(f"{'méthode':<8} {'R@10':>6} {'R@50':>6} {'Hit@10':>7} {'MRR':>6} {'nDCG@10':>8}")
    for method, agg in results["aggregate"].items():
        print(
            f"{method:<8} {agg['recall@10']:>6.3f} {agg['recall@50']:>6.3f} "
            f"{agg['hit@10']:>7.3f} {agg['mrr']:>6.3f} {agg['ndcg@10']:>8.3f}"
        )

    print(f"\nRapport écrit : {OUTPUT}")


if __name__ == "__main__":
    main()
