"""L5 — Évaluation & benchmark de la semaine 3.

Produit un rapport reproductible (raw vs normalized vs graph) et les métriques
d'analyse (entity F1, intent accuracy, abstention accuracy) sur les questions
Q1–Q22 + la variante Q3f.

Usage :
    python scripts/14_eval_week3.py                # bm25, dense, hybride
    python scripts/14_eval_week3.py --bm25-only    # sans FAISS ni modèle
    python scripts/14_eval_week3.py --methods bm25,hybrid

Sorties :
    data/processed/week_3/eval_week3.md
    data/processed/week_2/retrieval_comparison.md (régénéré en mode complet)
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pharmeazor.config import CORPUS_PATH, PROCESSED  # noqa: E402
from pharmeazor.evaluation import (  # noqa: E402
    MAX_K,
    MODES,
    QUERIES,
    render_markdown,
    run_week3_evaluation,
)
from pharmeazor.retrieval import Retriever  # noqa: E402

OUT = PROCESSED / "week_3" / "eval_week3.md"
COMPARISON = PROCESSED / "week_2" / "retrieval_comparison.md"
ALL_METHODS = ("bm25", "dense", "hybrid")
HELDOUT = PROCESSED / "week_3" / "heldout_questions.json"
TESTSET = PROCESSED / "week_2" / "test_questions.json"
ENRICH = Path(__file__).resolve().parents[1] / "src" / "pharmeazor" / "enrich.py"
ENRICHED = ("normalized", "graph", "normalized+graph")


def load_heldout():
    """10 questions tenues à l'écart du réglage de L4 (scripts/21_build_heldout.py)."""
    data = json.loads(HELDOUT.read_text(encoding="utf-8"))
    queries = [{**q, "category": q["type"], "type": "positive"} for q in data["questions"]]
    current = hashlib.sha256(ENRICH.read_bytes()).hexdigest()[:12]
    return queries, data["frozen_enrich_sha256"], current


def tuning_questions():
    """Les 40 questions sur lesquelles les poids de L4 ont été réglés (semaine 3)."""
    tuned = {f"Q{i}" for i in range(1, 18)}
    out = [{"id": q["id"], "type": "positive", "question": q["question"], "gold": q["gold"]}
           for q in QUERIES if q["id"] in tuned and q.get("gold") and not q.get("variant")]
    for q in json.loads(TESTSET.read_text(encoding="utf-8")):
        if q["gold"]:
            out.append({"id": q["id"], "type": "positive", "question": q["question"],
                        "gold": q["gold"]})
    return out


def parse_args():
    parser = argparse.ArgumentParser(description="Évaluation semaine 3 (L5)")
    parser.add_argument("--bm25-only", action="store_true",
                        help="ne charge ni FAISS ni le modèle d'embedding")
    parser.add_argument("--methods", default="bm25,dense,hybrid",
                        help="méthodes séparées par des virgules (défaut: toutes)")
    parser.add_argument("--k", type=int, default=MAX_K, help="profondeur d'évaluation")
    return parser.parse_args()


def corpus_ids():
    ids = set()
    with open(CORPUS_PATH, encoding="utf-8") as handle:
        for line in handle:
            ids.add(json.loads(line)["chunk_id"])
    return ids


def validate_gold(ids):
    missing = []
    for query in QUERIES:
        for gold_id in query["gold"]:
            if gold_id not in ids:
                missing.append((query["id"], gold_id))
        if "gold_intent" not in query or "should_abstain" not in query:
            missing.append((query["id"], "métadonnées d'analyse absentes"))
    return missing


def fmt(value):
    return f"{value:.3f}"


