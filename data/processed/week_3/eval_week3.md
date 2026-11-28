# Évaluation de la semaine 3 — L5

## Protocole

- **23 questions** : Q1–Q22 et la variante Q3f ; 19 positives avec passage gold.
- **Modes** : `raw` (recherche semaine 2 inchangée), `normalized` (variantes DCI/classes + boost métadonnées), `graph` (expansion L3), `normalized+graph` (les deux, mode recommandé par L4).
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
| bm25 | raw | 0.100 | 0.211 | 0.145 | 0.086 | 0.7 | 0.9 |
| bm25 | normalized | 0.518 | 0.789 | 0.763 | 0.574 | 6.9 | 9.4 |
| bm25 | graph | 0.305 | 0.474 | 0.421 | 0.309 | 1.0 | 1.5 |
| bm25 | normalized+graph | 0.628 | 0.895 | 0.868 | 0.671 | 7.2 | 9.7 |
| dense | raw | 0.165 | 0.316 | 0.263 | 0.161 | 32.3 | 40.6 |
| dense | normalized | 0.576 | 0.737 | 0.737 | 0.614 | 38.9 | 55.7 |
| dense | graph | 0.384 | 0.632 | 0.579 | 0.408 | 31.1 | 34.0 |
| dense | normalized+graph | 0.670 | 0.895 | 0.855 | 0.700 | 38.7 | 43.3 |
| hybrid | raw | 0.242 | 0.316 | 0.316 | 0.255 | 31.1 | 33.5 |
| hybrid | normalized | 0.571 | 0.789 | 0.763 | 0.614 | 39.0 | 44.0 |
| hybrid | graph | 0.461 | 0.632 | 0.579 | 0.475 | 31.7 | 37.5 |
| hybrid | normalized+graph | 0.679 | 0.895 | 0.868 | 0.704 | 39.6 | 44.2 |

## Analyse des requêtes (L2)

| Métrique | Valeur |
|---|---:|
| Entity F1 | 0.957 |
| Intent accuracy | 0.957 |
| Abstention accuracy | 0.957 |

Entity F1 compare les DCI prédites (et les classes seules quand la question ne cite pas de DCI) aux entités attendues. L'abstention compare `analyze_query(...).out_of_scope` à l'attente de refus.

## Détail par question (MRR)

### bm25

| Question | Type | raw | normalized | graph | normalized+graph |
|---|---|---:|---:|---:|---:|
| Q1 | positive | 0.000 | 0.200 | 0.000 | 0.200 |
| Q2 | positive | 0.000 | 0.500 | 1.000 | 1.000 |
| Q3 | positive | 0.250 | 0.048 | 1.000 | 1.000 |
| Q6 | positive | 0.000 | 0.500 | 0.000 | 0.500 |
| Q7 | positive | 0.083 | 1.000 | 0.083 | 1.000 |
| Q8 | positive | 0.050 | 1.000 | 0.500 | 1.000 |
| Q9 | positive | 0.000 | 0.500 | 0.000 | 0.500 |
| Q10 | positive | 0.042 | 0.032 | 0.042 | 0.032 |
| Q11 | positive | 0.033 | 1.000 | 0.033 | 1.000 |
| Q12 | positive | 0.062 | 0.100 | 0.250 | 0.250 |
| Q13 | positive | 0.000 | 0.167 | 0.000 | 0.167 |
| Q14 | positive | 0.143 | 1.000 | 0.143 | 1.000 |
| Q15 | positive | 0.111 | 1.000 | 0.111 | 1.000 |
| Q16 | positive | 0.000 | 0.015 | 0.500 | 0.500 |
| Q17 | positive | 0.038 | 0.034 | 0.048 | 0.042 |
| Q18 | positive | 0.091 | 0.500 | 0.091 | 0.500 |
| Q19 | positive | 0.000 | 1.000 | 1.000 | 1.000 |
| Q20 | positive | 0.000 | 0.250 | 0.000 | 0.250 |
| Q22 | positive | 1.000 | 1.000 | 1.000 | 1.000 |
### dense

