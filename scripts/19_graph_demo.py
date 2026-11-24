
"""Demonstration of the Pharmeazor knowledge graph."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pharmeazor.graph import KnowledgeGraph

GRAPH_PATH = ROOT / "data/processed/week_3/knowledge_graph.json"


def main():
    kg = KnowledgeGraph.load(GRAPH_PATH)

    print("\n=== PHARMEAZOR KNOWLEDGE GRAPH DEMO ===")

    for dci in ["AMLODIPINE", "IBUPROFENE"]:
        print(f"\nInteractions for {dci}:")

        interactions = kg.interactions_for(dci)

        if not interactions:
            print("No interaction records found.")
        else:
            for interaction in interactions:
                print("-", interaction.get("label"))

    print("\n=== ABSENCE EXPLANATION ===")

    explanation = kg.explain_absence("AINS", "AMLODIPINE")
    print(explanation["message"])

    print("\n=== GRAPH STATISTICS ===")
    print(kg.stats())


if __name__ == "__main__":
    main()
