# Section 3 — Analyse Sémantique de Requête (Lot L2)

**Auteur** : Mohamed Ali BAGHRICHE (moh bgh)  
**Livrables** : `src/pharmeazor/query.py`, `scripts/11_analyze_query.py`, `tests/test_query.py`  
**Relecteur assigné** : Rachid Anis KELLIL (rachid)  

---

## 3.1 Objectif et responsabilités du Lot L2

Le module d'analyse de requête (`src/pharmeazor/query.py`) constitue la passerelle entre le langage naturel saisi par l'utilisateur et les moteurs de recherche enrichis (retrieval hybride L4, graphe de connaissances L3).

Ses responsabilités opérationnelles sont :
1. **Extraction d'entités pharmaceutiques par plus long match (`longest-match`)** : identification glissante sur le lexique unifié L1 (`lexicon.json`, 7 069 alias et 171 classes) avec gestion native des élisions françaises (`l'Amlodipine` $\rightarrow$ `Amlodipine`).
2. **Repli flou maîtrisé (`fuzzy fallback`)** : rattrapage des coquilles usagers par `rapidfuzz` (seuil de similarité $\ge 85\,\%$) avec protection stricte contre les faux positifs sur les mots du langage courant.
3. **Classification d'intention clinique** : orientation déterministe parmi 6 intentions (`dosage`, `interaction`, `contraindication`, `price`, `out_of_scope`, `unknown`).
4. **Filtrage des garde-fous déontologiques (`out_of_scope`)** : détection immédiate des demandes de diagnostic, d'ordonnance, d'avis pédiatriques personnalisés ou de questions non médicales.
5. **Expansion sémantique ordonnée (`expanded_terms`)** : génération des DCI canoniques, classes pharmacologiques parentes et mots-clés d'intention pour le reranking.
6. **Contrainte de latence industrielle** : exécution en **< 5 ms** par requête sans dépendance aux modèles neuronaux lourds.

---

## 3.2 Architecture des données et interface figée

Conformément à l'interface gelée le lundi 24/11 à 09h00 :

```python
@dataclass(frozen=True)
class Entity:
    term: str             # Terme brut extrait dans la requête
    dci: str | None       # DCI canonique unifiée (ex. 'PARACETAMOL')
    classes: list[str]    # Classes pharmacologiques Thésaurus / ATC
    confidence: float     # Score de confiance (1.0 exact, >= 0.85 flou)
    start: int            # Indice de début dans le texte brut
    end: int              # Indice de fin dans le texte brut

@dataclass(frozen=True)
class QueryAnalysis:
    raw: str                     # Requête textuelle originale
    normalized: str              # Requête normalisée (minuscules, sans accents)
    entities: list[Entity]       # Liste ordonnée des entités extraites
    intent: str                  # Intention ('dosage', 'interaction', etc.)
    expanded_terms: list[str]    # Termes pour l'enrichissement documentaire
    out_of_scope: bool           # Booléen de refus déontologique immédiat
```

---

## 3.3 Algorithme d'analyse pas à pas

```text
Texte brut utilisateur
       │
       ▼