| Question | Type | raw | normalized | graph | normalized+graph |
|---|---|---:|---:|---:|---:|
| Q1 | positive | 0.167 | 1.000 | 0.167 | 1.000 |
| Q2 | positive | 0.000 | 0.333 | 1.000 | 1.000 |
| Q3 | positive | 0.000 | 0.010 | 0.500 | 0.167 |
| Q6 | positive | 0.038 | 0.500 | 0.038 | 0.500 |
| Q7 | positive | 0.200 | 1.000 | 0.200 | 1.000 |
| Q8 | positive | 0.000 | 1.000 | 1.000 | 1.000 |
| Q9 | positive | 0.083 | 0.500 | 0.083 | 0.500 |
| Q10 | positive | 0.016 | 0.016 | 0.000 | 0.016 |
| Q11 | positive | 0.200 | 0.500 | 0.200 | 0.500 |
| Q12 | positive | 0.000 | 0.067 | 0.125 | 0.500 |
| Q13 | positive | 0.071 | 1.000 | 0.071 | 1.000 |
| Q14 | positive | 1.000 | 1.000 | 1.000 | 1.000 |
| Q15 | positive | 0.250 | 1.000 | 0.250 | 1.000 |
| Q16 | positive | 0.000 | 0.011 | 0.500 | 0.500 |
| Q17 | positive | 0.000 | 0.013 | 0.067 | 0.050 |
| Q18 | positive | 0.056 | 0.500 | 0.056 | 0.500 |
| Q19 | positive | 0.000 | 1.000 | 1.000 | 1.000 |
| Q20 | positive | 0.048 | 0.500 | 0.048 | 0.500 |
| Q22 | positive | 1.000 | 1.000 | 1.000 | 1.000 |
### hybrid

| Question | Type | raw | normalized | graph | normalized+graph |
|---|---|---:|---:|---:|---:|
| Q1 | positive | 0.019 | 0.333 | 0.038 | 0.333 |
| Q2 | positive | 0.000 | 0.500 | 1.000 | 1.000 |
| Q3 | positive | 0.037 | 0.029 | 1.000 | 1.000 |
| Q6 | positive | 0.017 | 0.333 | 0.020 | 0.333 |
| Q7 | positive | 0.500 | 1.000 | 0.500 | 1.000 |
| Q8 | positive | 0.016 | 1.000 | 0.500 | 1.000 |
| Q9 | positive | 0.024 | 0.500 | 0.034 | 0.500 |
| Q10 | positive | 0.042 | 0.029 | 0.024 | 0.029 |
| Q11 | positive | 1.000 | 1.000 | 1.000 | 1.000 |
| Q12 | positive | 0.030 | 0.100 | 0.200 | 0.167 |
| Q13 | positive | 0.037 | 1.000 | 0.037 | 1.000 |
| Q14 | positive | 0.333 | 1.000 | 0.333 | 1.000 |
| Q15 | positive | 1.000 | 1.000 | 1.000 | 1.000 |
| Q16 | positive | 0.000 | 0.000 | 0.500 | 0.500 |
| Q17 | positive | 0.016 | 0.023 | 0.048 | 0.042 |
| Q18 | positive | 0.500 | 0.500 | 0.500 | 0.500 |
| Q19 | positive | 0.000 | 1.000 | 1.000 | 1.000 |
| Q20 | positive | 0.024 | 0.500 | 0.024 | 0.500 |
| Q22 | positive | 1.000 | 1.000 | 1.000 | 1.000 |

## Régressions du mode enrichi

| Question | Méthode | Mode | Raw | Enrichi |
|---|---|---|---:|---:|
| Q3 | bm25 | normalized | 0.250 | 0.048 |
| Q10 | bm25 | normalized | 0.042 | 0.032 |
| Q10 | bm25 | normalized+graph | 0.042 | 0.032 |
| Q17 | bm25 | normalized | 0.038 | 0.034 |
| Q10 | dense | graph | 0.016 | 0.000 |
| Q3 | hybrid | normalized | 0.037 | 0.029 |
| Q10 | hybrid | normalized | 0.042 | 0.029 |
| Q10 | hybrid | graph | 0.042 | 0.024 |
| Q10 | hybrid | normalized+graph | 0.042 | 0.029 |

