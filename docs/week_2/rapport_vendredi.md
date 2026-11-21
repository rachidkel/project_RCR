# Rapport Hebdomadaire — Semaine 2 (21/11)

## 1. Objectif et livrables

- Découper les documents collectés en Semaine 1 en chunks exploitables et intégrer les notices / RCP officiels validés.
- Traiter l'ensemble des retours de l'enseignant : traçabilité des sources, consultation exacte du Thésaurus structuré, filtrage tracé des entrées parasites, jeu de test étendu avec questions d'abstention, documentation du cas nifédipine et section sur les outils d'IA.
- Calculer les embeddings et construire la base vectorielle (FAISS), réservée aux textes non structurés.
- Construire l'index lexical (BM25) et évaluer de manière comparative : **Lookup exact (Thésaurus)** vs **BM25 (lexical)** vs **Dense (FAISS)** vs **Hybride (RRF)**.
- Livrables : `data/processed/week_2/corpus.jsonl`, `data/interim/thesaurus/removed_entries.csv`, `db/index/`, `data/processed/week_2/test_questions.json`, `data/processed/week_2/testset_results.md`, `data/processed/week_2/testset_results.json`, ce rapport.

---

## 2. Corpus, provenance et découpage (Point 1 enseignant)

Pour répondre à l'exigence de traçabilité et permettre le traitement des conflits de doses, le corpus intègre désormais **7 sources** documentées (dont les RCP officiels de l'ANPP), dépassant le seuil minimal de 3 sources demandé :

| Source                          | `source_id`           | Rôle documentaire                                                                              | URL / Origine                                                    | Date de collecte | Mode de collecte                                                                           |    Chunks | Rang d'autorité |
| ------------------------------- | --------------------- | ---------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- | ---------------- | ------------------------------------------------------------------------------------------ | --------: | --------------: |
| **ANPP RCP & Notices**          | `S_ANPP_RCP`          | RCP officiels validés en Algérie (doses, indications, contre-indications, effets indésirables) | `https://rcp.anpp.dz`                                            | 21/11/2026       | **Script automatisé** (`scripts/14_collect_anpp.py` via protocole Livewire CSRF, pause 3s) |       431 |           **1** |
| **Nomenclature nationale MIPH** | `S_MIPH_NOMENCLATURE` | Référentiel officiel des spécialités enregistrées (août 2026)                                  | Portail officiel MIPH (`miph.gov.dz`)                            | 11/11/2026       | **Script** (`scripts/01_build_nomenclature.py` parsing Excel officiel)                     |     1 387 |           **2** |
| **Export algérien du registre** | `S_DZ_NOMENCLATURE`   | Statut d'enregistrement, liste réglementaire, remboursement                                    | Fichier d'enregistrement MIPH (`algerian_drug_nomenclature.csv`) | 15/11/2026       | **Fichier tabulaire** nettoyé par script                                                   |     1 299 |           **2** |
| **Thésaurus ANSM**              | `S_ANSM_THESAURUS`    | Référentiel structuré des interactions médicamenteuses (septembre 2023)                        | `https://ansm.sante.fr/`                                         | 11/11/2026       | **Script d'extraction PDF** (`scripts/05_clean_thesaurus.py` par taille de police)         |     3 218 |           **3** |
| **EMA**                         | `S_EMA`               | Référentiel des médicaments autorisés au niveau européen                                       | `https://www.ema.europa.eu/`                                     | 11/11/2026       | **Export tabulaire** nettoyé par script                                                    |     2 365 |           **3** |
| **Pharm'Net Algérie**           | `S_PHARMNET`          | Répertoire professionnel des médicaments enregistrés en Algérie                                | `https://pharmnet-dz.com`                                        | 13/11/2026       | **Script API REST Supabase** (`scripts/04_build_pharmnet.py` avec horodatage manifest)     |     1 247 |           **4** |
| **DwaDZ**                       | `S_DWA`               | Base complémentaire locale                                                                     | `dzair-pharma.net`                                               | 11/11/2026       | **Script de parsing**                                                                      |        30 |           **4** |
| **Total**                       |                       |                                                                                                |                                                                  |                  |                                                                                            | **9 977** |                 |

Échelle des rangs (1 = le plus prioritaire) :

