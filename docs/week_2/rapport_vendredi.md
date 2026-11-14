# Rapport Hebdomadaire — Semaine 2 (20/11)

## 1. Objectif et livrables
- Découper les documents collectés en Semaine 1 en chunks exploitables.
- Calculer les embeddings et construire une base vectorielle (FAISS).
- Construire un index lexical (BM25) et comparer **recherche par mots-clés** vs **recherche sémantique** sur les questions du projet.
- Livrables : `data/processed/week_2/corpus.jsonl`, `db/index/`, `data/processed/week_2/retrieval_comparison.md`, ce rapport.

## 2. Corpus et découpage

| Source | `source_id` | Chunks | Rang d'autorité |
|---|---|---:|---:|
| Thésaurus ANSM (interactions) | `S_ANSM_THESAURUS` | 3 218 | 3 |
| Nomenclature MIPH (médicaments) | `S_MIPH_NOMENCLATURE` | 1 387 | 1 |
| Pharm'Net Algérie (médicaments enregistrés) | `S_PHARMNET` | 1 247 | 1 |
| EMA (médicaments autorisés) | `S_EMA` | 2 365 | 3 |
| DWA (liste alsacienne) | `S_DWA` | 30 | 2 |
| **Total** | | **8 247** | |

- **Correction du parsing du Thésaurus** : le rapport de Semaine 1 annonçait 801 substances / 2 561 interactions. Le parseur traitait à tort les libellés de risque en majuscules (`ASDEC - APEC`, etc.) comme des titres, ce qui fusionnait des blocs. La détection des titres se fait désormais par **taille de police** (`HEADING_MIN_SIZE = 9.5`) et non plus par casse. Résultat corrigé : **614 substances / 3 218 interactions** (`scripts/05_clean_thesaurus.py`).
- **Chunking du Thésaurus** : 1 chunk = 1 interaction (substance + cible + niveau + description + conduite à tenir + membres de classe). Métadonnées : `substance`, `cible`, `niveau`, `membres`, `voir_aussi`.
- **Chunking de la Nomenclature** : les 5 425 lignes produit ont été agrégées en **1 chunk par DCI** (1 387 chunks). Chaque chunk liste marques, formes, dosages et laboratoires. Cela supprime les quasi-doublons (ex. 55 lignes IBUPROFENE) qui noyaient la recherche, tout en conservant l'information de dosage et de marque.
- **Chunking Pharm'Net** : les 5 387 lignes `produits_enregistres.csv` sont agrégées en **1 chunk par DCI** (1 247 chunks). Chaque chunk liste la classe thérapeutique, les marques, formes, dosages, laboratoires, la liste (I/II/stupéfiant) et la fourchette de prix PPA. Les produits retirés ou non renouvelés sont exclus (filtre `registre = ENREGISTRE`).
- **EMA / DWA** : 1 chunk par médicament / par entrée de liste.
- Schéma commun : `chunk_id, doc_id, source_id, source_name, authority_rank, lang, text, metadata`. Les `chunk_id` sont rendus uniques par suffixe `#idx`.

## 3. Embeddings et base vectorielle
- Modèle : **`intfloat/multilingual-e5-small`** (384 dimensions), choisi pour rester exécutable sur CPU. Il est configurable via `EMBEDDING_MODEL`.
- Préfixes e5 respectés : `"query: "` pour les requêtes, `"passage: "` pour les chunks ; vecteurs **normalisés**.
- Index : **FAISS `IndexFlatIP`** (produit scalaire = similarité cosinus sur vecteurs normalisés), 8 247 × 384, fichier `db/index/faiss.index` (12,1 Mo).
- Temps de construction : **231 s** (embedding inclus) sur CPU ; BM25 : **0,6 s**.
- Fichiers : `faiss.index`, `chunk_ids.json`, `bm25/`.