## Jeu tenu à l'écart (10 questions non vues par le réglage)

Les questions H01–H10 (`scripts/21_build_heldout.py`) portent sur des médicaments et des paires absents des questions utilisées pour régler L4. Elles ont été écrites avant leur première évaluation, et les poids de L4 n'ont pas été modifiés depuis. Un gold a été corrigé après la première exécution (H06 : l'entrée directe fluoxétine + tramadol, plus grave, manquait) ; la correction est notée dans le fichier. Les paires du Thésaurus comptent les deux sens.

Poids de L4 inchangés depuis la création du jeu (empreinte de `enrich.py` : `929badcfdcda`).

| Méthode | Mode | MRR@100 | Hit@10 |
|---|---|---:|---:|
| bm25 | raw | 0.505 | 0.700 |
| bm25 | normalized | 0.764 | 1.000 |
| bm25 | graph | 0.605 | 0.800 |
| bm25 | normalized+graph | 0.848 | 1.000 |
| dense | raw | 0.203 | 0.400 |
| dense | normalized | 0.698 | 0.900 |
| dense | graph | 0.637 | 0.900 |
| dense | normalized+graph | 0.835 | 0.900 |
| hybrid | raw | 0.230 | 0.500 |
| hybrid | normalized | 0.764 | 1.000 |
| hybrid | graph | 0.673 | 1.000 |
| hybrid | normalized+graph | 0.848 | 1.000 |

### Détail par question — bm25 (MRR)

| Question | Catégorie | Énoncé | raw | normalized | graph | normalized+graph |
|---|---|---|---:|---:|---:|---:|
| H01 | direct | Quelles marques de losartan sont enregistrées en Algérie ? | 0.053 | 1.000 | 0.053 | 1.000 |
| H02 | direct | Quelle est la DCI du médicament COVERSYL ? | 0.333 | 1.000 | 0.333 | 1.000 |
| H03 | direct | Quelle est la posologie du BIODAZOLE selon son RCP ? | 0.125 | 1.000 | 0.125 | 1.000 |
| H04 | direct | Quelles sont les contre-indications du CEBREX selon son RCP ? | 0.036 | 0.333 | 0.036 | 0.333 |
| H05 | cross | Peut-on associer la doxycycline et des sels de fer ? | 1.000 | 1.000 | 1.000 | 1.000 |
| H06 | cross | Peut-on associer le tramadol et la fluoxétine ? | 1.000 | 1.000 | 1.000 | 1.000 |
| H07 | cross | Peut-on associer le diclofénac et le losartan ? | 0.000 | 0.167 | 1.000 | 1.000 |
| H08 | cross | Le méthotrexate peut-il être pris avec du kétoprofène ? | 1.000 | 1.000 | 1.000 | 1.000 |
| H09 | cross | Peut-on donner des sels de potassium à un patient sous amiloride ? | 1.000 | 0.143 | 1.000 | 0.143 |
| H10 | cross | Quelle précaution pour l'association nébivolol et amiodarone ? | 0.500 | 1.000 | 0.500 | 1.000 |

### Détail par question — dense (MRR)

| Question | Catégorie | Énoncé | raw | normalized | graph | normalized+graph |
|---|---|---|---:|---:|---:|---:|
| H01 | direct | Quelles marques de losartan sont enregistrées en Algérie ? | 0.500 | 1.000 | 0.500 | 1.000 |
| H02 | direct | Quelle est la DCI du médicament COVERSYL ? | 1.000 | 1.000 | 1.000 | 1.000 |
| H03 | direct | Quelle est la posologie du BIODAZOLE selon son RCP ? | 0.200 | 1.000 | 0.200 | 1.000 |
| H04 | direct | Quelles sont les contre-indications du CEBREX selon son RCP ? | 0.333 | 0.333 | 0.333 | 0.333 |
| H05 | cross | Peut-on associer la doxycycline et des sels de fer ? | 0.000 | 1.000 | 1.000 | 1.000 |
| H06 | cross | Peut-on associer le tramadol et la fluoxétine ? | 0.000 | 1.000 | 1.000 | 1.000 |
| H07 | cross | Peut-on associer le diclofénac et le losartan ? | 0.000 | 0.125 | 1.000 | 1.000 |
| H08 | cross | Le méthotrexate peut-il être pris avec du kétoprofène ? | 0.000 | 0.500 | 1.000 | 1.000 |
| H09 | cross | Peut-on donner des sels de potassium à un patient sous amiloride ? | 0.000 | 0.017 | 0.000 | 0.017 |
| H10 | cross | Quelle précaution pour l'association nébivolol et amiodarone ? | 0.000 | 1.000 | 0.333 | 1.000 |

