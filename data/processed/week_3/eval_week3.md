# Évaluation de la semaine 3 — L5

## Protocole

- **23 questions** : Q1–Q22 et la variante Q3f ; 19 positives avec passage gold.
- **Modes** : `raw` (recherche semaine 2 inchangée), `normalized` (variantes DCI/classes + boost métadonnées), `graph` (expansion L3).
- **Méthodes** : bm25, dense, hybrid.
- **Profondeur** : top-100 ; MRR plafonné à 100.
- **Gold** : identifiants vérifiés dans `corpus.jsonl` par ce script.

> Les poids de la recherche enrichie (L4) ont été réglés sur ces mêmes questions : les gains sont optimistes. Le but ici est la comparaison avant/après et la couverture des métriques, pas une estimation non biaisée.

## Questions ajoutées pour L5

| ID | Type | Question | Attendu |
|---|---|---|---|
| Q18 | positive | Le DOLIPRANE est-il disponible en plusieurs dosages en Algérie ? | PARACETAMOL |
| Q19 | positive | Peut-on associer un AINS avec un IEC ? | ANTI-INFLAMMATOIRES NON STEROIDIENS, INHIBITEURS DE L ENZYME DE CONVERSION |
| Q20 | positive | Quel est le dosage du paracétamole en Algérie ? | PARACETAMOL |
| Q21 | negative | Quel médicament prendre pour une angine ? | abstention |
| Q22 | positive | Quelles marques de ramipril sont enregistrées en Algérie ? | RAMIPRIL |

## Validation du gold

Tous les identifiants gold (40) existent dans le corpus, et toutes les questions ont leurs métadonnées d'analyse.

## Avant / après (retrieval)

| Méthode | Mode | MRR@100 | Hit@10 | Recall@10 | nDCG@10 | Latence médiane (ms) | Latence p95 (ms) |
|---|---|---:|---:|---:|---:|---:|---:|
| bm25 | raw | 0.100 | 0.211 | 0.145 | 0.086 | 0.5 | 0.7 |
| bm25 | normalized | 0.521 | 0.789 | 0.763 | 0.576 | 4.8 | 7.5 |
| bm25 | graph | 0.305 | 0.474 | 0.421 | 0.309 | 0.7 | 1.5 |
| dense | raw | 0.165 | 0.316 | 0.263 | 0.161 | 18.4 | 20.8 |
| dense | normalized | 0.576 | 0.737 | 0.737 | 0.614 | 22.9 | 27.3 |
| dense | graph | 0.384 | 0.632 | 0.579 | 0.408 | 18.6 | 32.9 |
| hybrid | raw | 0.242 | 0.316 | 0.316 | 0.255 | 18.6 | 21.4 |
| hybrid | normalized | 0.571 | 0.789 | 0.763 | 0.614 | 25.0 | 28.0 |
| hybrid | graph | 0.464 | 0.632 | 0.579 | 0.476 | 18.7 | 20.1 |

## Analyse des requêtes (L2)

| Métrique | Valeur |
|---|---:|
| Entity F1 | 0.957 |
| Intent accuracy | 0.957 |
| Abstention accuracy | 0.957 |

Entity F1 compare les DCI prédites (et les classes seules quand la question ne cite pas de DCI) aux entités attendues. L'abstention compare `analyze_query(...).out_of_scope` à l'attente de refus.

## Détail par question (MRR)

### bm25

| Question | Type | Raw | Normalized | Graph |
|---|---|---:|---:|---:|
| Q1 | positive | 0.000 | 0.200 | 0.000 |
| Q2 | positive | 0.000 | 0.500 | 1.000 |
| Q3 | positive | 0.250 | 0.048 | 1.000 |
| Q6 | positive | 0.000 | 0.500 | 0.000 |
| Q7 | positive | 0.083 | 1.000 | 0.083 |
| Q8 | positive | 0.050 | 1.000 | 0.500 |
| Q9 | positive | 0.000 | 0.500 | 0.000 |
| Q10 | positive | 0.042 | 0.032 | 0.042 |
| Q11 | positive | 0.033 | 1.000 | 0.033 |
| Q12 | positive | 0.067 | 0.111 | 0.250 |
| Q13 | positive | 0.000 | 0.200 | 0.000 |
| Q14 | positive | 0.143 | 1.000 | 0.143 |
| Q15 | positive | 0.111 | 1.000 | 0.111 |
| Q16 | positive | 0.000 | 0.015 | 0.500 |
| Q17 | positive | 0.038 | 0.034 | 0.048 |
| Q18 | positive | 0.091 | 0.500 | 0.091 |
| Q19 | positive | 0.000 | 1.000 | 1.000 |
| Q20 | positive | 0.000 | 0.250 | 0.000 |
| Q22 | positive | 1.000 | 1.000 | 1.000 |
### dense