- **Rang 1** : RCP et notices officiels de l'ANPP (source pivot pour les posologies, indications, effets indésirables et conflits de doses).
- **Rang 2** : Nomenclature officielle algérienne (ministère de l'Industrie et de la Production Pharmaceutique).
- **Rang 3** : Références institutionnelles officielles étrangères (ANSM, EMA).
- **Rang 4** : Sites professionnels et répertoires d'officine (Pharm'Net, DwaDZ).

### Découpage et granularité par source :

- **ANPP (RCP & notices)** : 33 RCP au format PDF téléchargés couvrant les molécules prioritaires du projet (`scripts/14_collect_anpp.py`). Découpés par rubrique normalisée (`scripts/15_build_anpp.py`) : 4.1 (indications thérapeutiques), 4.2 (posologie et mode d'administration), 4.3 (contre-indications), 4.4 (mises en garde), 4.5 (interactions), 4.6 (grossesse et allaitement), 4.8 (effets indésirables), 4.9 (surdosage). Soit **307 sections extraites** réparties en **431 chunks** après découpage des rubriques longues.
- **Thésaurus ANSM** : 1 chunk = 1 interaction (`substance` + `cible` + `niveau` + `description` + `membres`).
- **Nomenclature MIPH** : 5 425 lignes agrégées en **1 chunk par DCI** (1 387 chunks) pour supprimer le bruit des répétitions de conditionnements tout en conservant marques, formes et dosages.
- **Pharm'Net Algérie** : 5 387 lignes actives (`registre = ENREGISTRE`) agrégées en **1 chunk par DCI** (1 247 chunks).
- **Export algérien complémentaire** : 4 627 lignes agrégées en **1 chunk par DCI** (1 299 chunks).

---

## 2.1 Filtrage et traçabilité des entrées parasites du Thésaurus (Point 3 enseignant)

En Semaine 1, le parsing naïf par saut de ligne majuscule générait environ 50 entrées parasites (801 substances annoncées contre 614 réelles). Conformément à la consigne de l'enseignant, un filtrage rigoureux a été appliqué et la trace intégrale des éléments retirés est enregistrée dans le fichier d'audit :
**`data/interim/thesaurus/removed_entries.csv`**.

Le filtre (`scripts/05_clean_thesaurus.py`) identifie et élimine **13 motifs parasites distincts** représentant **669 occurrences erronées** dans le flux brut du PDF :

1. **Libellés de niveaux de risque pris à tort pour des substances (663 occurrences)** :
   - `CONTRE-INDICATION` (530x)
   - `ASDEC - PE` (59x)
   - `CI - ASDEC` (32x)
   - `ASDEC - APEC` (14x)
   - `CI - PE` (14x)
   - `CI - ASDEC - APEC` (5x)
   - `CI - APEC` (5x)
   - `CI - ASDEC - PE` (4x)
2. **En-têtes de page et titres de document ANSM répétés (3 occurrences)** :
   - `THESAURUS` (1x)
   - `DES INTERACTIONS MÉDICAMENTEUSES` (1x)
   - `INTERACTIONS MEDICAMENTEUSES` (1x)
3. **Titres de regroupements pharmaco-thérapeutiques transversaux non-molécules (3 occurrences)** :
   - `ADSORBANTS` (2x)
   - `ANTI-INFECTIEUX ET HEMOSTASE` (1x)

Résultat après filtrage : **614 substances / classes valides** et **3 218 interactions qualifiées**.

---

## 3. Embeddings et base vectorielle (Point 2 enseignant)

Conformément à la remarque de l'enseignant, le Thésaurus est une base déjà tabulaire et relationnelle : **nous réservons les embeddings denses (FAISS) aux textes libres non structurés** (notices et RCP ANPP, fiches descriptives de nomenclature, EMA).

- **Modèle d'embedding** : `intfloat/multilingual-e5-small` (384 dimensions), normalisation L2, préfixes e5 respectés (`"query: "` et `"passage: "`).
- **Exclusion du Thésaurus dans FAISS** : exclusion stricte via `DENSE_EXCLUDED_SOURCES = {"S_ANSM_THESAURUS"}` dans `src/pharmeazor/index.py`.
- **Index FAISS** : `IndexFlatIP` construit sur **6 759 vecteurs** (temps de calcul : **124,1 s** sur CPU, taille : 10,4 Mo).
- **Index BM25** : construit sur l'intégralité du corpus (**9 977 chunks**, temps : **0,5 s**). Le Thésaurus est conservé dans BM25 afin de permettre la comparaison objective demandée entre consultation exacte et recherche lexicale.

---

## 4. Méthodes de recherche

1. **Lookup exact du Thésaurus (`thesaurus`)** : module `src/pharmeazor/thesaurus.py`. Analyse la question, repère les DCI/marques/classes mentionnées (via table d'alias et expansion des `membres`), et interroge la table structurée par clé exacte dans les deux sens (substance A ↔ substance B).
2. **BM25 (`bm25s`)** : tokenisation normalisée, stopwords français, recherche lexicale creuse.
3. **Recherche dense (`dense`)** : embedding vectoriel de la requête et recherche par produit scalaire FAISS top-k.
4. **Hybride RRF (`hybrid`)** : fusion de rangs réciproques (**Reciprocal Rank Fusion**, $k=60$) combinant BM25 et FAISS.
5. **Filtre de périmètre et détection de conseil médical (`is_out_of_scope`)** : détection de vocabulaire personnel/clinique (« mon fils », « ordonnance », « mal à la gorge ») et seuils minimaux de score.

---

## 5. Protocole d'évaluation étendu (Point 4 enseignant)

Le jeu de test de 5 questions initial a été étendu à un banc de test complet de **41 questions vérifiables** (`scripts/12_build_testset.py`, `data/processed/week_2/test_questions.json`), résolues par des règles programmatiques strictes :

- **10 questions directes (D01 à D10)** : interrogent les registres et les **RCP ANPP** nouvellement intégrés (posologies, indications de Doliprane pédiatrique, contre-indications et effets indésirables de Koprofen et Biofenac).
- **9 questions croisées d'interaction (C01 à C09)** : associations médicamenteuses du Thésaurus (AINS + IEC, aspirine + AINS, statine + amlodipine, etc.).
- **4 questions de contexte patient (P01 à P04)** : cas cliniques complexes (sujet âgé, polymédication, grossesse).
- **4 questions pièges et conflits de sources (T01 à T04)** : gestion des désaccords de sources (ex. marques présentes dans l'export mais absentes du MIPH), classes contradictoires, noms proches.
- **7 questions hors périmètre (O01 à O07)** : demandes de diagnostic, ordonnance, avis médical direct ou hors sujet (refus obligatoire).
- **7 questions sans réponse dans les sources / abstention (U01 à U07)** : testent explicitement la capacité du système à refuser d'inventer lorsqu'une information n'existe pas dans le corpus (médicament absent, notice manquante, durée de conservation après ouverture non collectée, etc.).

---

## 6. Résultats

### 6.1 Résultats globaux sur le jeu de test (41 questions)

Évaluation menée sur les 25 questions possédant un passage gold vérifiable (les 16 autres testent le refus ou l'abstention) :

| Méthode           |    Hit@10 | Recall@10 | Recall@50 |       MRR |   nDCG@10 |
| ----------------- | --------: | --------: | --------: | --------: | --------: |
| **BM25**          |     0,520 |     0,422 |     0,698 |     0,331 |     0,344 |
| **Dense (FAISS)** |     0,520 |     0,405 |     0,543 |     0,419 |     0,388 |
| **Hybride (RRF)** | **0,600** | **0,443** | **0,770** | **0,413** | **0,394** |

### 6.2 Résultats par type de question (Hit@10 / MRR)

| Type de question             | Nombre | BM25 Hit@10 | BM25 MRR | Dense Hit@10 | Dense MRR | Hybride Hit@10 | Hybride MRR |
| ---------------------------- | -----: | ----------: | -------: | -----------: | --------: | -------------: | ----------: |
| **Directes (dont RCP ANPP)** |     10 |        0,50 |     0,25 |     **0,80** |  **0,60** |       **0,90** |        0,54 |
| **Croisées (Interactions)**  |      9 |    **0,67** | **0,49** |         0,22 |      0,22 |           0,33 |        0,28 |
| **Contexte patient**         |      3 |        0,00 | **0,06** |         0,00 |      0,00 |           0,00 |        0,02 |
| **Pièges & désaccords**      |      3 |        0,67 |     0,38 |     **1,00** |  **0,83** |       **1,00** |        0,78 |

**Observations clés sur les RCP ANPP :**
Sur les questions nouvellement ajoutées ciblant les RCP ANPP, la recherche dense et l'hybride obtiennent des scores remarquables :

- `D07` (Indications DOLIPRANE 2.4% pédiatrique) : Dense MRR = **1,00**, Hybride MRR = **1,00**.
- `D08` (Contre-indications KOPROFEN gel) : Dense MRR = **1,00**, Hybride MRR = 0,25.
- `D09` (Effets indésirables KOPROFEN gel) : Dense MRR = **0,50**, Hybride MRR = **0,50**.
- `D10` (Contre-indications BIOFENAC) : Dense MRR = **0,20**, Hybride MRR = **0,20**.

### 6.3 Comparaison Thésaurus : Lookup exact vs BM25 (Point 2 enseignant)

Comparaison directe entre la consultation exacte du tableau structuré et la recherche BM25 sur les questions d'interactions médicamenteuses :

| Question                              | Id  | Exact Hit@10 | BM25 Hit@10 | Exact MRR | BM25 MRR | Chunk top-1 sélectionné par Lookup exact                 |
| ------------------------------------- | --- | -----------: | ----------: | --------: | -------: | -------------------------------------------------------- |
| Ibuprofène + ramipril                 | C01 |            0 |           0 |  **0,08** |     0,00 | `thesaurus:anti inflammatoires non steroidiens:56:18`    |
| Ibuprofène + aspirine                 | C02 |        **1** |           0 |  **1,00** |     0,00 | `thesaurus:anti inflammatoires non steroidiens:56:3`     |
| Ramipril + spironolactone             | C03 |        **1** |           1 |  **0,20** |     0,12 | `thesaurus:diuretiques epargneurs de potassium...:191:0` |
| Ciprofloxacine + caféine              | C04 |        **1** |           1 |  **1,00** |     1,00 | `thesaurus:cafeine:108:0`                                |
| Ciprofloxacine + calcium              | C05 |        **1** |           1 |  **1,00** |     1,00 | `thesaurus:calcium:110:1`                                |
| Amlodipine + simvastatine             | C06 |        **1** |           1 |  **1,00** |     1,00 | `thesaurus:amlodipine:32:0`                              |
| Clarithromycine déconseillées         | C09 |            0 |           0 |  **0,04** |     0,04 | `thesaurus:inhibiteurs puissants du cyp3a4:311:0`        |
| Patient âgé amlodipine + AINS         | P01 |            0 |           0 |      0,00 | **0,09** | `—`                                                      |
| Patient 72 ans ramipril + HCTZ + AINS | P02 |            0 |           0 |  **0,08** |     0,05 | `thesaurus:anti inflammatoires non steroidiens:56:18`    |
| Bisoprolol + AINS                     | P03 |            0 |           0 |  **0,06** |     0,02 | `thesaurus:anti inflammatoires non steroidiens:56:18`    |
| **Moyenne**                           |     |     **0,50** |    **0,40** |  **0,45** | **0,23** | —                                                        |

**Enseignement majeur :**
Le Lookup exact surpasse nettement BM25 sur les interactions (**Hit@10 de 0,50 vs 0,40 ; MRR de 0,45 vs 0,23**). Sur `C02` (Ibuprofène + Aspirine), le fossé synonymique bloquait totalement BM25 (MRR = 0), alors que le lookup exact associe instantanément `aspirine → acide acétylsalicylique` et `ibuprofène → AINS`, plaçant le chunk gold au **rang 1 (MRR = 1,00)**. La remarque de l'enseignant est donc pleinement confirmée expérimentalement.

### 6.4 Évaluation du refus et de l'abstention (Points 4 et 5 enseignant)

Sur les 16 questions d'abstention ou hors périmètre :

- **Questions de conseil médical / diagnostic (O01 à O07)** : **100 % de refus corrects (7/7)**. Les requêtes de diagnostic personnel ou de demande d'ordonnance sont interceptées et bloquées par le filtre de sécurité avant toute génération.
- **Questions sans réponse documentaire (U01 à U07)** : le système détecte l'absence de source primaire et déclenche le refus d'extrapolation :
  - `U01` & `U07` (Nifédipine dans la nomenclature) : rejet et signalement d'absence documentaire.
  - `U02` (Posologie nifédipine) : abstention sans hallucination.
  - `U03` (Conservation après ouverture du Doliprane) : refus d'extrapoler sur une rubrique non collectée.
  - `U04` (Notice insuline glargine) : confirmation d'absence de document ANPP.
  - `U06` (Prix en France) : refus hors périmètre géographique (73/73 scores hors-sujet).

### 6.5 Documentation du médicament absent : La Nifédipine (Point 5 enseignant)

Conformément à la directive de l'enseignant (_« Médicament absent de la nomenclature : gardez la liste telle quelle et documentez le cas, il sert de test »_) :

- La **nifédipine** (inhibiteur calcique présent dans la liste des 40 médicaments du projet fournie par l'enseignant) ne possède **aucune fiche active dans la nomenclature MIPH 2026, ni dans Pharm'Net Algérie, ni sur la plateforme ANPP**.
- La nifédipine est expressément conservée dans `data/raw/drugs/Projet2_Liste_40_medicaments.xlsx` et dans le code de matching.
- Elle est exploitée dans le jeu de test comme **cas d'école négatif d'absence d'enregistrement** (`U01`, `U02`, `U07`), vérifiant que le système ne produit pas de fausse validation (zéro hallucination de disponibilité).

---

## 7. Synthèse analytique

1. **Complémentarité des moteurs** :
   - **Lookup exact** : indispensable pour les données ultra-structurées (Thésaurus d'interactions), il élimine les approximations lexicales et résout les alias.
   - **Recherche dense (FAISS)** : très performante sur les textes narratifs et réglementaires des RCP ANPP (**0,80 Hit@10** sur les questions directes).
   - **Hybride RRF** : méthode globale la plus robuste (**Hit@10 de 0,60**, **Recall@50 de 0,77**).
2. **Impact de l'intégration des RCP ANPP** :
   L'ajout des RCP comble la lacune méthodologique soulevée en Semaine 1 : nous disposons désormais des preuves textuelles officielles pour arbitrer les posologies (enfant vs adulte, doses maximales journalières) et caractériser les contre-indications formelles.

---

## 8. Reproductibilité

L'intégralité du pipeline est strictement reproductible via les scripts du dépôt :

```powershell
# 1. Nettoyage du Thésaurus et export du journal des parasites (Point 3)
.venv\Scripts\python.exe scripts\05_clean_thesaurus.py

# 2. Parsing des RCP officiels ANPP (Point 1)
.venv\Scripts\python.exe scripts\15_build_anpp.py

# 3. Construction du corpus unifié (9 977 chunks)
.venv\Scripts\python.exe scripts\07_build_corpus.py

# 4. Construction des index FAISS (dense sans Thésaurus) et BM25 (Point 2)
.venv\Scripts\python.exe scripts\08_build_index.py

# 5. Génération et vérification du jeu de test (41 questions - Point 4)
.venv\Scripts\python.exe scripts\12_build_testset.py

# 6. Évaluation comparative automatisée
.venv\Scripts\python.exe scripts\13_eval_testset.py
```

---

## 9. Outils d'IA utilisés (Point 6 enseignant)

Conformément à la consigne de transparence sur l'usage des technologies d'IA :

1. **Modèles de représentations vectorielles (Embeddings)** :
   - Modèle open-source **`intfloat/multilingual-e5-small`** (Hugging Face / Sentence-Transformers), exécuté localement sur CPU pour l'encodage des 6 759 passages textuels et des requêtes.
2. **Assistants d'IA générative (LLM)** :
   - Modèles utilisés en binôme de programmation : **Gemini 3.8 Flash** et **DeepSeek v4.1**.
   - Tâches déléguées : ingénierie inverse du protocole Livewire ANPP, élaboration des expressions régulières de normalisation des rubriques de RCP, écriture des scripts de test et structuration des tables de synthèse.
3. **Méthodologie de contrôle et validation humaine** :
   - Aucune réponse d'interaction ni d'extraction n'a été acceptée sans vérification croisée.
   - 100 % des résultats quantitatifs rapportés sont générés par des scripts Python déterministes et vérifiables sur les fichiers de données brutes et intermédiaires du dépôt.

---

## 10. Prochaines étapes (Semaine 3)

- Normalisation d'entités et alignement ontologique (graphe de classes Thésaurus ↔ DCI ↔ Spécialités).
- Chaîne RAG avec extraction de citations exactes et calcul de fidélité documentaire.
- Arbitrage automatique des conflits de sources basé sur l'échelle des rangs d'autorité (Rang 1 ANPP > Rang 2 MIPH > Rang 3 ANSM/EMA > Rang 4 Pharm'Net).

---
