# Comparaison BM25 vs recherche sémantique — Semaine 2

Corpus : 9 546 chunks — S_ANSM_THESAURUS (3 218), S_EMA (2 365), S_MIPH_NOMENCLATURE (1 387), S_DZ_NOMENCLATURE (1 299), S_PHARMNET (1 247), S_DWA (30). Top-100 évalué.

## Résultats agrégés (questions réelles Q1, Q2, Q3)

| Méthode | Recall@10 | Recall@50 | Hit@10 | MRR@100 | nDCG@10 |
|---|---|---|---|---|---|
| bm25 | 0.083 | 0.250 | 0.333 | 0.333 | 0.130 |
| dense | 0.333 | 0.500 | 0.333 | 0.085 | 0.129 |
| hybrid | 0.167 | 0.250 | 0.333 | 0.058 | 0.084 |

## Détail par question

| Question | Méthode | Recall@10 | Recall@50 | MRR | nDCG@10 |
|---|---|---|---|---|---|
| Q1 | bm25 | 0.000 | 0.000 | 0.000 | 0.000 |
| Q1 | dense | 1.000 | 1.000 | 0.200 | 0.387 |
| Q1 | hybrid | 0.000 | 0.000 | 0.019 | 0.000 |
| Q2 | bm25 | 0.000 | 0.000 | 0.000 | 0.000 |
| Q2 | dense | 0.000 | 0.000 | 0.020 | 0.000 |
| Q2 | hybrid | 0.000 | 0.000 | 0.012 | 0.000 |
| Q3 | bm25 | 0.250 | 0.750 | 1.000 | 0.390 |
| Q3 | dense | 0.000 | 0.500 | 0.034 | 0.000 |
| Q3 | hybrid | 0.500 | 0.750 | 0.143 | 0.253 |
| Q3f (variante) | bm25 | 0.250 | 1.000 | 0.500 | 0.246 |
| Q3f (variante) | dense | 0.250 | 1.000 | 0.500 | 0.246 |
| Q3f (variante) | hybrid | 0.250 | 1.000 | 1.000 | 0.390 |

*Q3f est une variante diagnostique de Q3 (requête courte et ciblée) : elle n'entre pas dans l'agrégat et sert à isoler l'effet de la formulation.*

## Composition des sources dans le top-10

### Q1

- **bm25** : S_MIPH_NOMENCLATURE (3), S_ANSM_THESAURUS (2), S_PHARMNET (2), S_DZ_NOMENCLATURE (2), S_DWA (1)
- **dense** : S_MIPH_NOMENCLATURE (6), S_PHARMNET (4)
- **hybrid** : S_MIPH_NOMENCLATURE (5), S_PHARMNET (2), S_ANSM_THESAURUS (2), S_DZ_NOMENCLATURE (1)

### Q2

- **bm25** : S_ANSM_THESAURUS (8), S_MIPH_NOMENCLATURE (1), S_DZ_NOMENCLATURE (1)
- **dense** : S_PHARMNET (5), S_ANSM_THESAURUS (3), S_MIPH_NOMENCLATURE (2)
- **hybrid** : S_PHARMNET (6), S_MIPH_NOMENCLATURE (4)

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
- **dense** top-3 : thesaurus:ciclosporine:124:28, thesaurus:lercanidipine:334:0, pharmnet:solution a chlorure de calcium dihydrate chlorure de magnesium hexahydrate glucose anhydre s f monohydrate solution b chlorure de sodium bicarbonate de sodium
- **hybrid** top-3 : thesaurus:acide acetylsalicylique:5:9, thesaurus:ciclosporine:124:49, thesaurus:tenofovir alafenamide:558:0

### Q5 (negative)

> Quel médicament prendre pour mes douleurs dentaires ?

- **bm25** top-3 : nomenclature_dz:lidocaine chlorhydrate noradrenaline tartrate, nomenclature_dz:lidocaine chlorhydrate, thesaurus:topotecane:577:1
- **dense** top-3 : pharmnet:mepivacaine chlorhydrate, thesaurus:diltiazem:183:9, thesaurus:dronedarone:201:2
- **hybrid** top-3 : thesaurus:anticholinesterasiques:48:1, pharmnet:mepivacaine chlorhydrate, nomenclature_dz:lidocaine chlorhydrate noradrenaline tartrate
