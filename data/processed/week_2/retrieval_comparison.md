# Comparaison BM25 vs recherche sémantique — Semaine 2

Corpus : 7 000 chunks (ANSM Thésaurus, MIPH, EMA, DWA). Top-100 évalué.

## Résultats agrégés (questions réelles Q1, Q2, Q3)

| Méthode | Recall@10 | Recall@50 | Hit@10 | MRR@100 | nDCG@10 |
|---|---|---|---|---|---|
| bm25 | 0.083 | 0.583 | 0.333 | 0.179 | 0.082 |
| dense | 0.333 | 0.667 | 0.333 | 0.103 | 0.144 |
| hybrid | 0.250 | 0.583 | 0.333 | 0.078 | 0.120 |

## Détail par question

| Question | Méthode | Recall@10 | Recall@50 | MRR | nDCG@10 |
|---|---|---|---|---|---|
| Q1 | bm25 | 0.000 | 1.000 | 0.038 | 0.000 |
| Q1 | dense | 1.000 | 1.000 | 0.250 | 0.431 |
| Q1 | hybrid | 0.000 | 1.000 | 0.077 | 0.000 |
| Q2 | bm25 | 0.000 | 0.000 | 0.000 | 0.000 |
| Q2 | dense | 0.000 | 0.500 | 0.025 | 0.000 |
| Q2 | hybrid | 0.000 | 0.000 | 0.014 | 0.000 |
| Q3 | bm25 | 0.250 | 0.750 | 0.500 | 0.246 |
| Q3 | dense | 0.000 | 0.500 | 0.034 | 0.000 |
| Q3 | hybrid | 0.750 | 0.750 | 0.143 | 0.360 |
| Q3f (variante) | bm25 | 0.250 | 1.000 | 0.500 | 0.246 |
| Q3f (variante) | dense | 0.250 | 1.000 | 0.500 | 0.246 |
| Q3f (variante) | hybrid | 0.250 | 1.000 | 1.000 | 0.390 |

*Q3f est une variante diagnostique de Q3 (requête courte et ciblée) : elle n'entre pas dans l'agrégat et sert à isoler l'effet de la formulation.*

## Composition des sources dans le top-10

### Q1

- **bm25** : S_MIPH_NOMENCLATURE (5), S_ANSM_THESAURUS (4), S_DWA (1)
- **dense** : S_MIPH_NOMENCLATURE (9), S_ANSM_THESAURUS (1)
- **hybrid** : S_MIPH_NOMENCLATURE (8), S_ANSM_THESAURUS (2)

### Q2

- **bm25** : S_ANSM_THESAURUS (7), S_MIPH_NOMENCLATURE (3)
- **dense** : S_ANSM_THESAURUS (7), S_MIPH_NOMENCLATURE (3)
- **hybrid** : S_MIPH_NOMENCLATURE (5), S_ANSM_THESAURUS (5)

### Q3

- **bm25** : S_ANSM_THESAURUS (10)
- **dense** : S_ANSM_THESAURUS (10)
- **hybrid** : S_ANSM_THESAURUS (10)

### Q3f

- **bm25** : S_ANSM_THESAURUS (10)
- **dense** : S_ANSM_THESAURUS (10)
- **hybrid** : S_ANSM_THESAURUS (10)

## Requêtes méta / hors périmètre

### Q4 (meta)

> Deux sources donnent une dose maximale différente : que doit répondre le système ?

- **bm25** top-3 : thesaurus:maraviroc:353:2, thesaurus:inhibiteurs puissants du cyp3a4:311:39, thesaurus:maraviroc:353:1
- **dense** top-3 : thesaurus:ciclosporine:124:28, thesaurus:lercanidipine:334:0, thesaurus:ciclosporine:124:13
- **hybrid** top-3 : thesaurus:maraviroc:353:2, thesaurus:acide acetylsalicylique:5:9, thesaurus:tenofovir alafenamide:558:0

### Q5 (negative)

> Quel médicament prendre pour mes douleurs dentaires ?

- **bm25** top-3 : thesaurus:topotecane:577:1, thesaurus:laxatifs type macrogol:330:0, thesaurus:anticholinesterasiques:48:1
- **dense** top-3 : thesaurus:diltiazem:183:9, thesaurus:dronedarone:201:2, nomenclature:mepivacaine hydrochloride
- **hybrid** top-3 : thesaurus:anticholinesterasiques:48:1, thesaurus:diltiazem:183:9, thesaurus:topotecane:577:1
