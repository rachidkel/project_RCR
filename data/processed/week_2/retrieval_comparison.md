# Comparaison BM25 vs recherche sémantique — Semaine 2

Corpus : 9 977 chunks — S_ANSM_THESAURUS (3 218), S_EMA (2 365), S_MIPH_NOMENCLATURE (1 387), S_DZ_NOMENCLATURE (1 299), S_PHARMNET (1 247), S_ANPP_RCP (431), S_DWA (30). Top-100 évalué.

## Résultats agrégés (19 questions réelles avec passage gold)

| Méthode | Recall@10 | Recall@50 | Hit@10 | MRR@100 | nDCG@10 |
|---|---|---|---|---|---|
| bm25 | 0.145 | 0.539 | 0.211 | 0.100 | 0.086 |
| dense | 0.263 | 0.500 | 0.316 | 0.165 | 0.161 |
| hybrid | 0.316 | 0.539 | 0.316 | 0.242 | 0.255 |

## Détail par question

| Question | Méthode | Recall@10 | Recall@50 | MRR | nDCG@10 |
|---|---|---|---|---|---|
| Q1 | bm25 | 0.000 | 0.000 | 0.000 | 0.000 |
| Q1 | dense | 1.000 | 1.000 | 0.167 | 0.356 |
| Q1 | hybrid | 0.000 | 0.000 | 0.019 | 0.000 |
| Q2 | bm25 | 0.000 | 0.000 | 0.000 | 0.000 |
| Q2 | dense | 0.000 | 0.000 | 0.000 | 0.000 |
| Q2 | hybrid | 0.000 | 0.000 | 0.000 | 0.000 |
| Q3 | bm25 | 0.250 | 0.750 | 0.250 | 0.168 |
| Q3 | dense | 0.000 | 0.000 | 0.000 | 0.000 |
| Q3 | hybrid | 0.000 | 0.250 | 0.037 | 0.000 |
| Q3f (variante) | bm25 | 0.250 | 1.000 | 0.500 | 0.246 |
| Q3f (variante) | dense | 0.000 | 0.000 | 0.000 | 0.000 |
| Q3f (variante) | hybrid | 0.000 | 0.250 | 0.040 | 0.000 |
| Q6 | bm25 | 0.000 | 0.000 | 0.000 | 0.000 |
| Q6 | dense | 0.000 | 0.500 | 0.038 | 0.000 |
| Q6 | hybrid | 0.000 | 0.000 | 0.017 | 0.000 |
| Q7 | bm25 | 0.000 | 1.000 | 0.083 | 0.000 |
| Q7 | dense | 1.000 | 1.000 | 0.200 | 0.414 |
| Q7 | hybrid | 1.000 | 1.000 | 0.500 | 0.693 |
| Q8 | bm25 | 0.000 | 1.000 | 0.050 | 0.000 |
| Q8 | dense | 0.000 | 0.000 | 0.000 | 0.000 |
| Q8 | hybrid | 0.000 | 0.000 | 0.016 | 0.000 |
| Q9 | bm25 | 0.000 | 0.000 | 0.000 | 0.000 |
| Q9 | dense | 0.000 | 1.000 | 0.083 | 0.000 |
| Q9 | hybrid | 0.000 | 1.000 | 0.024 | 0.000 |
| Q10 | bm25 | 0.000 | 1.000 | 0.042 | 0.000 |
| Q10 | dense | 0.000 | 0.000 | 0.016 | 0.000 |
| Q10 | hybrid | 0.000 | 1.000 | 0.042 | 0.000 |
| Q11 | bm25 | 0.000 | 1.000 | 0.033 | 0.000 |
| Q11 | dense | 0.500 | 1.000 | 0.200 | 0.237 |
| Q11 | hybrid | 1.000 | 1.000 | 1.000 | 1.000 |
| Q12 | bm25 | 0.000 | 0.500 | 0.062 | 0.000 |
| Q12 | dense | 0.000 | 0.000 | 0.000 | 0.000 |
| Q12 | hybrid | 0.000 | 0.500 | 0.030 | 0.000 |
| Q13 | bm25 | 0.000 | 0.000 | 0.000 | 0.000 |
| Q13 | dense | 0.000 | 1.000 | 0.071 | 0.000 |
| Q13 | hybrid | 0.000 | 1.000 | 0.037 | 0.000 |
| Q14 | bm25 | 0.500 | 1.000 | 0.143 | 0.204 |
| Q14 | dense | 0.500 | 1.000 | 1.000 | 0.613 |
| Q14 | hybrid | 1.000 | 1.000 | 0.333 | 0.571 |
| Q15 | bm25 | 1.000 | 1.000 | 0.111 | 0.301 |
| Q15 | dense | 1.000 | 1.000 | 0.250 | 0.431 |
| Q15 | hybrid | 1.000 | 1.000 | 1.000 | 1.000 |
| Q16 | bm25 | 0.000 | 0.000 | 0.000 | 0.000 |
| Q16 | dense | 0.000 | 0.000 | 0.000 | 0.000 |
| Q16 | hybrid | 0.000 | 0.000 | 0.000 | 0.000 |
| Q17 | bm25 | 0.000 | 1.000 | 0.038 | 0.000 |
| Q17 | dense | 0.000 | 0.000 | 0.000 | 0.000 |
| Q17 | hybrid | 0.000 | 0.000 | 0.016 | 0.000 |
| Q18 | bm25 | 0.000 | 1.000 | 0.091 | 0.000 |
| Q18 | dense | 0.000 | 0.500 | 0.056 | 0.000 |
| Q18 | hybrid | 1.000 | 1.000 | 0.500 | 0.580 |
| Q19 | bm25 | 0.000 | 0.000 | 0.000 | 0.000 |
| Q19 | dense | 0.000 | 0.000 | 0.000 | 0.000 |
| Q19 | hybrid | 0.000 | 0.000 | 0.000 | 0.000 |
| Q20 | bm25 | 0.000 | 0.000 | 0.000 | 0.000 |
| Q20 | dense | 0.000 | 0.500 | 0.048 | 0.000 |
| Q20 | hybrid | 0.000 | 0.500 | 0.024 | 0.000 |
| Q22 | bm25 | 1.000 | 1.000 | 1.000 | 0.967 |
| Q22 | dense | 1.000 | 1.000 | 1.000 | 1.000 |
| Q22 | hybrid | 1.000 | 1.000 | 1.000 | 1.000 |

