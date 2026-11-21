# Conformité et légalité des sources — Pharmeazor

Mise à jour du **21/11/2026** (suite aux retours enseignants du 21/11 à 12h23).

---

## 1. Typologie réglementaire appliquée (Cas 1, 2 ou 3)

Conformément au cadre méthodologique du projet RCR :
* **Cas 1 — Données ouvertes et officielles** : Publications d'autorité publique, domaine public ou licences ouvertes autorisant la réutilisation libre (ex. Nomenclature MIPH, EMA, DailyMed).
* **Cas 2 — Données consultables sous conditions d'usage professionnel** : Portails et bases documentaires publiques sans licence d'open data explicite mais d'accès libre pour information, nécessitant le respect strict des conditions techniques (cadence, pas de surcharge) et une consultation appropriée (ex. Pharm'Net via API publique, Thésaurus ANSM, ANPP en consultation manuelle).
* **Cas 3 — Données protégées ou à accès restreint / interdiction des agents IA** : Sites interdisant explicitement les robots d'indexation ou les agents IA commerciaux (ex. DwaDZ / `dzair-pharma.net` avec 23 robots IA bloqués dans `robots.txt`). Tout crawl automatisé est strictement proscrit ; seul un usage manuel restreint avec citation d'origine est toléré.

---

## 2. Tableau récapitulatif de conformité

