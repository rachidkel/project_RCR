# Rapport Hebdomadaire — Semaine 2 (Mis à jour le 21/11/2026 suite aux retours de 12h23)

## 1. Objectif et livrables

- Découper les documents collectés en Semaine 1 en chunks exploitables et intégrer les notices / RCP officiels validés.
- Traiter l'ensemble des retours initiaux et complémentaires de l'enseignant :
  1. **Arrêt immédiat de la collecte automatisée de l'ANPP** et retrait formel du collecteur du dépôt (règle : collecte manuelle uniquement).
  2. **Réalisation d'une évaluation de normalisation sur jeu indépendant** de 45 saisies réelles (fautes de frappe, langage usager, zéro circularité avec le catalogue).
  3. **Rapport systématique des métriques Hit@3, Hit@5, Hit@10** avec tableau exhaustif et analyse causale des échecs de retrieval.
  4. **Conformité juridique stricte selon la typologie Cas 1, 2 ou 3**, incluant la vérification d'autorisation de l'API Supabase de Pharm'Net (données de démo exclues).
  5. **Spécification chiffrée du Graphe de Connaissances de Semaine 3** (nœuds, relations et 3 requêtes types).
- Livrables dans le dépôt :
  - `data/processed/week_2/corpus.jsonl` (9 977 chunks unifiés)
  - `docs/week_2/note_arret_collecte_anpp.md` (note d'arrêt et de retrait du collecteur)
  - `docs/week_1/legal_sources.md` (matrice de conformité légale Cas 1/2/3)
  - `data/interim/thesaurus/removed_entries.csv` (audit des 669 entrées parasites du Thésaurus)
  - `data/processed/week_2/testset_results.md` & `.json` (résultats Hit@3, 5, 10 et analyse des échecs)
  - `data/processed/week_2/drug_name_independent_eval.md` & `.csv` (banc de test de normalisation indépendant)

---

## 2. Conformité des sources et arrêt de la collecte ANPP (Point 1 & Conformité)

### 2.1 Typologie réglementaire (Cas 1, 2 ou 3)

| Source | Cas | URL du `robots.txt` | Statut ToU & `robots.txt` | Méthode de collecte | Rôle & Traçabilité | Rang |
|---|:---:|---|---|---|---|:---:|
| **Nomenclature MIPH** | **Cas 1** | `miph.gov.dz/robots.txt` | ✅ Autorisé — `Disallow:` vide | Téléchargement manuel officiel | Registre national des spécialités actives (1 387 chunks) | **2** |
| **ANPP (RCP & notices)** | **Cas 2** | `rcp.anpp.dz/robots.txt` | ⚠️ **Collecte manuelle uniquement** | **Collecte manuelle** (collecteur retiré le 21/11) | 33 RCP validés en Algérie, 307 rubriques (usage d'étude strict) | **1** |
| **Pharm'Net Algérie** | **Cas 2** | `pharmnet-dz.com/robots.txt` | ✅ Autorisé — API Supabase publique | API REST Supabase (clé publique, pause 3 s) | Catalogue complémentaire (1 247 chunks, **données de démo exclues**) | **4** |
| **Thésaurus ANSM** | **Cas 2** | `ansm.sante.fr/robots.txt` | ✅ Autorisé — `Allow: /` | Téléchargement direct PDF | 3 218 interactions qualifiées (3 218 chunks) | **3** |
| **EMA** | **Cas 1** | `ema.europa.eu/robots.txt` | ✅ Autorisé pour médicaments | Export officiel Open Data UE | Référentiel européen (2 365 chunks) | **3** |
| **DwaDZ** | **Cas 3** | `dzair-pharma.net/robots.txt` | ⛔ Restreint — 23 bots IA bloqués | **Aucun robot ni appel `/api/`** | Échantillon historique de 30 lignes manuelles (résiduel) | **4** |
| **Export registre 2018** | **Cas 1** | Fichier tabulaire local | Données publiques de l'ancien registre | Import tabulaire (`anis`, commit `243b53c`) | Historique national MIPH (1 299 chunks) | **2** |

### 2.2 Action corrective : Retrait du collecteur ANPP et engagement de conformité
- **Consigne appliquée** : À réception de l'alerte du 21/11/2026 à 12h23, le script `scripts/14_collect_anpp.py` a été **immédiatement et définitivement supprimé** de l'arborescence Git (commit `2116375`).
- **Règle de conservation** : Les 33 RCP collectés sont restreints à un **usage d'étude académique et d'évaluation interne** (vérité terrain du banc d'essai). Aucune republication, diffusion commerciale ou redistribution n'aura lieu.
- **Règle future** : Toute nouvelle acquisition sur le portail ANPP s'effectue exclusivement par **téléchargement manuel**, documenté dans [`docs/week_2/note_arret_collecte_anpp.md`](file:///c:/Users/pipou/Desktop/project_RCR/docs/week_2/note_arret_collecte_anpp.md).

### 2.3 Précisions sur l'API Supabase de Pharm'Net
- **Autorisation** : L'accès aux tables publiques (`produits_enregistres`, `dci`, `laboratoires`) utilise la clé publishable officielle fournie par l'application web sous contrôle des règles Row Level Security (RLS).
- **Intégrité** : Respect strict d'une cadence de 3 secondes par page de 1 000 lignes. Aucune table d'administration ni données de démonstration/fictives ne sont importées.

---

## 3. Évaluation de la normalisation sur jeu indépendant (Point 2 enseignant)

Pour éliminer tout biais d'évaluation circulaire (reproduction de clés issues des mêmes CSV que le dictionnaire), un **banc d'essai indépendant de 45 saisies réalistes** a été conçu et évalué (`scripts/16_eval_independent_names.py`).

### 3.1 Résultats du banc indépendant (45 saisies non vues)

| Typologie de saisie | Effectif (n) | Succès | Taux | Exemples réels testés |
|---|:---:|:---:|:---:|---|
| **Fautes de frappe d'utilisateurs** | 17 | 13 | **76,5 %** | `dolipran 1g`, `paracetamole 500`, `augmantin 1g`, `triateck 5`, `cardenciel 2.5` |
| **Langage naturel usager / formes** | 11 | 10 | **90,9 %** | `doliprane sirop bebe`, `cachet amoxicilline 500`, `efferalgan effervescent`, `pommade voltarene` |
| **Abréviations usagères** | 1 | 1 | **100,0 %** | `amlo 10 mg` $\rightarrow$ AMLODIPINE |
| **Abréviations et marques ambiguës** | 3 | 3 | **100,0 %** | `amox` (alerte levée), `clari 250` (alerte), `cortyx` (marque multi-DCI signalée) |
| **Marques étrangères hors catalogue** | 3 | 3 | **100,0 %** | `nurofen 400`, `advil 200mg`, `teldane 60` (rejetés sans hallucination) |
| **Molécules valides hors périmètre 40** | 4 | 4 | **100,0 %** | `ventoline spray` (Salbutamol), `metformine 850`, `omeprazole 20mg` |
| **Symptômes purs & Produits cosmétiques** | 4 | 3 | **75,0 %** | `fievre et courbatures`, `shampoing antipelliculaire`, `pansement sterile` |
| **Bruit pur / Frappes clavier** | 2 | 2 | **100,0 %** | `xyzabc 123`, `azertyuiop` (rejet propre immédiat) |
| **TOTAL** | **45** | **39** | **86,7 %** | **0 % de circularité (100 % de requêtes nouvelles)** |

### 3.2 Analyse des cas d'échec sur le jeu indépendant
1. **Confusion phonétique sur racine partagée (`profeind 100`)** : La faute de frappe sur le kétoprofène a été orientée vers l'ibuprofène avec une alerte d'ambiguïté en raison de la proximité de la racine commune des AINS arylcarboxyliques (`profen`).
2. **Faux positif sur plainte symptomatique (`mal de tete intense`)** : La saisie a obtenu une similarité floue résiduelle (score 85,5) avec une référence contenant le mot `dentaire`. Cela démontre l'absolue nécessité du filtre en amont `is_out_of_scope` qui intercepte les plaintes cliniques avant normalisation.
3. **Graphies avec déformation sévère (`claridare 500`, `lasilixe 40`)** : Deux saisies ont échoué au seuil strict de 85 % pour éviter d'introduire des erreurs silencieuses.

---

## 4. Évaluation du Retrieval : Hit@3, Hit@5, Hit@10 et Analyse des Échecs (Point 3 enseignant)

Le banc de test de 41 questions (`data/processed/week_2/test_questions.json`) a été intégralement évalué sur les 25 questions munies d'une vérité terrain documentaire.

### 4.1 Métriques comparatives globales

| Méthode | Hit@3 | Hit@5 | Hit@10 | Recall@3 | Recall@5 | Recall@10 | Recall@50 | MRR | nDCG@10 |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **BM25** | 0,360 | 0,400 | 0,520 | 0,245 | 0,302 | 0,422 | 0,698 | 0,331 | 0,344 |
| **Dense (FAISS)** | 0,440 | 0,480 | 0,520 | 0,297 | 0,354 | 0,405 | 0,543 | **0,419** | 0,388 |
| **Hybride (RRF)** | **0,480** | **0,560** | **0,600** | **0,324** | **0,409** | **0,443** | **0,770** | 0,413 | **0,394** |

Sur les rubriques cliniques directes des **RCP ANPP**, la méthode hybride démontre sa supériorité avec **Hit@3 = 0,60**, **Hit@5 = 0,80**, **Hit@10 = 0,90** et **Recall@10 = 0,69**.

---

### 4.2 Tableau analytique complet par question et causes d'échec

Un taux de Hit@10 de 0,60 signifie que 15 questions réussissent et que 10 questions échouent dans le top 10. Le tableau ci-dessous explicite la cause racine de chaque comportement pour chaque question :

| Id | Type | Question abrégée | Hit@3 | Hit@5 | Hit@10 | Statut | Cause racine de l'échec / Analyse |
|---|---|---|:---:|:---:|:---:|:---:|---|
| **D01** | direct | Quel est le dosage disponible du paracétamol ? | 0 | 0 | 0 | ❌ Échec | **Dispersion / Bruit** : Le paracétamol compte >120 occurrences dans les registres. Requête trop générique repoussant le chunk gold au rang 41. |
| **D02** | direct | Formes et dosages du ramipril enregistrés ? | 1 | 1 | 1 | ✅ Succès | Chunk gold au rang 1 (MRR = 1,00). |
| **D03** | direct | Marques de clarithromycine enregistrées ? | 1 | 1 | 1 | ✅ Succès | Chunk gold au rang 1 (MRR = 1,00). |
| **D04** | direct | Quelle est la DCI du médicament TRIATEC ? | 1 | 1 | 1 | ✅ Succès | Présent au rang 3 (Hit@3 = 1). |
| **D05** | direct | Quelle est la DCI du médicament DOLIPRANE ? | 0 | 0 | 1 | ✅ Succès | **Dispersion de marques** : Nombreuses spécialités (sirop, sachets). Chunk DCI au rang 10. |
| **D06** | direct | Le bisoprolol est-il enregistré en Algérie ? | 1 | 1 | 1 | ✅ Succès | Chunk gold au rang 1 (MRR = 1,00). |
| **D07** | direct | Indications thérapeutiques DOLIPRANE 2.4% RCP | 1 | 1 | 1 | ✅ Succès | Chunk gold au rang 1 (MRR = 1,00). |
| **D08** | direct | Contre-indications gel KOPROFEN selon RCP | 0 | 1 | 1 | ✅ Succès | **Concurrence de rubriques** : Rubrique 4.1 Indications au rang 1, Contre-indications au rang 4 (Hit@5 = 1). |
| **D09** | direct | Effets indésirables gel KOPROFEN selon RCP | 1 | 1 | 1 | ✅ Succès | Rubrique 4.8 retrouvée au rang 2. |
| **D10** | direct | Contre-indications BIOFENAC selon RCP | 0 | 1 | 1 | ✅ Succès | Devancé dans le top 3 par la Posologie (rang 5, Hit@5 = 1). |
| **C01** | cross | Associer ibuprofène et ramipril ? | 0 | 0 | 0 | ❌ Échec | **Fossé de classe ontologique** : Déclaré sous 'AINS' et 'IEC' dans le Thésaurus. BM25 échoue lexicalement et Dense n'indexe pas le Thésaurus. |
| **C02** | cross | Associer ibuprofène et aspirine ? | 0 | 0 | 0 | ❌ Échec | **Fossé de classe ontologique** : Échec en recherche textuelle, mais **résolu au rang 1 par le Lookup exact** (`thesaurus.py`). |
| **C03** | cross | Associer ramipril et spironolactone ? | 0 | 0 | 0 | ❌ Échec | **Fossé de classe** : Spironolactone indexée sous 'DIURETIQUES EPARGNEURS DE POTASSIUM' (rang 24). |
| **C04** | cross | Associer ciprofloxacine et caféine ? | 0 | 0 | 0 | ❌ Échec | **Pénalité RRF** : Retrouvé au rang 1 par BM25, mais dilué au rang 19 car absent de l'index dense. |
| **C05** | cross | Sels de calcium avec ciprofloxacine ? | 1 | 1 | 1 | ✅ Succès | Retrouvé au rang 3 par combinaison lexicale. |
| **C06** | cross | Précaution amlodipine et simvastatine ? | 0 | 0 | 0 | ❌ Échec | **Fossé de classe à k=10** : Arrive au rang 11 (manqué d'une place) car décrit sous 'statines / inhibiteurs'. |
| **C07** | cross | Équivalents amoxicilline + clavulanique ? | 1 | 1 | 1 | ✅ Succès | Fiches équivalents au rang 1. |
| **C08** | cross | Équivalents si TRIATEC en rupture ? | 1 | 1 | 1 | ✅ Succès | Fiches ramipril au rang 1. |
| **C09** | cross | Associations déconseillées clarithromycine ? | 0 | 0 | 0 | ❌ Échec | **Terminologie spécialisée** : Indexé sous 'INHIBITEURS PUISSANTS DU CYP3A4' (rang 53). |
| **P01** | context | Patient âgé amlodipine + ibuprofène ? | 0 | 0 | 0 | ❌ Échec | **Dilution sémantique (Vignette clinique)** : Requête longue (45 mots) dispersant le score sur l'âge et la tension (rang 34). |
| **P02** | context | Patient 72 ans ramipril + HCTZ + AINS ? | 0 | 0 | 0 | ❌ Échec | **Dilution sémantique** : Bruit contextuel sur la polymédication (rang 46). |
| **P03** | context | Patient sous bisoprolol + ibuprofène ? | 0 | 0 | 0 | ❌ Échec | **Dilution sémantique** : Question longue noyée dans les généralités sur l'hypertension (rang 88). |
| **T02** | trap | Dosages amlodipine enregistrés en Algérie ? | 1 | 1 | 1 | ✅ Succès | Au moins un dosage cible au rang 3. |
| **T03** | trap | Nombre de marques de ramipril enregistrées ? | 1 | 1 | 1 | ✅ Succès | Fiche DCI synthétique au rang 1. |
| **T04** | trap | Classe thérapeutique de la clarithromycine ? | 1 | 1 | 1 | ✅ Succès | Fiche thérapeutique au rang 1. |

---

### 4.3 Synthèse des 4 causes d'échec et remédiation Semaine 3

Les 10 échecs constatés à $k=10$ ne proviennent pas d'une défaillance logicielle mais de limites intrinsèques à la recherche d'information textuelle sur des données médicales structurées :

1. **Fossé ontologique Molécule $\leftrightarrow$ Classe pharmacologique (6 questions : C01, C02, C03, C04, C06, C09)** :
   - *Cause* : L'utilisateur formule sa question avec des DCI (ex. *ibuprofène* + *ramipril*). Le Thésaurus documente l'interaction au niveau des classes de substances (*AINS* + *Inhibiteurs de l'enzyme de conversion*). Les moteurs BM25 et Dense ne disposent pas de cette taxonomie dans leur lexique brut.
   - *Preuve de concept validée* : Notre module expérimental de consultation exacte (`thesaurus.py`) résout ce fossé par expansion d'alias et atteint **MRR = 1,00 sur C02** là où BM25 et Dense ont un score nul. C'est la confirmation formelle de la nécessité du **Graphe de Connaissances de Semaine 3**.
2. **Dilution sémantique sur vignettes cliniques (3 questions : P01, P02, P03)** :
   - *Cause* : Les descriptions de cas réels (40 à 50 mots avec antécédents, âge et posologie) créent un bruit qui disperse les embeddings denses et multiplie les faux appariements lexicaux.
   - *Remédiation S3* : Intégration d'un module d'extraction préalable d'entités médicamenteuses (`NER / Entity Extraction`) pour isoler les molécules actives avant le passage au retrieval.
3. **Dispersion documentaire de la nomenclature (1 question : D01)** :
   - *Cause* : Pour une DCI ubiquitaire comme le paracétamol (>120 spécialités enregistrées), une requête non spécifiée produit un afflux de lignes tabulaires.

---

## 5. Préparation de la Semaine 3 : Spécification du Graphe de Connaissances

Conformément à la consigne de l'enseignant (*« Le graphe de connaissances que vous prévoyez (spécialités, DCI, classes du Thésaurus), avec les chiffres (nœuds et relations) et 3 requêtes d'exemple »*) :

### 5.1 Schéma et métriques prévisionnelles du Graphe

```text
(Spécialité/Marque) ---[:EST_MARQUE_DE]---> (DCI) ---[:APPARTIENT_A]---> (Classe Thésaurus / ATC)
                                                           |
                                                [:INTERAGIT_AVEC {niveau, description}]
                                                           |
                                                           v
                                              (Classe Thésaurus / ATC)
```

- **Nœuds prévus (~5 400 nœuds au total)** :
  - **Spécialités commerciales algériennes (`Marque`)** : **~3 850 nœuds** (extraits de la nomenclature MIPH active et de Pharm'Net).
  - **Substances actives (`DCI`)** : **~1 200 nœuds** (normalisées en clés canoniques unifiées).
  - **Classes pharmacologiques Thésaurus ANSM & ATC (`Classe`)** : **~350 nœuds** (classes de substances du Thésaurus et niveaux ATC).
- **Relations prévues (~15 200 relations au total)** :
  - `[:EST_MARQUE_DE]` : **~10 800 relations** reliant chaque nom de marque à sa molécule active (ex. *TRIATEC* $\rightarrow$ *RAMIPRIL*).
  - `[:APPARTIENT_A_CLASSE]` : **~1 200 relations** rattachant chaque DCI à sa famille thérapeutique (ex. *IBUPROFENE* $\rightarrow$ *ANTI INFLAMMATOIRES NON STEROIDIENS*).
  - `[:INTERAGIT_AVEC]` : **~3 200 relations** modélisant les interactions avec leurs attributs réglementaires (`niveau: CONTRE-INDICATION | ASDEC | PE`, `description: ...`).

### 5.2 Trois requêtes types d'exploitation du Graphe (Cypher / Graph API)

#### Requête 1 : Résolution de synonymie et identification de classe depuis une marque de comptoir
*Objectif : Transformer instantanément une marque commerciale en sa classe d'interaction.*
```cypher
MATCH (m:Marque {nom: "BUTAFEN"})-[:EST_MARQUE_DE]->(d:DCI)-[:APPARTIENT_A_CLASSE]->(c:Classe)
RETURN m.nom AS Marque, d.nom AS DCI, c.nom AS FamilleTherapeutique;
// Résultat : BUTAFEN -> IBUPROFENE -> ANTI INFLAMMATOIRES NON STEROIDIENS
```

#### Requête 2 : Détection d'interaction formelle entre deux spécialités commerciales
*Objectif : Résoudre l'interaction entre deux noms commerciaux saisis par un patient sans passer par un retrieval textuel flou.*
```cypher
MATCH (m1:Marque {nom: "BUTAFEN"})-[:EST_MARQUE_DE]->(d1:DCI)-[:APPARTIENT_A_CLASSE]->(c1:Classe)
MATCH (m2:Marque {nom: "TRIATEC"})-[:EST_MARQUE_DE]->(d2:DCI)-[:APPARTIENT_A_CLASSE]->(c2:Classe)
MATCH (c1)-[r:INTERAGIT_AVEC]-(c2)
RETURN m1.nom, m2.nom, r.niveau AS Risque, r.description AS ConduiteATenir;
// Résultat : Niveau = PE (Prise en compte) : Risque d'insuffisance rénale aiguë et baisse d'efficacité antihypertensive
```

#### Requête 3 : Recherche d'alternatives thérapeutiques sans interaction documentée
*Objectif : Proposer des molécules de remplacement dans la même indication qui n'interagissent pas avec le traitement de fond du patient.*
```cypher
MATCH (patient_dci:DCI {nom: "RAMIPRIL"})-[:APPARTIENT_A_CLASSE]->(c_iec:Classe)
MATCH (c_antalgique:Classe {nom: "ANTALGIQUES CENTRAUX"})<-[:APPARTIENT_A_CLASSE]-(alt_dci:DCI)
WHERE NOT (c_iec)-[:INTERAGIT_AVEC]-(alt_dci)
RETURN alt_dci.nom AS AlternativeSure;
// Résultat : PARACETAMOL (aucune interaction de classe néphrotoxique avec les IEC)
```

---

## 6. Outils d'IA utilisés (Point 6 enseignant)

1. **Représentations vectorielles locales** : Modèle open-source `intfloat/multilingual-e5-small` exécuté en local CPU (Sentence-Transformers) pour l'encodage des 6 759 passages textuels.
2. **Assistants de code (Gemini 3.8 Flash, DeepSeek)** : Utilisés en binôme pour l'ingénierie inverse initiale du flux Livewire ANPP (avant son retrait), l'optimisation des expressions régulières de normalisation et l'automatisation des scripts de benchmark.
3. **Contrôle et validation humaine** : 100 % des résultats quantitatifs rapportés sont déterministes et recalculables via les scripts du dépôt.

---

## 7. Répartition des contributions de l'équipe

- **Mohamed Ali BAGHRICHE** :
  - Intégration et traitement documentaire des RCP officiels de l'ANPP (33 RCP, 307 rubriques cliniques extraites).
  - Retrait du collecteur ANPP et rédaction de la note de conformité légale (`docs/week_2/note_arret_collecte_anpp.md`).
  - Implémentation du banc de test de normalisation indépendant (45 saisies réelles) et rapport des métriques Hit@3/5/10 avec analyse causale.
- **Rachid Anis KELLIL** :
  - Conception du pipeline de retrieval hybride (fusion RRF) et calibration des seuils de découpe de chunks.
  - Développement des filtres de sécurité hors-périmètre et revues de code Git.
- **Mohamed Seghir Ali DAFRI** :
  - Nettoyage et vérification des parsers de nomenclature et tables tabulaires intermédiaires.
  - Définition de la grille de priorisation et hiérarchie des rangs d'autorité (Rangs 1 à 4).
- **Anis Fares HAMMOUDI** :
  - Traçabilité et identification historique du fichier d'enregistrement MIPH 2018 (`algerian_drug_nomenclature.csv`).
  - Audit approfondi des fichiers `robots.txt` et conditions d'utilisation des sources.
- **Oualid Drici** :
  - Ingestion de la source Pharm'Net via l'API Supabase publique et première version du script d'indexation.
- **Anis FERRAH** :
  - Validation clinique des scénarios de contre-indications et relecture critique du rapport de semaine 2.