1. Tokenisation & Découpage avec offsets réels (gestion l', d', qu')
       │
       ▼
2. Fenêtre glissante Longest-Match (6 tokens -> 1 token)
       ├─ Si match exact dans lexicon.json ──────► Entité validée (confiance 1.0)
       └─ Si token non consommé (len >= 4)
             et hors NON_DRUG_WORDS ─────────────► Repli flou RapidFuzz (>= 85%)
       │
       ▼
3. Analyse des Garde-fous (MEDICAL_ADVICE_PATTERNS & Symptômes isolés)
       ├─ Conseil médical / Ordonnance / Symptôme seul ─► out_of_scope = True
       └─ Requête d'information pharmaceutique ──────────► out_of_scope = False
       │
       ▼
4. Détection d'Intention clinique (Règles regex + Heuristique multi-entités)
       │
       ▼
5. Expansion sémantique (DCI + Composants d'association + Classes parentes + Intent)
       │
       ▼
QueryAnalysis prête en < 1 ms
```

---

## 3.4 Validation des critères d'acceptation (Acceptance Criteria)

| Critère d'acceptation | Requête testée | Résultat obtenu | Statut |
|---|---|---|:---:|
| **Résolution de Doliprane** | `"Quel est le dosage de Doliprane ?"` | `entity.dci == "PARACETAMOL"`, `confidence == 0.98`, `out_of_scope == False` | ✅ Validé |
| **Résolution de l'aspirine** | `"Est-ce que l'aspirine est un AINS ?"` | `entity.dci == "ACIDE ACETYLSALICYLIQUE"`, classe `ANTI-INFLAMMATOIRES NON STEROIDIENS` présente dans `classes` et `expanded_terms` | ✅ Validé |
| **Garde-fou douleurs dentaires** | `"Quel médicament prendre pour mes douleurs dentaires ?"` | `out_of_scope == True`, `intent == "out_of_scope"` | ✅ Validé |
| **Latence & Robustesse** | 100 requêtes consécutives + termes inconnus | **0,18 ms** de latence moyenne (seuil : < 5 ms), **zéro crash** sur chaînes vides, bruit pur ou ponctuation | ✅ Validé |

---

## 3.5 Exemples concrets d'exécution (Questions Q1 à Q5 du projet)

### Exemple 1 : Interaction multi-entités (Q3)
* **Requête** : `Peut-on associer l'Amlodipine et l'Ibuprofène ?`
* **Intention** : `INTERACTION` | **Hors périmètre** : `False` | **Latence** : `0,21 ms`
* **Entités** :
  1. `"Amlodipine"` [19:29] $\rightarrow$ DCI: `AMLODIPINE`, Classes: `ANTAGONISTES DES CANAUX CALCIQUES`, `ANTIHYPERTENSEURS`
  2. `"Ibuprofène"` [35:45] $\rightarrow$ DCI: `IBUPROFENE`, Classes: `ANTI-INFLAMMATOIRES NON STEROIDIENS`, `HYPERKALIEMIANTS`
* **Termes d'expansion générés** :
  `['AMLODIPINE', 'IBUPROFENE', 'ANTAGONISTES DES CANAUX CALCIQUES', 'INHIBITEURS CALCIQUES', 'ANTIHYPERTENSEURS SAUF ALPHA-BLOQUANTS', 'ANTI-INFLAMMATOIRES NON STEROIDIENS', 'AINS', 'HYPERKALIEMIANTS', 'INTERACTION MEDICAMENTEUSE']`

### Exemple 2 : Posologie pédiatrique / adulte (Q1)
* **Requête** : `Quel est le dosage disponible du paracétamol ?`
* **Intention** : `DOSAGE` | **Hors périmètre** : `False`
* **Entité** : `"paracétamol"` $\rightarrow$ DCI: `PARACETAMOL`
* **Termes d'expansion** : `['PARACETAMOL', 'POSOLOGIE', 'DOSAGE']`

### Exemple 3 : Interception de conseil médical (Q5)
* **Requête** : `Quel médicament prendre pour mes douleurs dentaires ?`
* **Intention** : `OUT_OF_SCOPE` | **Hors périmètre** : `True` (Refus immédiat)
* **Comportement** : Aucune hallucination de prescription ; interception déontologique en amont du retrieval.

---

## 3.6 Résultats de la suite de tests (`tests/test_query.py`)

Une suite exhaustive de **17 tests unitaires** valide l'intégralité des fonctionnalités :
```powershell
.venv\Scripts\pytest tests/test_query.py -v
# 17 passed in 0.56s
```
L'intégration globale du dépôt totalise **44 tests verts** (`test_lexicon.py`, `test_query.py`, `test_retrieval.py`) sans aucune régression.

---

## 3.7 Commandes reproductibles (CLI)

```powershell
# Analyse textuelle détaillée
.venv\Scripts\python.exe scripts\11_analyze_query.py "Peut-on associer l'Amlodipine et l'Ibuprofène ?"

# Sortie JSON structurée pour les scripts d'évaluation et de benchmark
.venv\Scripts\python.exe scripts\11_analyze_query.py --json "Quelles sont les contre-indications du gel KOPROFEN ?"

# Démonstration automatique sur 6 requêtes types
.venv\Scripts\python.exe scripts\11_analyze_query.py --demo
```
