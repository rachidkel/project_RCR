# Rapport Semaine 3 — Pharmeazor

**Date** : 28 novembre 2026  
**Périmètre** : Normalisation d'entités, analyse sémantique de requêtes, graphe de connaissances substances/classes, recherche enrichie, évaluation reproductible et hygiène du dépôt.

---

## 1. Introduction et prise en compte des retours de la Semaine 2

La Semaine 3 a permis de passer d'une recherche purement lexicale/dense sur texte brut à un pipeline structuré autour de trois briques complémentaires : un lexique pharmaceutique unifié (L1), un analyseur de requêtes avec garde-fous (L2) et un graphe de connaissances thérapeutiques (L3), tous branchés sur le moteur de recherche enrichi (L4) et évalués de manière reproductible (L5).

Les corrections demandées par l'enseignant à l'issue de la Semaine 2 ont été intégralement traitées :
1. **Arrêt de la collecte automatisée ANPP** : le collecteur automatisé a été retiré du dépôt ; les 33 RCP existants sont conservés strictement pour l'étude et l'évaluation sans republication.
2. **Évaluation non circulaire de la normalisation** : `scripts/16_eval_independent_names.py` évalue 45 saisies indépendantes (fautes de frappe, langage naturel, hors périmètre) avec un taux de succès de **39/45 (86,7 %)**.
3. **Hit@k et analyse des échecs** : les métriques `MRR@100`, `Hit@10`, `Recall@10` et `nDCG@10` sont rapportées par question et par mode, avec analyse des régressions.

---

## 2. Lexique et alias (Lot L1)

**Auteur** : Anis Fares Hammoudi (`fares`) | **Relecteur** : Rachid Anis Kellil (`review_l1_rachid.md`)  
**Livrables** : `src/pharmeazor/lexicon.py`, `data/processed/week_3/lexicon.json`, `data/processed/week_3/lexicon_coverage.md`, `tests/test_lexicon.py`

- **Volume** : **7 069 alias** et **171 classes** Thésaurus (avec 161 conflits journalisés) indexant les spécialités/marques algériennes (`nomenclature_active.csv`, `produits_enregistres.csv`, `algerian_drug_nomenclature.csv`), les DCI canoniques, les variantes de sels/formes et les classes du Thésaurus (`metadata.membres`).
- **Normalisation** : résolution exacte des synonymes manuels (`Doliprane` $\rightarrow$ `PARACETAMOL`, `aspirine` $\rightarrow$ `ACIDE ACETYLSALICYLIQUE`, `ibuprofène` $\rightarrow$ `AINS`), gestion explicite des ambiguïtés via un journal de conflits (aucun écrasement silencieux).
- **Couverture** : **40/40 (100,0 %)** des molécules du périmètre projet résolues ; 21 tests unitaires passants (`tests/test_lexicon.py`).

---

## 3. Analyse sémantique de requête (Lot L2)

**Auteur** : Mohamed Ali Baghriche (`moh bgh`) | **Détails** : [section_3_query_analysis.md](section_3_query_analysis.md)  
**Livrables** : `src/pharmeazor/query.py`, `scripts/11_analyze_query.py`, `tests/test_query.py`

- **Extraction & résolution** : tokenisation avec conservation des offsets et gestion des élisions françaises (`l'Amlodipine`), fenêtre glissante *longest-match* sur `lexicon.json` et repli flou `rapidfuzz` ($\ge 85\,\%$) protégé par `NON_DRUG_WORDS` pour éviter les faux positifs sur les mots d'intention (ex. `prix`).
- **Intentions & garde-fous** : classification déterministe parmi `dosage`, `interaction`, `contraindication`, `price`, `out_of_scope`, `unknown`.
- **Résultats L2 (23 questions L5)** :
  - **Entity F1** : `0.957` (22/23)
  - **Intent accuracy** : `0.957` (22/23)
  - **Abstention accuracy** : `0.957` (22/23)
  - **Latence** : < 5 ms par requête en moyenne (< 0,25 ms hors chargement initial) ; 17 tests unitaires passants (`tests/test_query.py`).

---

## 4. Graphe de connaissances thérapeutiques (Lot L3)

**Auteur** : Rachid Anis Kellil (`rachid`)  
**Livrables** : `src/pharmeazor/graph.py`, `scripts/17_build_graph.py`, `scripts/19_graph_demo.py`, `data/processed/week_3/knowledge_graph.json`, `tests/test_graph.py`

