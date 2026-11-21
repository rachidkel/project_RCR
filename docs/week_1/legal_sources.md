# Conformité des sources — Pharmeazor

Vérification du **20/11/2026**. Le tableau reprend les colonnes de la version
précédente — URL du `robots.txt`, autorisation, méthode, date de vérification —
et en ajoute deux : les conditions d'utilisation, et **l'état réel de collecte
dans ce dépôt**. Une source annoncée mais jamais collectée ne doit pas figurer
comme acquise.

Règle appliquée : si une source interdit la collecte automatique, elle est
utilisée **manuellement ou écartée**, jamais contournée. La date de collecte est
conservée avec les données.

## Tableau

| Source | URL du `robots.txt` | Autorisé ? | Conditions d'utilisation | Méthode de collecte | Collectée ? | Date de vérification |
|---|---|---|---|---|---|---|
| Nomenclature nationale — MIPH | `miph.gov.dz/robots.txt` | ✅ Oui — `User-agent: *` / `Disallow:` vide, tout est autorisé | Aucune licence restrictive ; publication officielle d'utilité publique | Téléchargement manuel du fichier officiel | Oui (`nomenclature_active.csv`, `retraits.csv`, `non_renouveles.csv`) | 20/11/2026 |
| ANPP (RCP / notices) | `rcp.anpp.dz/robots.txt` | ✅ Oui — `User-agent: *` / `Disallow:` vide, tout autorisé | Consultation publique gratuite des RCP officiels algériens ; usage d'information professionnelle | Script automatisé (`scripts/14_collect_anpp.py`, Livewire/CSRF, pause 3 s) | Oui (33 RCP PDF, 307 rubriques extraites dans `data/raw/anpp/` et `data/processed/anpp/`) | 21/11/2026 |
| Pharm'Net (pharmnet-dz.com) | `pharmnet-dz.com/robots.txt` | ✅ Oui — `Allow: /`, sauf `/administration`, `/admin-*`, `/mon-profil`, `/notifications`, `/tableau-de-bord`, `/connexion` | Données publiques issues de la nomenclature, consultation libre à titre informatif ; respect des quotas (pause 3 s, pas d'accès aux tables privées via RLS) | API REST publique (Supabase), 1 000 lignes/page, 3 s entre requêtes | Oui (`produits_enregistres.csv`, `dci.csv`, `laboratoires.csv`) | 21/11/2026 |
| DwaDZ (dzair-pharma.net) | `www.dzair-pharma.net/robots.txt` | ⚠️ Mitigé — allow `/`, sauf `/admin`, `/api/`, `/diff`, **et blocage nommé de 23 agents IA commerciaux** | Page `/a-propos` vérifiée : moteur indépendant rediffusant la nomenclature MIPH à titre d'aide à la décision ; interdiction des appels directs à `/api/` | Échantillon manuel de 30 lignes, aucun appel automatique au site ni à `/api/` | Partiellement — 30 lignes manuelles (usage résiduel) | 21/11/2026 |
| Thésaurus ANSM | `ansm.sante.fr/robots.txt` | ✅ Oui — `User-agent: *` / `Allow: /`, tout est autorisé | PDF publics, usage documentaire | Téléchargement direct des PDF | Oui (`interactions_medicamenteuses.json`, 3 218 interactions) | 20/11/2026 |
| EMA | `www.ema.europa.eu/robots.txt` | ✅ Oui pour les pages médicaments — interdits : `/core/`, `/profiles/`, `/search/`, `/user/*` | Données ouvertes de l'Union européenne | Export tabulaire officiel nettoyé | Oui (`ema_medicines_clean.csv`) | 20/11/2026 |
| DailyMed (NLM) | `dailymed.nlm.nih.gov/dailymed/robots.txt` | ✅ Oui — seul `/archives/` est interdit | Données du domaine public (gouvernement fédéral US) ; API officielle | Non utilisée en Semaine 2 (candidate Semaine 3) | Non | 21/11/2026 |
| Export algérien (registre 2018) | s.o. (fichier, pas un site) | s.o. | Données publiques de l'ancien registre MIPH | Ajouté par `anis` (commit `243b53c`, 15/11/2026), export de 4 627 lignes (historique MIPH) | Oui (`algerian_drug_nomenclature.csv`) | 21/11/2026 |

## Détail

**MIPH.** Le `robots.txt` du 20/11/2026 ne contient qu'un bloc Yoast
(`User-agent: *` / `Disallow:` vide) : rien n'est interdit. La version
précédente de ce fichier indiquait l'inverse (« ❌ Non (Interdit) »), ce qui
était faux et se contredisait avec le fait que la nomenclature MIPH est la
première source du projet.

Le cahier des charges affirme de son côté que « la page de la liste interdit
l'accès automatique (`robots.txt`) ». Le `robots.txt` du domaine, lui, autorise
tout. Les deux constats ne portent donc pas sur la même chose : nous restons en
**téléchargement manuel**, ce qui est conforme à la lecture la plus stricte
comme à la plus permissive. Aucun robot n'est utilisé sur ce site.

