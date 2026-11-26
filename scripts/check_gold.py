"""Vérifie que tous les passages gold existent dans le corpus.

Couvre les questions de `evaluation.py` (Q1–Q22 + Q3f) et la liste historique
de contrôle de la semaine 2. Échoue avec un code non nul si un identifiant est
absent, ce qui empêche d'évaluer sur un gold invalide.

Usage : python scripts/check_gold.py
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pharmeazor.config import CORPUS_PATH  # noqa: E402
from pharmeazor.evaluation import QUERIES  # noqa: E402

A_VERIFIER = [
    "pharmnet:amoxicilline acide clavulanique",
    "nomenclature:amoxicilline acide clavulanique",
    "pharmnet:paracetamol",
    "thesaurus:inhibiteurs de l enzyme de conversion:305:0",
    "thesaurus:anticoagulants oraux:49:1",
    "thesaurus:acide acetylsalicylique:5:2",
    "thesaurus:clarithromycine:130:0",
    "thesaurus:clarithromycine:130:1",
    "nomenclature:amlodipine besilate amlodipine",
    "nomenclature:amlodipine besilate exprime en amlodipine",
    "nomenclature:clarithromycine",
    "pharmnet:clarithromycine",
]


def load_ids():
    ids = set()
    with open(CORPUS_PATH, encoding="utf-8") as handle:
        for line in handle:
            ids.add(json.loads(line)["chunk_id"])
    return ids


def main():
    all_ids = load_ids()
    errors = []

    for query in QUERIES:
        for gold in query["gold"]:
            if gold not in all_ids:
                errors.append(f"{query['id']}: {gold}")
        if "gold_intent" not in query or "should_abstain" not in query:
            errors.append(f"{query['id']}: métadonnées d'analyse absentes")

    for gold in A_VERIFIER:
        if gold not in all_ids:
            errors.append(f"contrôle S2: {gold}")

    checked = sum(len(query["gold"]) for query in QUERIES) + len(A_VERIFIER)
    if errors:
        print(f"❌ {len(errors)} identifiant(s) gold absent(s) :")
        for error in errors:
            print("  -", error)
        return 1

    print(f"✅ {checked} identifiants gold vérifiés dans le corpus "
          f"({len(QUERIES)} questions).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
