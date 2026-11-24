# Revue de Code — Lot L1 (Lexique & Alias)
**Auteur du Lot L1** : Anis Fares HAMMOUDI (fares)  
**Relecteur assigné** : Mohamed Ali BAGHRICHE (moh bgh)  
**Date de relecture** : 24 novembre 2026  
**Branche examinée** : `origin/l1-lexicon` (commit `d5ff418`)  
**Statut de la revue** : ✅ **APPROUVÉ (LGTM)**

---

## 1. Périmètre et livrables vérifiés
- [x] Fichier JSON du lexique unifié : `data/processed/week_3/lexicon.json` (60 561 lignes, version 1).
- [x] Module d'accès au lexique : `src/pharmeazor/lexicon.py` (291 lignes).
- [x] Script de génération reproductible : `scripts/18_build_lexicon.py`.
- [x] Suite de tests unitaires : `tests/test_lexicon.py` (21 tests).
- [x] Rapport de couverture : `data/processed/week_3/lexicon_coverage.md`.

---

## 2. Vérification des critères d'acceptation (Acceptance Criteria)

| Critère d'acceptation | Attendu | Résultat obtenu | Statut |
|---|---|---|:---:|
| **Régression Semaine 2** | 42/42 variantes de noms de médicaments de S2 restent vertes | 42/42 validées dans `test_regression_week2_variants_unchanged` | ✅ Conforme |
| **Couverture des 40 molécules** | $\ge 95\%$ des 40 molécules du projet résolues sans ambiguïté | **100 % (40/40)** résolues dans `test_at_least_95_percent_of_the_40_drugs_resolved` | ✅ Conforme |
| **Résolution des marques clés** | `Doliprane` $\rightarrow$ `PARACETAMOL`, `Efferalgan` $\rightarrow$ `PARACETAMOL`, `Augmentin` $\rightarrow$ `AMOXICILLINE + ACIDE CLAVULANIQUE` | Exactement résolu avec confiance $\ge 0.98$ | ✅ Conforme |
| **Synonymes manuels & classes** | `aspirine` $\rightarrow$ `ACIDE ACETYLSALICYLIQUE`, `ibuprofène` rattaché aux `AINS` | `resolve("aspirine")` donne `ACIDE ACETYLSALICYLIQUE`, `resolve("ibuprofène").classes` contient `ANTI-INFLAMMATOIRES NON STEROIDIENS` | ✅ Conforme |
| **Gestion des ambiguïtés** | Les marques multi-DCI ne sont jamais écrasées silencieusement | `candidates` répertoriés avec `dci=None` et `ambiguous=True` (ex. Dafalgan seul) | ✅ Conforme |
| **Gestion des coquilles sources** | Normalisation des coquilles de nomenclature (`ACIDE ACETYLSALICYTIQUE`, `PROPANOLOL`) | 11 corrections documentées dans `DCI_TYPO_FIXES` sans altération des paires distinctes | ✅ Conforme |

---

## 3. Résultats d'exécution des tests
```powershell
.venv\Scripts\pytest tests/test_lexicon.py -v
# 21 passed in 1.01s
```

---

## 4. Remarques techniques et intégration avec L2 (Query Analysis)
1. **Performance** : `resolve()` s'exécute en **0,015 ms** grâce au chargement mémoire mis en cache (`lru_cache`). C'est optimal pour l'objectif de latence globale de L2 (< 5 ms).
2. **Cohérence des classes** : La séparation nette entre l'aspirine (qui n'est pas forcée dans les AINS dans le Thésaurus relationnel brut) et la classe d'interaction est respectée. Le lot L2 prend en charge l'expansion sémantique antalgique/AINS au niveau de l'analyse de requête.
3. **Validation pour merge** : La PR L1 est propre, respecte les types et passe l'ensemble des tests. Prêt pour le merge sur `main`.
