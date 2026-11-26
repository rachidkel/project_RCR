# Revue de Code — Lot L4 (Recherche enrichie)

**Auteur du lot L4** : moh 117
**Relecteur assigné** : oualid
**Date de relecture** : 26 novembre 2026
**Branche examinée** : `origin/l4-retrieval` (commit `a04a562`, fusionnée par la PR #5 / `eb0c6db`)
**Statut de la revue** : ✅ **APPROUVÉ**, avec réserves mineures non bloquantes

---

## 1. Périmètre et livrables vérifiés

- [x] `src/pharmeazor/retrieval.py` : `search(query, k, method, normalize, expand, graph, return_trace)` sans casser le mode brut.
- [x] `src/pharmeazor/enrich.py` : variantes de requête, RRF, boost métadonnées, `GraphExpander`.
- [x] `tests/test_retrieval_integration.py` : reproductibilité brute, requête vide, absence amlodipine + AINS, latence, `split_long_chunks`.
- [x] `scripts/20_eval_enriched_retrieval.py` : comparaison brut / normalisé / graphe + latence.
- [x] `data/processed/week_3/l4_enriched_retrieval.md` et `docs/week_3/section_5_enriched_retrieval.md`.

## 2. Critères d'acceptation

| Critère du plan | Attendu | Vérification | Statut |
|---|---|---|---|
| Mode brut reproductible | Mêmes classements que la semaine 2 | `test_raw_mode_reproduces_week2` passe ; `search()` sans options ne renvoie pas de champ `signals` | ✅ |
| Normalisé améliore Q2/Q16 sans casser Q1/Q3 | Gains sur les interactions, pas de régression | Rapport L4 : Q1 0,04→0,33 ; Q2 0,00→1,00 ; Q3 0,06→1,00 ; Q16 0,00→0,50 (hybride, normalisé + graphe) | ✅ |
| Latence < 50 ms CPU | Médiane sous 50 ms | Médiane 41 ms ; p95 54 ms (au-dessus uniquement à cause de l'encodage de la question, ~31 ms) | ✅ (médiane) |
| `corpus.split_long_chunks` intact | Aucun changement | `test_split_long_chunks_still_works` passe | ✅ |
| Chaque résultat enrichi s'explique | Champ `signals` non vide | `test_every_enriched_result_explains_itself` passe | ✅ |
| Absence expliquée, pas inventée | Amlodipine + AINS sans arête directe | `test_graph_absence_uses_related_classes_and_says_so` passe ; preuves `related_class` uniquement | ✅ |

## 3. Exécution des tests

```powershell
.venv\Scripts\python.exe scripts\08_build_index.py   # index local à jour
.venv\Scripts\python.exe -m pytest tests -q
# 65 passed
```

Les 65 tests de la suite passent sur un index reconstruit. Les tests L4 se
dégradent correctement en `skip` quand l'index BM25/FAISS est absent.

## 4. Remarques techniques

1. **Garde de `skip` incomplète (corrigée dans la branche L5).**
   `HAS_FAISS = (INDEX_DIR / "faiss.index").exists()` ne vérifiait que l'index
   FAISS. `load_faiss()` lit aussi `faiss_chunk_ids.json` ; sur un index
   partiel, les tests échouaient au lieu d'être ignorés. La garde vérifie
   désormais les deux fichiers (`faiss.index` **et** `faiss_chunk_ids.json`),
   ainsi que `bm25/` + `bm25_chunk_ids.json`. Rencontré en pratique sur ce
   poste avec un index de semaine 2 incomplet.

2. **`requirements.txt` collait deux paquets.** La ligne
   `bm25s==0.3.16pytest==9.2.0` empêchait `pip install -r requirements.txt`
   d'installer pytest. Corrigé dans la branche L5 (deux lignes distinctes) :
   c'est une correction de dette, pas une réécriture du lot L4.

3. **Interactions non mappées silencieuses.** `GraphExpander.unmapped` vaut 4
   sur 3 218 interactions mais n'apparaît pas dans la trace. Exposer ce compteur
   dans `trace["graph"]` rendrait la couverture du graphe vérifiable.

4. **Boost `anpp_product` sans garde d'intention.** Le boost de marque n'est pas
   protégé par `wants_registry()`. Sur une question d'interaction citant une
   marque, un RCP de produit peut être remonté pour une raison d'identité.
   Faible impact (les sections demandées restent filtrées), mais ajouter la
   garde serait plus sûr.

5. **`search()` change de type de retour avec `return_trace`.** Liste ou
   `(liste, trace)`. C'est documenté, mais un petit dataclass de résultat
   éviterait aux appelants de tester le type.

6. **`is_out_of_scope` reste l'ancienne implémentation.** Le mode enrichi utilise
   `analyze_query` (L2), mais `is_out_of_scope` conserve ses propres motifs. À
   terme, le faire déléguer à L2 pour une seule source de vérité.

## 5. Verdict

Le lot L4 remplit ses critères : mode brut intact, gains nets sur les questions
d'interaction, preuves traçables, latence médiane conforme, absence explicitée.
Les remarques 1 et 2 sont des corrections d'outillage (dont la seconde est déjà
traitée côté L5) ; les remarques 3 à 6 sont des améliorations à planifier, sans
remettre en cause la fusion.

**Revue : approuvée.**