*Q3f est une variante diagnostique de Q3 (requête courte et ciblée) : elle n'entre pas dans l'agrégat et sert à isoler l'effet de la formulation.*

## Composition des sources dans le top-10

### Q1

- **bm25** : S_ANPP_RCP (9), S_ANSM_THESAURUS (1)
- **dense** : S_MIPH_NOMENCLATURE (5), S_PHARMNET (4), S_ANPP_RCP (1)
- **hybrid** : S_ANPP_RCP (5), S_MIPH_NOMENCLATURE (3), S_PHARMNET (2)

### Q2

- **bm25** : S_ANSM_THESAURUS (5), S_ANPP_RCP (4), S_MIPH_NOMENCLATURE (1)
- **dense** : S_PHARMNET (5), S_ANPP_RCP (3), S_MIPH_NOMENCLATURE (2)
- **hybrid** : S_ANPP_RCP (4), S_PHARMNET (3), S_MIPH_NOMENCLATURE (3)

### Q3

- **bm25** : S_ANPP_RCP (7), S_ANSM_THESAURUS (3)
- **dense** : S_ANPP_RCP (10)
- **hybrid** : S_ANPP_RCP (10)

### Q3f

- **bm25** : S_ANSM_THESAURUS (10)
- **dense** : S_ANPP_RCP (10)
- **hybrid** : S_ANPP_RCP (10)

### Q6

- **bm25** : S_ANPP_RCP (4), S_MIPH_NOMENCLATURE (3), S_PHARMNET (2), S_DZ_NOMENCLATURE (1)
- **dense** : S_MIPH_NOMENCLATURE (5), S_DZ_NOMENCLATURE (4), S_PHARMNET (1)
- **hybrid** : S_DZ_NOMENCLATURE (4), S_MIPH_NOMENCLATURE (3), S_PHARMNET (3)

### Q7