## 4. Méthodes de recherche
- **BM25** (`bm25s`) : tokens normalisés (minuscules, sans accents), stopwords français, sans racinisation. Index lexical creux.
- **Dense** : embedding de la requête + recherche FAISS top-k.
- **Hybride** : fusion par **Reciprocal Rank Fusion** (RRF, `k = 60`) des listes BM25 et dense (`src/pharmeazor/retrieval.py`).

Latence mesurée après chargement du modèle (CPU, 20 requêtes) :

| Méthode | Latence / requête |
|---|---:|
| BM25 | 0,37 ms |
| Dense | 18,0 ms |
| Hybride | 18,1 ms |

(Le chargement initial du modèle ajoute ~10 s par processus.)

## 5. Protocole d'évaluation
- **Questions réelles** : Q1 (dosage paracétamol), Q2 (ibuprofène + aspirine), Q3 (question-test Amlodipine + Ibuprofène, multi-étapes).
- **Variante diagnostique** Q3f : version courte et ciblée de Q3, pour isoler l'effet de la formulation. Exclue de l'agrégat.
- **Q4 (méta, conflit de doses)** et **Q5 (hors périmètre, douleurs dentaires)** : pas de gold unique ; traitées qualitativement.
- **Gold** : identifiants de chunks jugés pertinents manuellement (interaction AINS + classe antihypertensive pour Q3).
- **Métriques** : Recall@10, Recall@50, Hit@10, MRR@100, nDCG@10. Top-100 classé.

## 6. Résultats

### Agrégat (Q1, Q2, Q3)

| Méthode | Recall@10 | Recall@50 | Hit@10 | MRR@100 | nDCG@10 |
|---|---:|---:|---:|---:|---:|
| BM25 | 0,083 | 0,583 | 0,333 | **0,174** | 0,082 |
| Dense | **0,333** | **0,667** | 0,333 | 0,085 | **0,129** |
| Hybride | 0,250 | 0,583 | 0,333 | 0,074 | 0,122 |

### Détail

| Question | Méthode | Recall@10 | Recall@50 | MRR | nDCG@10 |
|---|---|---:|---:|---:|---:|
| Q1 | BM25 | 0,000 | 1,000 | 0,021 | 0,000 |
| Q1 | Dense | **1,000** | 1,000 | **0,200** | **0,387** |
| Q1 | Hybride | 0,000 | 1,000 | 0,067 | 0,000 |
| Q2 | BM25 | 0,000 | 0,000 | 0,000 | 0,000 |
| Q2 | Dense | 0,000 | 0,500 | 0,020 | 0,000 |
| Q2 | Hybride | 0,000 | 0,000 | 0,012 | 0,000 |
| Q3 | BM25 | 0,250 | 0,750 | **0,500** | 0,246 |
| Q3 | Dense | 0,000 | 0,500 | 0,034 | 0,000 |
| Q3 | Hybride | **0,750** | 0,750 | 0,143 | **0,366** |
| Q3f (variante) | BM25 | 0,250 | 1,000 | 0,500 | 0,246 |
| Q3f (variante) | Dense | 0,250 | 1,000 | 0,500 | 0,246 |
| Q3f (variante) | Hybride | 0,250 | 1,000 | **1,000** | **0,390** |

Le détail complet (composition des sources dans le top-10, requêtes Q4/Q5) est dans `data/processed/week_2/retrieval_comparison.md`.

## 7. Analyse