| Question | Type | Raw | Normalized | Graph |
|---|---|---:|---:|---:|
| Q1 | positive | 0.167 | 1.000 | 0.167 |
| Q2 | positive | 0.000 | 0.333 | 1.000 |
| Q3 | positive | 0.000 | 0.010 | 0.500 |
| Q6 | positive | 0.038 | 0.500 | 0.038 |
| Q7 | positive | 0.200 | 1.000 | 0.200 |
| Q8 | positive | 0.000 | 1.000 | 1.000 |
| Q9 | positive | 0.083 | 0.500 | 0.083 |
| Q10 | positive | 0.016 | 0.017 | 0.000 |
| Q11 | positive | 0.200 | 0.500 | 0.200 |
| Q12 | positive | 0.000 | 0.067 | 0.125 |
| Q13 | positive | 0.071 | 1.000 | 0.071 |
| Q14 | positive | 1.000 | 1.000 | 1.000 |
| Q15 | positive | 0.250 | 1.000 | 0.250 |
| Q16 | positive | 0.000 | 0.011 | 0.500 |
| Q17 | positive | 0.000 | 0.013 | 0.067 |
| Q18 | positive | 0.056 | 0.500 | 0.056 |
| Q19 | positive | 0.000 | 1.000 | 1.000 |
| Q20 | positive | 0.048 | 0.500 | 0.048 |
| Q22 | positive | 1.000 | 1.000 | 1.000 |
### hybrid

| Question | Type | Raw | Normalized | Graph |
|---|---|---:|---:|---:|
| Q1 | positive | 0.019 | 0.333 | 0.038 |
| Q2 | positive | 0.000 | 0.500 | 1.000 |
| Q3 | positive | 0.037 | 0.029 | 1.000 |
| Q6 | positive | 0.017 | 0.333 | 0.020 |
| Q7 | positive | 0.500 | 1.000 | 0.500 |
| Q8 | positive | 0.016 | 1.000 | 0.500 |
| Q9 | positive | 0.024 | 0.500 | 0.034 |
| Q10 | positive | 0.042 | 0.029 | 0.024 |
| Q11 | positive | 1.000 | 1.000 | 1.000 |
| Q12 | positive | 0.032 | 0.111 | 0.250 |
| Q13 | positive | 0.037 | 1.000 | 0.037 |
| Q14 | positive | 0.333 | 1.000 | 0.333 |
| Q15 | positive | 1.000 | 1.000 | 1.000 |
| Q16 | positive | 0.000 | 0.000 | 0.500 |
| Q17 | positive | 0.016 | 0.023 | 0.048 |
| Q18 | positive | 0.500 | 0.500 | 0.500 |
| Q19 | positive | 0.000 | 1.000 | 1.000 |
| Q20 | positive | 0.024 | 0.500 | 0.024 |
| Q22 | positive | 1.000 | 1.000 | 1.000 |

## Régressions du mode enrichi

| Question | Méthode | Mode | Raw | Enrichi |
|---|---|---|---:|---:|
| Q3 | bm25 | normalized | 0.250 | 0.048 |
| Q10 | bm25 | normalized | 0.042 | 0.032 |
| Q17 | bm25 | normalized | 0.038 | 0.034 |
| Q10 | dense | graph | 0.016 | 0.000 |
| Q3 | hybrid | normalized | 0.037 | 0.029 |
| Q10 | hybrid | normalized | 0.042 | 0.029 |
| Q10 | hybrid | graph | 0.042 | 0.024 |

## Erreurs d'analyse (cas concrets)

| Question | Entity F1 | Intention (prévu / attendu) | Abstention (prévu / attendu) | Entités (prévu / attendu) |
|---|---:|---|---|---|
| Q4 | 0.000 | out_of_scope / unknown | True / False | fer / — |

## Reproduction

```powershell
.venv\Scripts\python.exe scripts\14_eval_week3.py
.venv\Scripts\python.exe scripts\14_eval_week3.py --bm25-only
.venv\Scripts\python.exe -m pytest tests -q
```

Fichier généré : `data/processed/week_3/eval_week3.md`.
