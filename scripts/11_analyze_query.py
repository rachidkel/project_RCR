"""Interface CLI d'analyse de requête (Livrable L2 - Mohamed Ali BAGHRICHE).

Usage :
    python scripts/11_analyze_query.py "Peut-on associer l'Amlodipine et l'Ibuprofène ?"
    python scripts/11_analyze_query.py --json "Quel est le dosage de Doliprane 1000 mg ?"
    python scripts/11_analyze_query.py --demo
"""

import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pharmeazor.query import QueryAnalysis, analyze_query


def format_text_output(qa: QueryAnalysis, elapsed_ms: float) -> str:
    lines = [
        "=" * 65,
        "PHARMEAZOR — ANALYSE SÉMANTIQUE DE REQUÊTE (L2)",
        "=" * 65,
        f"Requête brute      : {qa.raw}",
        f"Requête normalisée : {qa.normalized}",
        f"Intention clinique : {qa.intent.upper()}",
        f"Hors périmètre     : {'⚠️ OUI (Refus / Conseil médical)' if qa.out_of_scope else '✅ NON (Dans le périmètre)'}",
        f"Temps d'analyse    : {elapsed_ms:.2f} ms",
        "-" * 65,
        f"Entités identifiées ({len(qa.entities)}) :",
    ]

    if not qa.entities:
        lines.append("  (aucune entité médicamenteuse identifiée)")
    else:
        for idx, ent in enumerate(qa.entities, 1):
            classes_str = ", ".join(ent.classes) if ent.classes else "(aucune classe)"
            lines.extend([
                f"  [{idx}] Terme extrait : \"{ent.term}\" [offsets {ent.start}:{ent.end}]",
                f"      DCI canonique : {ent.dci or '(inconnue / ambiguë)'}",
                f"      Classes       : {classes_str}",
                f"      Confiance     : {ent.confidence:.0%}",
            ])

    lines.extend([
        "-" * 65,
        f"Termes d'expansion ({len(qa.expanded_terms)}) :",
        f"  {', '.join(qa.expanded_terms) if qa.expanded_terms else '(aucun)'}",
        "=" * 65,
    ])
    return "\n".join(lines)


def to_dict(qa: QueryAnalysis, elapsed_ms: float) -> dict:
    return {
        "raw": qa.raw,
        "normalized": qa.normalized,
        "intent": qa.intent,
        "out_of_scope": qa.out_of_scope,
        "elapsed_ms": round(elapsed_ms, 3),
        "entities": [
            {
                "term": e.term,
                "dci": e.dci,
                "classes": e.classes,
                "confidence": round(e.confidence, 3),
                "start": e.start,
                "end": e.end,
            }
            for e in qa.entities
        ],
        "expanded_terms": qa.expanded_terms,
    }


def main():
    args = sys.argv[1:]
    json_mode = "--json" in args
    demo_mode = "--demo" in args

    if json_mode:
        args.remove("--json")
    if demo_mode:
        args.remove("--demo")

    if demo_mode or not args:
        queries = [
            "Peut-on associer l'Amlodipine et l'Ibuprofène ?",
            "Quel est le dosage de Doliprane 1000 mg chez l'adulte ?",
            "Quelles sont les contre-indications du gel KOPROFEN ?",
            "Quel est le prix du sirop Doliprane ?",
            "Quel médicament prendre pour mes douleurs dentaires ?",
            "Est-ce que l'aspirine est contre-indiquée avec le Triatec ?",
        ]
        print(f"--- DÉMONSTRATION L2 : {len(queries)} REQUÊTES TYPES ---\n")
        for q in queries:
            t0 = time.perf_counter()
            qa = analyze_query(q)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            print(format_text_output(qa, elapsed_ms))
            print()
        return

    query = " ".join(args)
    t0 = time.perf_counter()
    qa = analyze_query(query)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    if json_mode:
        print(json.dumps(to_dict(qa, elapsed_ms), ensure_ascii=False, indent=2))
    else:
        print(format_text_output(qa, elapsed_ms))


if __name__ == "__main__":
    main()