**Ce qui marche**
- **Dense** est le plus robuste sur les reformulations et les questions « métier » : Q1 (`dosage` ↔ `dosages`, chunk long) est trouvé au rang 5 (MRR 0,20), là où BM25 échoue à cause de la normalisation par longueur du chunk agrégé.
- **BM25** est excellent quand les termes rares sont présents tels quels : sur Q3 il place la bonne classe d'interaction au rang 2 (MRR 0,50) et reste très rapide (< 1 ms).
- **L'hybride RRF** est le meilleur sur la **vraie question-test Q3** : 3 des 4 chunks gold dans le top-10 (Recall@10 = 0,75, nDCG = 0,366), contre 0,25 pour BM25 et 0 pour le dense. Sur la variante ciblée Q3f, il place un chunk pertinent au **rang 1** (MRR = 1,0). La complémentarité lexicale/sémantique est donc réelle.
- **Pharm'Net apporte le catalogue algérien** : il apparaît dans le top-10 de Q1 (2 à 4 chunks) et de Q2 (5 à 6 chunks), mais comme source de catalogue (rang 1) il ne remplace pas le Thésaurus pour les interactions.

**Ce qui échoue (et pourquoi)**
- **Q2 : fossé synonymique.** La requête dit « aspirine » et « ibuprofène », les chunks disent `ACIDE ACÉTYLSALICYLIQUE` et `ANTI-INFLAMMATOIRES NON STÉROÏDIENS`. Aucune méthode ne relie les deux au top-10 ; le dense ne compense qu'en partie (Recall@50 = 0,5). C'est le cas typique que la normalisation d'entités (Semaine 3) doit résoudre.
- **Q3 : dilution de la requête longue.** Le dense, noyé par une question multi-étapes, descend sous le rang 10 ; BM25 résiste mieux car il s'accroche aux termes rares de classe. D'où l'intérêt de **décomposer** la question (Semaine 4).
- **Q1 : longueur des chunks agrégés.** BM25 pénalise le chunk DCI très long (liste de marques/dosages), d'où un rang ~48 malgré un terme quasi unique.
- **Q5 hors périmètre :** les trois méthodes renvoient des chunks thérapeutiques avec des scores non nuls (topotécane, laxatifs, anticholinestérasiques, et `mepivacaine` côté Pharm'Net, un anesthésique dentaire). Il faut un **seuil de pertinence / détecteur hors-sujet** avant toute génération (Semaine 4).
- **Q4 conflit de doses :** aucune méthode ne peut arbitrer seule ; c'est un traitement de méta-raisonnement (comparer les sources, `authority_rank`, dates).

**Résultat négatif documenté** : l'ajout d'une racinisation française (PyStemmer) a **dégradé** BM25 (Recall@10 0,125 → 0,062) car `associer`/`association` convergent vers `associ` et saturent la requête longue. Expérience annulée et code reverté.

**Limite statistique** : avec 3 questions réelles, les écarts agrégés ne sont qu'indicatifs. Le signal le plus solide est le comportement par question (Q1 dense, Q3 hybride).

## 8. Prochaines étapes
- **Semaine 3** : normalisation d'entités et synonymes (marques → DCI, aspirine → acide acétylsalicylique, ibuprofène → AINS), extraction des entités de la question, graphe substance ↔ classe pour relier **Amlodipine → antihypertenseur → interaction AINS**.
- **Semaine 4** : RAG avec citations, seuil d'abstention (Q5), gestion des conflits de sources (Q4), décomposition des questions multi-étapes.
- **Améliorations optionnelles** : reranker cross-encoder, modèle d'embedding plus fort (BGE-M3) si GPU, réglage du paramètre `b` de BM25, pondération de l'hybride.

## 9. Reproductibilité
```powershell
.venv\Scripts\python.exe scripts\05_clean_thesaurus.py
.venv\Scripts\python.exe scripts\07_build_corpus.py
.venv\Scripts\python.exe scripts\08_build_index.py
.venv\Scripts\python.exe scripts\09_eval_retrieval.py
```
Environnement : Python 3.12.16, `sentence-transformers==6.3.0`, `faiss-cpu==1.16.0`, `bm25s==0.3.16`, `torch` CPU.

## 10. Contribution des membres
- **[Membre 1]** : correction du parsing Thésaurus, découpage, rapport.
- **[Membre 2]** : embeddings, index FAISS/BM25, évaluation.
- *(Ajoutez vos noms)*