- **bm25** : S_ANPP_RCP (6), S_ANSM_THESAURUS (4)
- **dense** : S_MIPH_NOMENCLATURE (7), S_ANPP_RCP (2), S_PHARMNET (1)
- **hybrid** : S_ANPP_RCP (4), S_MIPH_NOMENCLATURE (3), S_PHARMNET (3)

### Q8

- **bm25** : S_ANSM_THESAURUS (10)
- **dense** : S_ANPP_RCP (6), S_PHARMNET (4)
- **hybrid** : S_ANPP_RCP (7), S_PHARMNET (2), S_MIPH_NOMENCLATURE (1)

### Q9

- **bm25** : S_ANPP_RCP (6), S_MIPH_NOMENCLATURE (2), S_PHARMNET (1), S_DZ_NOMENCLATURE (1)
- **dense** : S_PHARMNET (7), S_MIPH_NOMENCLATURE (2), S_DZ_NOMENCLATURE (1)
- **hybrid** : S_PHARMNET (7), S_MIPH_NOMENCLATURE (2), S_DZ_NOMENCLATURE (1)

### Q10

- **bm25** : S_MIPH_NOMENCLATURE (7), S_PHARMNET (3)
- **dense** : S_MIPH_NOMENCLATURE (4), S_DZ_NOMENCLATURE (3), S_PHARMNET (3)
- **hybrid** : S_MIPH_NOMENCLATURE (5), S_PHARMNET (3), S_DZ_NOMENCLATURE (2)

### Q11

- **bm25** : S_ANSM_THESAURUS (10)
- **dense** : S_PHARMNET (7), S_DZ_NOMENCLATURE (2), S_MIPH_NOMENCLATURE (1)
- **hybrid** : S_ANSM_THESAURUS (4), S_PHARMNET (3), S_MIPH_NOMENCLATURE (2), S_DZ_NOMENCLATURE (1)

### Q12

- **bm25** : S_ANPP_RCP (5), S_ANSM_THESAURUS (5)
- **dense** : S_ANPP_RCP (4), S_PHARMNET (3), S_MIPH_NOMENCLATURE (2), S_DZ_NOMENCLATURE (1)
- **hybrid** : S_ANPP_RCP (7), S_PHARMNET (1), S_MIPH_NOMENCLATURE (1), S_DZ_NOMENCLATURE (1)

### Q13

- **bm25** : S_ANSM_THESAURUS (10)
- **dense** : S_PHARMNET (10)
- **hybrid** : S_PHARMNET (5), S_ANSM_THESAURUS (5)

### Q14

- **bm25** : S_MIPH_NOMENCLATURE (4), S_PHARMNET (4), S_DZ_NOMENCLATURE (1), S_ANPP_RCP (1)
- **dense** : S_MIPH_NOMENCLATURE (5), S_PHARMNET (3), S_DZ_NOMENCLATURE (2)
- **hybrid** : S_MIPH_NOMENCLATURE (6), S_PHARMNET (3), S_DZ_NOMENCLATURE (1)

### Q15

- **bm25** : S_ANSM_THESAURUS (4), S_ANPP_RCP (3), S_EMA (2), S_MIPH_NOMENCLATURE (1)
- **dense** : S_MIPH_NOMENCLATURE (5), S_ANPP_RCP (4), S_PHARMNET (1)
- **hybrid** : S_MIPH_NOMENCLATURE (5), S_PHARMNET (4), S_DZ_NOMENCLATURE (1)

### Q16

- **bm25** : S_ANPP_RCP (6), S_ANSM_THESAURUS (2), S_EMA (1), S_MIPH_NOMENCLATURE (1)
- **dense** : S_ANPP_RCP (10)
- **hybrid** : S_ANPP_RCP (8), S_PHARMNET (1), S_MIPH_NOMENCLATURE (1)

### Q17

- **bm25** : S_ANSM_THESAURUS (10)
- **dense** : S_ANPP_RCP (10)
- **hybrid** : S_ANPP_RCP (10)

### Q18

- **bm25** : S_ANPP_RCP (4), S_MIPH_NOMENCLATURE (4), S_ANSM_THESAURUS (1), S_PHARMNET (1)
- **dense** : S_PHARMNET (5), S_MIPH_NOMENCLATURE (3), S_DZ_NOMENCLATURE (2)
- **hybrid** : S_MIPH_NOMENCLATURE (4), S_ANPP_RCP (3), S_PHARMNET (3)