- **Statistiques du graphe (`kg.stats()`)** :
  - **11 371 nœuds** : `2 069` DCI, `172` classes Thésaurus, `5 911` alias/spécialités, `3 218` interactions, `1` source.
  - **27 881 relations** : `12 314` `member_of`, `6 436` `involves`, `5 913` `alias_of`, `3 218` `documented_in`.
  - **Taux d'orphelins** : **0,41 %** (47 / 11 371, bien en dessous du seuil de 5 %).
- **Exemples de requêtes (`scripts/19_graph_demo.py`)** :
  1. `kg.interactions_for("AMLODIPINE")` : identifie 22 interactions (via les classes *Dihydropyridines*, *Antagonistes des canaux calciques*, *Antihypertenseurs sauf alpha-bloquants* + interaction directe `AMLODIPINE - SIMVASTATINE`).
  2. `kg.interactions_for("IBUPROFENE")` : identifie 46 interactions via *Anti-inflammatoires non stéroïdiens* (dont *Acide acétylsalicylique*).
  3. `kg.explain_absence("AINS", "AMLODIPINE")` : confirme explicitement l'absence d'arête directe AINS $\leftrightarrow$ Amlodipine/CCB et renvoie un avertissement de prudence médicale.

---

## 5. Recherche enrichie (Lot L4)

**Auteur** : Mohamed Seghir Ali Dafri (`moh 117`) | **Relecteur** : Oualid Drici (`review_l4_oualid.md`) | **Détails** : [section_5_enriched_retrieval.md](section_5_enriched_retrieval.md)  
**Livrables** : `src/pharmeazor/retrieval.py`, `src/pharmeazor/enrich.py`, `scripts/20_eval_enriched_retrieval.py`, `tests/test_retrieval_integration.py`

- **Fonctionnement** : rétrocompatible à 100 % en mode `raw` (`normalize=False, expand=False`). En mode enrichi, fusion RRF de trois variantes (brute, DCI canoniques, classes), injection des fiches registre pertinentes, boost par métadonnées (sections ANPP, paires Thésaurus) et expansion par graphe (`graph:direct`, `graph:class`, `graph:related_class`).
- **Gains sur les 40 questions L4** (`data/processed/week_3/l4_enriched_retrieval.md`) :
  - **Hybride brut (S2)** : MRR `0.350`, Hit@10 `0.525`
  - **Hybride normalisé + graphe (S3)** : **MRR `0.820`**, **Hit@10 `0.925`** (37/40 questions dans le top 10).
  - **Cas critiques** : Q2 (`0.00` $\rightarrow$ `1.00`), Q3 (`0.06` $\rightarrow$ `1.00`), Q16 (`0.00` $\rightarrow$ `0.50`).

---

## 6. Évaluation et benchmark reproductible (Lot L5)

**Auteur** : Oualid Drici (`oualid`) | **Détails** : [section_6_evaluation.md](section_6_evaluation.md)  
**Livrables** : `src/pharmeazor/evaluation.py`, `scripts/14_eval_week3.py`, `data/processed/week_3/eval_week3.md`, `tests/test_evaluation.py`

Sur le jeu consolidé de **23 questions** (Q1–Q22 + Q3f, 19 positives avec 52 identifiants gold vérifiés par `scripts/check_gold.py`) :

| Méthode | Mode | MRR@100 | Hit@10 | Recall@10 | nDCG@10 | Latence médiane (ms) |
|---|---|---:|---:|---:|---:|---:|
| BM25 | `raw` | 0.100 | 0.211 | 0.145 | 0.086 | 0.5 |
| BM25 | `normalized` | 0.521 | 0.789 | 0.763 | 0.576 | 4.8 |
| BM25 | `graph` | 0.305 | 0.474 | 0.421 | 0.309 | 0.7 |
| Dense | `raw` | 0.165 | 0.316 | 0.263 | 0.161 | 18.4 |
| Dense | `normalized` | **0.576** | 0.737 | 0.737 | **0.614** | 22.9 |
| Dense | `graph` | 0.384 | 0.632 | 0.579 | 0.408 | 18.6 |
| Hybride | `raw` | 0.242 | 0.316 | 0.316 | 0.255 | 18.6 |
| Hybride | `normalized` | 0.571 | **0.789** | **0.763** | **0.614** | 25.0 |
| Hybride | `graph` | 0.464 | 0.632 | 0.579 | 0.476 | 18.7 |