**DwaDZ — le point sensible.** Le site autorise les robots génériques mais
exclut nommément **23 agents** : `GPTBot`, `ChatGPT-User`, `OAI-SearchBot`,
`CCBot`, `ClaudeBot`, `Claude-Web`, `anthropic-ai`, `Google-Extended`,
`Applebot-Extended`, `Meta-ExternalAgent`, `Bytespider`, `PerplexityBot`,
`YouBot`, `cohere-ai`, `Diffbot`, `omgilibot`, `Amazonbot`, `PetalBot`,
`SemrushBot`, `AhrefsBot`, `MJ12bot`, `DotBot`, `DataForSeoBot`. Notre système
est un assistant IA : la lecture littérale du `robots.txt` autorise un crawl
générique, mais l'intention de l'éditeur est claire. La collecte doit rester
manuelle, en petites quantités, avec attribution, et `/api/` ne doit pas être
appelé.

**DWA / DwaDZ : attention à l'amalgame.** Le fichier `data/raw/dwa/nomenclature_dz_clean.csv`
ne contient que **30 lignes** et porte lui-même `source_id = "S1/S4 (to confirm)"`.
Il a été ajouté par `walid` le 13/11/2026 (commit `ea4f049`). Rien ne prouve
encore que ces 30 lignes viennent de dzair-pharma.net : c'est une hypothèse,
appuyée par le fait que DwaDZ republie la nomenclature MIPH. Le rapport de
semaine 2 les présente comme « DWA (liste alsacienne) », ce qui est faux dans
tous les cas. Le renommage prévu en « dzair-pharma.net » doit donc être
présenté comme **à confirmer**, pas comme un fait établi.

**ANPP.** Plateforme officielle `rcp.anpp.dz`. Le `robots.txt` autorise
l'accès (`User-agent: * / Disallow:` vide). La collecte automatisée des RCP a
été réalisée le 21/11/2026 par `scripts/14_collect_anpp.py` via le protocole
Livewire avec jeton CSRF, limitation de cadence (pause de 3 s) et restriction au
périmètre des 40 médicaments. 33 RCP officiels ont été récupérés et convertis en
rubriques structurées dans `data/processed/anpp/`.

**Pharm'Net.** Les données sont exposées par une API Supabase avec une clé
« publishable » publique (présente dans le HTML du site), qui ne donne accès
qu'aux données publiques via RLS. `robots.txt` autorise l'ensemble du site public
(`Allow: /`). Le site est un portail professionnel rediffusant les données de la
nomenclature. La cadence de requêtage (3 s) et la limitation de volume sont
respectées par `scripts/04_build_pharmnet.py`. La table `interactions` n'est pas
lisible avec cette clé : les interactions restent couvertes par le thésaurus ANSM.

**Export algérien.** `data/raw/nomenclature/algerian_drug_nomenclature.csv`
(4 627 lignes, en-têtes anglais) a été ajouté par `anis` (`hammoudianis25@gmail.com`)
le 15/11/2026 (commit `243b53c`). Son contenu — numéros d'enregistrement
`352/15 F 099/16`, prix `PCSU`, `Liste I/II`, types `Ge`/`Re` — correspond à un
export antérieur (circa 2018) du registre MIPH. Il avait été nommé informellement
« ANPP » lors de son ajout, ce qui a causé une confusion initiale avec la
véritable plateforme ANPP (`rcp.anpp.dz`), désormais collectée distinctement.

## Écarts avec la version précédente de ce fichier

| Ligne | Ancienne valeur | Valeur vérifiée le 21/11/2026 |
|---|---|---|
| MIPH | « ❌ Non (Interdit) » | tout autorisé — *erreur corrigée* |
| Pharm'Net | « ⚠️ À vérifier » | vérifié : autorisé hors zones privées, API publique avec RLS respectée |
| dzair-pharma.net | « ⚠️ À vérifier » | vérifié : autorisé hors `/admin`, `/api/`, `/diff`, **agents IA bloqués** ; collecte automatique proscrite |
| ANPP | présenté comme non collecté | **collecté le 21/11/2026** (33 RCP officiels ANPP) |
| EMA, DailyMed | absents | ajoutés |
| Export algérien | origine inconnue | documenté : export registre MIPH 2018 ajouté par `anis` (commit `243b53c`) |
| DWA | « liste alsacienne », 30 chunks sans réserve | 30 lignes d'origine non confirmée, maintenues à titre résiduel |

## À faire

- [x] Vérifier les conditions et `robots.txt` de Pharm'Net et DwaDZ (fait le 21/11/2026).
- [x] Identifier l'auteur et l'origine de `algerian_drug_nomenclature.csv` (ajouté par Anis, commit `243b53c`, export registre MIPH).
- [x] Collecter et intégrer la véritable source ANPP RCP/notices (`scripts/14_collect_anpp.py`).
- [ ] Lire les conditions de réutilisation approfondies de l'EMA et de DailyMed (Semaine 3).
- [x] Vérifier que `/api/` de DwaDZ n'est jamais appelé par le code (respecté : aucun appel réseau à DwaDZ dans les scripts).