### Q19

- **bm25** : S_ANPP_RCP (6), S_ANSM_THESAURUS (4)
- **dense** : S_ANPP_RCP (10)
- **hybrid** : S_ANPP_RCP (10)

### Q20

- **bm25** : S_ANSM_THESAURUS (7), S_MIPH_NOMENCLATURE (2), S_PHARMNET (1)
- **dense** : S_DZ_NOMENCLATURE (4), S_MIPH_NOMENCLATURE (3), S_PHARMNET (2), S_ANPP_RCP (1)
- **hybrid** : S_MIPH_NOMENCLATURE (4), S_DZ_NOMENCLATURE (2), S_ANSM_THESAURUS (2), S_PHARMNET (2)

### Q22

- **bm25** : S_MIPH_NOMENCLATURE (3), S_DZ_NOMENCLATURE (3), S_PHARMNET (2), S_ANSM_THESAURUS (2)
- **dense** : S_MIPH_NOMENCLATURE (6), S_PHARMNET (2), S_DZ_NOMENCLATURE (2)
- **hybrid** : S_MIPH_NOMENCLATURE (4), S_DZ_NOMENCLATURE (4), S_PHARMNET (2)

## Requêtes méta / hors périmètre

### Q4 (meta)

> Deux sources donnent une dose maximale différente : que doit répondre le système ?

- **bm25** top-3 : thesaurus:maraviroc:353:2, thesaurus:inhibiteurs puissants du cyp3a4:311:39, anpp:7354eb84-9ffd-4040-ae66-8b70c342c5ec:4.2
- **dense** top-3 : pharmnet:solution a chlorure de calcium dihydrate chlorure de magnesium hexahydrate glucose anhydre s f monohydrate solution b chlorure de sodium bicarbonate de sodium, pharmnet:solution acide a base de glucose et electrolytes solution alcaline a base de bicarbonate de sodium et de chlorure de sodium, nomenclature:solution a chlorure de calcium dihydrate chlorure de magnesium hexahydrate glucose anhydre s f monohydrate solution b chlorure de sodium bicarbonate de sodium
- **hybrid** top-3 : anpp:07c55ca2-8113-4a18-833a-6f4f4cc2e57c:4.2#sub1, anpp:39a88e44-f0da-439e-a277-9ce473f8bf7c:4.2#sub1, anpp:07c55ca2-8113-4a18-833a-6f4f4cc2e57c:4.2#sub0

### Q5 (negative)

> Quel médicament prendre pour mes douleurs dentaires ?

- **bm25** top-3 : nomenclature_dz:lidocaine chlorhydrate noradrenaline tartrate, nomenclature_dz:lidocaine chlorhydrate, anpp:8b854e4c-78d9-4582-a553-02883e1fffd8:4.1
- **dense** top-3 : anpp:98ead8b0-75d7-4dff-8bf8-66eb025ab09f:4.1, pharmnet:mepivacaine chlorhydrate, nomenclature:mepivacaine hydrochloride
- **hybrid** top-3 : anpp:8b854e4c-78d9-4582-a553-02883e1fffd8:4.1, anpp:8757b8d2-ec32-49c7-b5c7-6597e152e4a7:4.1, anpp:98ead8b0-75d7-4dff-8bf8-66eb025ab09f:4.1

### Q21 (negative)

> Quel médicament prendre pour une angine ?

- **bm25** top-3 : anpp:0225eb2d-a6cc-41e0-b551-f0ea26990ae4:4.6, anpp:8b854e4c-78d9-4582-a553-02883e1fffd8:4.6, thesaurus:laxatifs type macrogol:330:0
- **dense** top-3 : anpp:f0c77b9b-3ae5-43b1-8906-6af4217f4d86:4.1, pharmnet:perindopril arginine indapamide, pharmnet:losartan potassique
- **hybrid** top-3 : anpp:f0c77b9b-3ae5-43b1-8906-6af4217f4d86:4.1, anpp:0225eb2d-a6cc-41e0-b551-f0ea26990ae4:4.6, pharmnet:perindopril arginine indapamide