---

## 7. Analyse d'erreurs (3 cas concrets)

1. **Cas 1 — Faux positif lexical sur question méta (`Q4`)** :
   - *Symptôme* : sur la question méta *"Deux sources donnent une dose différente..."*, `analyze_query` a extrait à tort l'entité `fer` (depuis un mot courant ou segment court) et classé l'intention en `out_of_scope` (`Entity F1 = 0.000`, `Abstention: True` au lieu de `False`).
   - *Cause & correctif* : ajouter une vérification contextuelle/longueur minimale pour les symboles chimiques courts comme `fer` et distinguer les questions méta sur les conflits de sources (`source_conflict`) du hors-périmètre clinique.
2. **Cas 2 — Régression de rang en mode normalisé sur `Q3` sans graphe (`bm25` / `hybrid`)** :
   - *Symptôme* : en mode `normalized` seul, `Q3` (Amlodipine + Ibuprofène) chute de `0.250` à `0.048` en BM25 (`0.037` $\rightarrow$ `0.029` en hybride), alors qu'il atteint **`1.000`** en mode `graph`.
   - *Cause & correctif* : l'expansion de multiples classes par requête sans le filtrage relationnel du graphe dilue les scores BM25 des paires pertinentes ; le routage automatique vers le mode `graph` pour toute requête d'interaction multi-entités corrige cette régression.
3. **Cas 3 — Bruit sur les noms d'entités génériques / dosages (`Q10`, `Q17`)** :
   - *Symptôme* : `Q10` et `Q17` obtiennent un MRR faible (`0.024`–`0.048` en hybride) et l'évaluation indépendante (`16_eval_independent_names.py`) relève 1 erreur silencieuse et 2 non-trouvés sur des fautes de frappe sévères (`39/45 = 86,7 %`).
   - *Cause & correctif* : plusieurs présentations/dosages partagent la même DCI dans les registres ; un reranking fin par dosage extrait et forme galénique sera intégré en Semaine 4.

---

## 8. Tableau final des contributions et état CI

| Membre | Lot assigné | PR / Commits principaux | Livrables & revue | État |
|---|---|---|---|---|
| **Anis Fares Hammoudi** (`fares`) | **L1** — Lexique & alias | PR #4 (`4c6a08c`, `d5ff418`) | `lexicon.py`, `lexicon.json`, `test_lexicon.py`, `lexicon_coverage.md` | Terminé |
| **Mohamed Ali Baghriche** (`moh bgh`) | **L2** — Analyse de requêtes | `eb62404`, `054c9e3`, `434c4dd` | `query.py`, `11_analyze_query.py`, `test_query.py`, `section_3_query_analysis.md` | Terminé |
| **Rachid Anis Kellil** (`rachid`) | **L3** — Graphe de connaissances | `def0dac` + merges PR #4, #6 | `graph.py`, `17_build_graph.py`, `19_graph_demo.py`, `test_graph.py`, revue L1 | Terminé |
| **Mohamed Seghir Ali Dafri** (`moh 117`) | **L4** — Recherche enrichie | PR #5 (`eb0c6db`, `9fbf86a`..`a04a562`) | `retrieval.py`, `enrich.py`, `20_eval_enriched_retrieval.py`, `test_retrieval_integration.py`, `section_5` | Terminé |
| **Oualid Drici** (`oualid`) | **L5** — Évaluation & benchmark | PR #6 (`daf15b9`, `d96126e`..`11807f5`) | `evaluation.py`, `14_eval_week3.py`, `eval_week3.md`, `test_evaluation.py`, `section_6`, revue L4 | Terminé |
| **Anis Ferrah** (`anis fer`) | **L6** — Rapport, intégration & CI | **0 commit / 0 PR** | Aucun livrable soumis par le membre ; rapport final, `.gitignore`, CI (`.github/workflows/ci.yml`) finalisés lors de la vérification finale | Non réalisé par le membre (complété en intégration) |

### Commandes de reproduction

```powershell
.venv\Scripts\python.exe scripts\check_gold.py
.venv\Scripts\python.exe scripts\11_analyze_query.py "Peut-on associer l'Amlodipine et l'Ibuprofène ?"
.venv\Scripts\python.exe scripts\19_graph_demo.py
.venv\Scripts\python.exe scripts\14_eval_week3.py
.venv\Scripts\python.exe -m pytest tests -q
```
