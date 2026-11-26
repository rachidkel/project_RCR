# L4 — Recherche enrichie : brut vs normalisé vs graphe

40 questions avec passage gold (evaluation.py Q1-Q17 + jeu de test). Méthodes : bm25, dense, hybrid.

**Attention :** les poids (boosts, poids des variantes) ont été réglés sur ces mêmes questions ; les gains sont donc optimistes. Une évaluation sur des questions non vues (L5) est nécessaire.

## Résultats et latence

| Méthode | Mode | MRR | Hit@10 | Latence médiane (ms) | Latence p95 (ms) |
|---|---|---:|---:|---:|---:|
| bm25 | brut (sem. 2) | 0.227 | 0.400 | 0.7 | 0.8 |
| bm25 | normalisé | 0.671 | 0.850 | 11.5 | 39.9 |
| bm25 | graphe | 0.429 | 0.625 | 1.0 | 1.8 |
| bm25 | normalisé + graphe | 0.773 | 0.925 | 7.8 | 9.8 |
| dense | brut (sem. 2) | 0.313 | 0.450 | 31.6 | 42.7 |
| dense | normalisé | 0.693 | 0.800 | 39.5 | 51.0 |
| dense | graphe | 0.546 | 0.775 | 31.8 | 41.5 |
| dense | normalisé + graphe | 0.785 | 0.900 | 39.9 | 55.3 |
| hybrid | brut (sem. 2) | 0.350 | 0.525 | 31.9 | 41.9 |
| hybrid | normalisé | 0.719 | 0.850 | 41.1 | 53.3 |
| hybrid | graphe | 0.600 | 0.800 | 32.7 | 44.3 |
| hybrid | normalisé + graphe | 0.820 | 0.925 | 41.3 | 53.8 |

## Questions du critère d'acceptation (MRR)

| Question | Méthode | brut (sem. 2) | normalisé | graphe | normalisé + graphe |
|---|---|---:|---:|---:|---:|
| Q1 | bm25 | 0.00 | 0.20 | 0.00 | 0.20 |
| Q1 | dense | 0.17 | 1.00 | 0.17 | 1.00 |
| Q1 | hybrid | 0.04 | 0.33 | 0.04 | 0.33 |
| Q2 | bm25 | 0.00 | 0.50 | 1.00 | 1.00 |
| Q2 | dense | 0.00 | 0.33 | 1.00 | 1.00 |
| Q2 | hybrid | 0.00 | 0.50 | 1.00 | 1.00 |
| Q3 | bm25 | 0.25 | 0.05 | 1.00 | 1.00 |
| Q3 | dense | 0.00 | 0.01 | 0.50 | 0.17 |
| Q3 | hybrid | 0.06 | 0.03 | 1.00 | 1.00 |
| Q16 | bm25 | 0.00 | 0.02 | 0.50 | 0.50 |
| Q16 | dense | 0.00 | 0.01 | 0.50 | 0.50 |
| Q16 | hybrid | 0.00 | 0.00 | 0.50 | 0.50 |

## Régressions (normalisé + graphe < brut, MRR)

| Question | Méthode | Brut | Enrichi |
|---|---|---:|---:|
| Q10 | bm25 | 0.04 | 0.03 |