def build_markdown(report, methods, modes, missing, heldout=None, gap=None):
    results = report["results"]
    positives = [
        q for q in QUERIES
        if q["type"] == "positive" and not q.get("variant") and q.get("gold")
    ]
    new_questions = [q for q in QUERIES if q["id"] in {"Q18", "Q19", "Q20", "Q21", "Q22"}]

    lines = [
        "# Évaluation de la semaine 3 — L5\n",
        "## Protocole\n",
        f"- **{len(QUERIES)} questions** : Q1–Q22 et la variante Q3f ; "
        f"{len(positives)} positives avec passage gold.",
        "- **Modes** : `raw` (recherche semaine 2 inchangée), `normalized` "
        "(variantes DCI/classes + boost métadonnées), `graph` (expansion L3), "
        "`normalized+graph` (les deux, mode recommandé par L4).",
        f"- **Méthodes** : {', '.join(methods)}.",
        f"- **Profondeur** : top-{report['k']} ; MRR plafonné à {MAX_K}.",
        "- **Gold** : identifiants vérifiés dans `corpus.jsonl` par ce script.",
        "",
        "> Les poids de la recherche enrichie (L4) ont été réglés sur ces mêmes "
        "questions : les gains sont optimistes. Le but ici est la comparaison "
        "avant/après et la couverture des métriques, pas une estimation non biaisée.\n",
        "## Questions ajoutées pour L5\n",
        "| ID | Type | Question | Entités à reconnaître (analyse L2) |",
        "|---|---|---|---|",
    ]
    for query in new_questions:
        expected = "abstention" if query.get("should_abstain") else (
            ", ".join(query.get("gold_entities") or ["—"])
        )
        lines.append(
            f"| {query['id']} | {query['type']} | {query['question']} | {expected} |"
        )

    lines += ["\n## Validation du gold\n"]
    if missing:
        lines.append(f"**{len(missing)} problème(s) détecté(s) :**\n")
        lines += [f"- `{qid}` : `{item}`" for qid, item in missing]
    else:
        lines.append(
            f"Tous les identifiants gold ({sum(len(q['gold']) for q in QUERIES)}) "
            "existent dans le corpus, et toutes les questions ont leurs "
            "métadonnées d'analyse."
        )

    lines += [
        "\n## Avant / après (retrieval)\n",
        "| Méthode | Mode | MRR@100 | Hit@10 | Recall@10 | nDCG@10 | "
        "Latence médiane (ms) | Latence p95 (ms) |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for method in methods:
        for mode in modes:
            row = results[(mode, method)]
            agg = row["aggregate"]
            if not agg:
                continue
            lines.append(
                f"| {method} | {mode} | {fmt(agg['mrr'])} | {fmt(agg['hit@10'])} | "
                f"{fmt(agg['recall@10'])} | {fmt(agg['ndcg@10'])} | "
                f"{row['latency']['median_ms']:.1f} | {row['latency']['p95_ms']:.1f} |"
            )

    analysis = report["analysis_aggregate"]
    lines += [
        "\n## Analyse des requêtes (L2)\n",
        "| Métrique | Valeur |",
        "|---|---:|",
        f"| Entity F1 | {fmt(analysis.get('entity_f1', 0.0))} |",
        f"| Intent accuracy | {fmt(analysis.get('intent_accuracy', 0.0))} |",
        f"| Abstention accuracy | {fmt(analysis.get('abstention_accuracy', 0.0))} |",
        "",
        "Entity F1 compare les DCI prédites (et les classes seules quand la "
        "question ne cite pas de DCI) aux entités attendues. L'abstention "
        "compare `analyze_query(...).out_of_scope` à l'attente de refus.",
    ]

    lines += ["\n## Détail par question (MRR)\n"]
    for method in methods:
        lines += [
            f"### {method}\n",
            "| Question | Type | " + " | ".join(modes) + " |",
            "|---|---|" + "---:|" * len(modes),
        ]
        for query in positives:
            cells = []
            for mode in modes:
                row = results[(mode, method)]["per_query"][query["id"]]
                cells.append(fmt(row["mrr"]))
            lines.append(
                f"| {query['id']} | {query['type']} | " + " | ".join(cells) + " |"
            )

    lines += ["\n## Régressions du mode enrichi\n"]
    regressions = []
    for method in methods:
        for query in positives:
            raw = results[("raw", method)]["per_query"][query["id"]]["mrr"]
            for mode in [m for m in ENRICHED if m in modes]:
                value = results[(mode, method)]["per_query"][query["id"]]["mrr"]
                if value + 1e-9 < raw:
                    regressions.append((query["id"], method, mode, raw, value))
    if regressions:
        lines += ["| Question | Méthode | Mode | Raw | Enrichi |",
                  "|---|---|---|---:|---:|"]
        lines += [f"| {qid} | {m} | {mode} | {fmt(raw)} | {fmt(value)} |"
                  for qid, m, mode, raw, value in regressions]
    else:
        lines.append("Aucune régression de MRR par rapport au mode brut.")

    if heldout:
        lines += heldout_section(heldout, methods, modes)
    if gap:
        lines += gap_section(gap, methods)

    lines += ["\n## Erreurs d'analyse (cas concrets)\n"]
    errors = []
    for query in QUERIES:
        row = report["analysis"][query["id"]]
        if not row["intent_correct"] or not row["abstention_correct"] or row["entity_f1"] < 1.0:
            errors.append((query, row))
    if errors:
        lines += ["| Question | Entity F1 | Intention (prévu / attendu) | "
                  "Abstention (prévu / attendu) | Entités (prévu / attendu) |",
                  "|---|---:|---|---|---|"]
        for query, row in errors:
            lines.append(
                f"| {query['id']} | {fmt(row['entity_f1'])} | "
                f"{row['predicted_intent']} / {row['gold_intent']} | "
                f"{row['predicted_abstain']} / {row['gold_abstain']} | "
                f"{', '.join(row['predicted_entities']) or '—'} / "
                f"{', '.join(row['gold_entities']) or '—'} |"
            )
    else:
        lines.append("Aucune erreur d'analyse sur ce jeu de questions.")

    lines += [
        "\n## Reproduction\n",
        "```powershell",
        ".venv\\Scripts\\python.exe scripts\\14_eval_week3.py",
        ".venv\\Scripts\\python.exe scripts\\14_eval_week3.py --bm25-only",
        ".venv\\Scripts\\python.exe -m pytest tests -q",
        "```",
        "",
        "Fichier généré : `data/processed/week_3/eval_week3.md`.",
    ]
    return "\n".join(lines) + "\n"


def heldout_section(heldout, methods, modes):
    report, frozen, current = heldout["report"], heldout["frozen"], heldout["current"]
    results, queries = report["results"], report["queries"]
    lines = ["\n## Jeu tenu à l'écart (10 questions non vues par le réglage)\n",
             "Les questions H01–H10 (`scripts/21_build_heldout.py`) portent sur des "
             "médicaments et des paires absents des questions utilisées pour régler L4. "
             "Elles ont été écrites avant leur première évaluation, et les poids de L4 n'ont "
             "pas été modifiés depuis. Un gold a été corrigé après la première exécution "
             "(H06 : l'entrée directe fluoxétine + tramadol, plus grave, manquait) ; la "
             "correction est notée dans le fichier. Les paires du Thésaurus comptent les "
             "deux sens.\n"]
    if frozen == current:
        lines.append(f"Poids de L4 inchangés depuis la création du jeu "
                     f"(empreinte de `enrich.py` : `{frozen}`).\n")
    else:
        lines.append(f"**Attention : `enrich.py` a changé depuis la création du jeu "
                     f"({frozen} → {current}). Ces questions ne sont plus tenues à "
                     f"l'écart.**\n")
    lines += ["| Méthode | Mode | MRR@100 | Hit@10 |", "|---|---|---:|---:|"]
    for method in methods:
        for mode in modes:
            agg = results[(mode, method)]["aggregate"]
            lines.append(f"| {method} | {mode} | {fmt(agg['mrr'])} | {fmt(agg['hit@10'])} |")
    for method in methods:
        lines += [f"\n### Détail par question — {method} (MRR)\n",
                  "| Question | Catégorie | Énoncé | " + " | ".join(modes) + " |",
                  "|---|---|---|" + "---:|" * len(modes)]
        for q in queries:
            cells = " | ".join(fmt(results[(m, method)]["per_query"][q["id"]]["mrr"])
                               for m in modes)
            lines.append(f"| {q['id']} | {q['category']} | {q['question']} | {cells} |")
    worse = [(q["id"], method, mode,
              results[("raw", method)]["per_query"][q["id"]]["mrr"],
              results[(mode, method)]["per_query"][q["id"]]["mrr"])
             for method in methods for q in queries for mode in ENRICHED if mode in modes
             if results[(mode, method)]["per_query"][q["id"]]["mrr"] + 1e-9
             < results[("raw", method)]["per_query"][q["id"]]["mrr"]]
    lines.append("\n### Questions qui se dégradent (MRR enrichi < brut)\n")
    if worse:
        lines += ["| Question | Méthode | Mode | Brut | Enrichi |", "|---|---|---|---:|---:|"]
        lines += [f"| {q} | {m} | {mode} | {fmt(a)} | {fmt(b)} |"
                  for q, m, mode, a, b in worse]
    else:
        lines.append("Aucune.")
    return lines


def gap_section(gap, methods):
    lines = ["\n## Pourquoi deux chiffres (0,820 et 0,571)\n",
             "Les deux chiffres publiés en semaine 3 ne mesuraient pas la même chose : "
             "0,820 (section 5) était le mode `normalized+graph` sur les 40 questions de "
             "réglage de L4 ; 0,571 (section 6) était le mode `normalized` seul sur les "
             "questions de L5. Le tableau les recalcule ici, dans la même exécution.\n",
             "| Méthode | Jeu de questions | n | normalized | normalized+graph |",
             "|---|---|---:|---:|---:|"]
    for method in methods:
        for label, rep in gap:
            res = rep["results"]
            n = len([q for q in rep["queries"] if q["type"] == "positive"
                     and not q.get("variant") and q.get("gold")])
            lines.append(f"| {method} | {label} | {n} | "
                         f"{fmt(res[('normalized', method)]['aggregate']['mrr'])} | "
                         f"{fmt(res[('normalized+graph', method)]['aggregate']['mrr'])} |")
    lines.append("\nLecture : sur un même jeu, l'écart entre les deux colonnes vient du mode ; "
                 "sur une même colonne, l'écart entre les lignes vient des questions. "
                 "Seule la ligne « tenu à l'écart » porte sur des questions qui n'ont pas "
                 "servi au réglage (10 questions : un ordre de grandeur, pas une preuve).")
    return lines


def main():
    args = parse_args()
    methods = tuple(m.strip() for m in args.methods.split(",") if m.strip())
    if args.bm25_only:
        methods = ("bm25",)
    unknown = [m for m in methods if m not in ALL_METHODS]
    if unknown:
        raise SystemExit(f"Méthode inconnue : {unknown}")

    ids = corpus_ids()
    missing = validate_gold(ids)
    if missing:
        for qid, item in missing:
            print(f"[gold] {qid}: {item}")
        raise SystemExit("Gold invalide : corriger avant d'évaluer.")

    retriever = Retriever(load_dense=not args.bm25_only)
    for method in methods:  # chauffe : modèle, graphe, caches
        retriever.search(QUERIES[0]["question"], 10, method=method,
                         normalize=True, expand=True)

    report = run_week3_evaluation(retriever=retriever, methods=methods, k=args.k)

    held_queries, frozen, current = load_heldout()
    held = {"report": run_week3_evaluation(retriever=retriever, methods=methods,
                                           queries=held_queries, k=args.k),
            "frozen": frozen, "current": current}
    tuned = run_week3_evaluation(retriever=retriever, methods=methods,
                                 modes=("normalized", "normalized+graph"),
                                 queries=tuning_questions(), k=args.k)
    gap = [("40 questions de réglage L4 (section 5)", tuned),
           ("questions L5, Q1–Q22 (section 6)", report),
           ("10 questions tenues à l'écart", held["report"])]
    markdown = build_markdown(report, methods, MODES, missing, heldout=held, gap=gap)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(markdown, encoding="utf-8")
    print(markdown)
    print(f"Écrit : {OUT}")

    if set(methods) == set(ALL_METHODS):
        legacy = {
            "queries": report["queries"],
            "per_query": {
                query["id"]: {
                    method: report["results"][("raw", method)]["per_query"][query["id"]]
                    for method in ALL_METHODS
                }
                for query in QUERIES
            },
            "aggregate": {
                method: report["results"][("raw", method)]["aggregate"]
                for method in ALL_METHODS
            },
            "corpus_size": report["corpus_size"],
            "source_counts": report["source_counts"],
        }
        COMPARISON.write_text(render_markdown(legacy), encoding="utf-8")
        print(f"Régénéré : {COMPARISON}")
    else:
        print("retrieval_comparison.md non régénéré (mode partiel).")


if __name__ == "__main__":
    main()