| Source | Cas | URL du `robots.txt` | Autorisation ToU & `robots.txt` | Méthode de collecte autorisée | Collectée dans le dépôt ? | Date de vérification |
|---|:---:|---|---|---|:---:|:---:|
| **Nomenclature nationale — MIPH** | **Cas 1** | `miph.gov.dz/robots.txt` | ✅ Autorisé — `User-agent: *` / `Disallow:` vide. Publication officielle du Ministère de l'Industrie Pharmaceutique | Téléchargement manuel direct du fichier officiel | Oui (`nomenclature_active.csv`, `retraits.csv`, `non_renouveles.csv`) | 20/11/2026 |
| **ANPP (RCP / notices)** | **Cas 2** | `rcp.anpp.dz/robots.txt` | ⚠️ **Collecte manuelle uniquement** (règle formelle enseignant du 21/11). `robots.txt` ouvert mais tout collecteur scripté est banni du projet | **Téléchargement manuel uniquement** (script automatisé retiré le 21/11) | Oui : 33 RCP PDF (usage d'étude restreint, aucune republication) | 21/11/2026 |
| **Pharm'Net (`pharmnet-dz.com`)** | **Cas 2** | `pharmnet-dz.com/robots.txt` | ✅ Autorisé — `Allow: /`, sauf espaces privés `/administration`, `/mon-profil`. API Supabase publique avec RLS autorisant la consultation des données du répertoire | API REST Supabase publique (clé publishable, pause 3 s, pagination, **données de démo exclues**) | Oui (`produits_enregistres.csv`, `dci.csv`, `laboratoires.csv`) | 21/11/2026 |
| **DwaDZ (`dzair-pharma.net`)** | **Cas 3** | `www.dzair-pharma.net/robots.txt` | ⛔ Restreint — Interdiction `/admin`, `/api/`, `/diff`, et **blocage explicite de 23 agents IA** (`GPTBot`, `ClaudeBot`, etc.) | **Aucun appel scripté ni appel à `/api/`**. Échantillon résiduel de 30 lignes manuelles | Partiellement (30 lignes manuelles résiduelles) | 21/11/2026 |
| **Thésaurus ANSM** | **Cas 2** | `ansm.sante.fr/robots.txt` | ✅ Autorisé — `User-agent: *` / `Allow: /`. Documents de référence clinique à usage documentaire public | Téléchargement manuel des PDF officiels | Oui (`interactions_medicamenteuses.json`, 3 218 interactions) | 20/11/2026 |
| **EMA (Agence Européenne du Médicament)** | **Cas 1** | `www.ema.europa.eu/robots.txt` | ✅ Autorisé pour les pages médicaments (interdits : `/core/`, `/search/`). Open data UE | Export tabulaire officiel | Oui (`ema_medicines_clean.csv`) | 20/11/2026 |
| **DailyMed (NLM)** | **Cas 1** | `dailymed.nlm.nih.gov/dailymed/robots.txt` | ✅ Autorisé (domaine public gouvernemental US, API officielle REST) | API officielle (non utilisée en S2, candidate S3) | Non | 21/11/2026 |
| **Export algérien (registre MIPH 2018)** | **Cas 1** | s.o. (fichier local) | Données publiques de l'ancien registre national | Import local par Anis (commit `243b53c`, 15/11/2026, 4 627 lignes) | Oui (`algerian_drug_nomenclature.csv`) | 21/11/2026 |

---

## 3. Détails et justifications d'audit

### A. ANPP (`rcp.anpp.dz`) — Règle de collecte manuelle stricte
* **Alerte enseignant (21/11/2026 à 12h23)** : *« Collecte automatisée de l'ANPP (rcp.anpp.dz) : la règle est la collecte manuelle uniquement, à appliquer dès maintenant »*.
* **Actions de mise en conformité immédiates** :
  1. Le script automatisé `scripts/14_collect_anpp.py` a été **définitivement supprimé du dépôt**.
  2. Une note de conformité dédiée a été rédigée dans [`docs/week_2/note_arret_collecte_anpp.md`](file:///c:/Users/pipou/Desktop/project_RCR/docs/week_2/note_arret_collecte_anpp.md).
  3. **Usage d'étude des 33 RCP existants** : Les 33 fichiers PDF téléchargés lors de la session de calibrage sont conservés pour un usage strictement académique et d'évaluation interne (vérité terrain du banc de test). **Aucune republication ni diffusion publique** de ces documents n'aura lieu.
  4. Pour toute collecte future, la règle appliquée est le **téléchargement manuel pièce par pièce via le navigateur**.

### B. Pharm'Net (`pharmnet-dz.com`) — Utilisation de l'API Supabase
* **Autorisation des ToU** : Pharm'Net est un annuaire pharmaceutique public destiné aux professionnels de santé et au public. Les mentions légales autorisent la consultation libre et gratuite des données descriptives de médicaments.
* **Mécanisme d'accès** : L'accès aux tables publiques (`produits_enregistres`, `dci`, `laboratoires`) utilise la clé anonyme officielle (*publishable API key*) exposée publiquement dans l'application web par l'éditeur. Les requêtes s'exécutent dans le cadre strict des politiques de sécurité niveau ligne (RLS) définies par l'administrateur de Pharm'Net.
* **Respect de l'infrastructure** : 
  - Pagination de 1 000 lignes par page avec temporisation de **3 secondes** entre chaque requête (`scripts/04_build_pharmnet.py`).
  - Aucun accès aux espaces privés (`/administration`, `/mon-profil`, `/notifications`) ni aux tables utilisateurs/commandes.
  - La table privée `interactions` n'est pas requêtée : le thésaurus ANSM est utilisé pour la gestion des interactions.
* **Exclusion des données de démonstration** : L'équipe garantit qu'aucune donnée de démonstration, maquette de test ou enregistrement fictif présent sur Pharm'Net n'a été inséré dans le corpus unifié (seules les données issues de la nomenclature nationale et enrichies sont intégrées).

### C. DwaDZ (`dzair-pharma.net`) — Cas 3 et proscription de tout robot
* Le fichier `robots.txt` bloque l'accès à `/admin`, `/api/`, `/diff`, et bloque nommément **23 robots IA** (`GPTBot`, `ChatGPT-User`, `CCBot`, `ClaudeBot`, `Google-Extended`, etc.).
* Même si l'agent Pharmeazor n'est pas nommément listé, la politique de l'éditeur est sans équivoque : les moteurs d'IA ne doivent pas crawler le site ni appeler `/api/`.
* **Conformité appliquée** : Aucun appel réseau automatisé n'est effectué vers ce domaine. Seul un échantillon historique de 30 lignes manuelles collecté au début du projet est conservé dans `data/raw/dwa/nomenclature_dz_clean.csv` à des fins comparatives résiduelles.

### D. Export algérien (`algerian_drug_nomenclature.csv`)
* Fichier de 4 627 lignes ajouté par `anis` (`hammoudianis25@gmail.com`) le 15/11/2026 (commit `243b53c`).
* Correspond à l'export historique du registre national des médicaments du Ministère (circa 2018), comportant les numéros d'enregistrement au format `352/15 F 099/16` et les prix `PCSU`.
* Documenté comme source complémentaire d'antériorité, distincte du portail ANPP en ligne.