### Détail par question — hybrid (MRR)

| Question | Catégorie | Énoncé | raw | normalized | graph | normalized+graph |
|---|---|---|---:|---:|---:|---:|
| H01 | direct | Quelles marques de losartan sont enregistrées en Algérie ? | 0.500 | 1.000 | 0.500 | 1.000 |
| H02 | direct | Quelle est la DCI du médicament COVERSYL ? | 1.000 | 1.000 | 1.000 | 1.000 |
| H03 | direct | Quelle est la posologie du BIODAZOLE selon son RCP ? | 0.250 | 1.000 | 0.250 | 1.000 |
| H04 | direct | Quelles sont les contre-indications du CEBREX selon son RCP ? | 0.143 | 0.333 | 0.143 | 0.333 |
| H05 | cross | Peut-on associer la doxycycline et des sels de fer ? | 0.056 | 1.000 | 1.000 | 1.000 |
| H06 | cross | Peut-on associer le tramadol et la fluoxétine ? | 0.031 | 1.000 | 1.000 | 1.000 |
| H07 | cross | Peut-on associer le diclofénac et le losartan ? | 0.000 | 0.167 | 1.000 | 1.000 |
| H08 | cross | Le méthotrexate peut-il être pris avec du kétoprofène ? | 0.067 | 1.000 | 1.000 | 1.000 |
| H09 | cross | Peut-on donner des sels de potassium à un patient sous amiloride ? | 0.091 | 0.143 | 0.333 | 0.143 |
| H10 | cross | Quelle précaution pour l'association nébivolol et amiodarone ? | 0.167 | 1.000 | 0.500 | 1.000 |

### Questions qui se dégradent (MRR enrichi < brut)

| Question | Méthode | Mode | Brut | Enrichi |
|---|---|---|---:|---:|
| H09 | bm25 | normalized | 1.000 | 0.143 |
| H09 | bm25 | normalized+graph | 1.000 | 0.143 |

## Pourquoi deux chiffres (0,820 et 0,571)

Les deux chiffres publiés en semaine 3 ne mesuraient pas la même chose : 0,820 (section 5) était le mode `normalized+graph` sur les 40 questions de réglage de L4 ; 0,571 (section 6) était le mode `normalized` seul sur les questions de L5. Le tableau les recalcule ici, dans la même exécution.

| Méthode | Jeu de questions | n | normalized | normalized+graph |
|---|---|---:|---:|---:|
| bm25 | 40 questions de réglage L4 (section 5) | 40 | 0.671 | 0.773 |
| bm25 | questions L5, Q1–Q22 (section 6) | 19 | 0.518 | 0.628 |
| bm25 | 10 questions tenues à l'écart | 10 | 0.764 | 0.848 |
| dense | 40 questions de réglage L4 (section 5) | 40 | 0.693 | 0.785 |
| dense | questions L5, Q1–Q22 (section 6) | 19 | 0.576 | 0.670 |
| dense | 10 questions tenues à l'écart | 10 | 0.698 | 0.835 |
| hybrid | 40 questions de réglage L4 (section 5) | 40 | 0.719 | 0.820 |
| hybrid | questions L5, Q1–Q22 (section 6) | 19 | 0.571 | 0.679 |
| hybrid | 10 questions tenues à l'écart | 10 | 0.764 | 0.848 |

Lecture : sur un même jeu, l'écart entre les deux colonnes vient du mode ; sur une même colonne, l'écart entre les lignes vient des questions. Seule la ligne « tenu à l'écart » porte sur des questions qui n'ont pas servi au réglage (10 questions : un ordre de grandeur, pas une preuve).

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
