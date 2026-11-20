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
| Nomenclature nationale — MIPH | `miph.gov.dz/robots.txt` | ✅ Oui — `User-agent: *` / `Disallow:` vide, tout est autorisé | Aucune licence de réutilisation trouvée sur les pages consultées | Téléchargement manuel du fichier officiel | Oui (`nomenclature_active.csv`, `retraits.csv`, `non_renouveles.csv`) | 20/11/2026 |
| ANPP (RCP / notices) | `anpp.dz/robots.txt` | ✅ Oui — seul `/wp-admin/` est interdit | À vérifier avant toute collecte | Aucune : source non collectée | Non — source candidate | 20/11/2026 |
| Pharm'Net (pharmnet-dz.com) | `pharmnet-dz.com/robots.txt` | ✅ Oui — `Allow: /`, sauf `/administration`, `/admin-*`, `/mon-profil`, `/notifications`, `/tableau-de-bord`, `/connexion` | CGU non trouvées (site en JavaScript) ; le site se dit « connecté à la base officielle (nomenclature juillet 2026) » | API REST publique (Supabase), 1 000 lignes/page, 3 s entre requêtes | Oui (`produits_enregistres.csv`, `dci.csv`, `laboratoires.csv`) | 20/11/2026 |
| DwaDZ (dzair-pharma.net) | `www.dzair-pharma.net/robots.txt` | ⚠️ Mitigé — allow `/`, sauf `/admin`, `/api/`, `/diff`, **et blocage nommé de 23 agents IA** | Republie la nomenclature MIPH ; « données à titre informatif » ; pas de licence | Manuel, petites quantités, attribution obligatoire | Partiellement — 30 lignes, provenance non confirmée | 20/11/2026 |
| Thésaurus ANSM | `ansm.sante.fr/robots.txt` | ✅ Oui — `User-agent: *` / `Allow: /`, tout est autorisé | PDF publics, usage documentaire | Téléchargement direct des PDF | Oui (`interactions_medicamenteuses.json`, 3 218 interactions) | 20/11/2026 |
| EMA | `www.ema.europa.eu/robots.txt` | ✅ Oui pour les pages médicaments — interdits : `/core/`, `/profiles/`, `/search/`, `/user/*` | À vérifier | À documenter | Oui (`ema_medicines_clean.csv`), origine à préciser | 20/11/2026 |
| DailyMed (NLM) | `dailymed.nlm.nih.gov/dailymed/robots.txt` | ✅ Oui — seul `/archives/` est interdit | Conditions NLM à vérifier ; API officielle disponible | Non utilisée | Non | 20/11/2026 |
| Export algérien | s.o. (fichier, pas un site) | s.o. | Inconnue | Fichier ajouté au dépôt le 15/11/2026 | Oui — **origine non confirmée** | 20/11/2026 |

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

**ANPP.** Le `robots.txt` autorise la lecture hors administration, mais **aucune
notice ANPP n'a été collectée** : le dépôt ne contient aucune donnée ANPP. La
version précédente listait cette source comme validée, ce qui laissait croire
que les notices officielles étaient disponibles. C'est pourtant la source
prioritaire du cahier des charges pour la posologie et les contre-indications.

**Pharm'Net.** Les données sont exposées par une API Supabase avec une clé
« publishable » publique (présente dans le HTML du site), qui ne donne accès
qu'aux données publiques via RLS. La table `interactions` n'est pas lisible
avec cette clé : les interactions restent couvertes par le thésaurus ANSM.

**Export algérien.** `data/raw/nomenclature/algerian_drug_nomenclature.csv`
(4 627 lignes, en-têtes anglais) a été ajouté par `anis` le 15/11/2026
(commit `243b53c`). Son contenu — numéros d'enregistrement `352/15 F 099/16`,
prix `PCSU`, `Liste I/II`, types `Ge`/`Re` — correspond à un export du registre
MIPH, mais un snapshot différent de `nomenclature_active.csv` (4 627 lignes
contre 5 425 actifs). **L'URL et la date de téléchargement restent à retrouver** :
tant que ce n'est pas fait, cette source ne peut pas être citée dans le rapport.

## Écarts avec la version précédente de ce fichier

| Ligne | Ancienne valeur | Valeur vérifiée le 20/11/2026 |
|---|---|---|
| MIPH | « ❌ Non (Interdit) » | tout autorisé — *erreur corrigée* |
| Pharm'Net | « ⚠️ À vérifier » | vérifié : autorisé hors zones privées |
| dzair-pharma.net | « ⚠️ À vérifier » | vérifié : autorisé hors `/admin`, `/api/`, `/diff`, mais **agents IA bloqués** |
| ANPP | présenté comme source acquise | robots autorisé, **source non collectée** |
| EMA, DailyMed | absents | ajoutés |
| Export algérien | absent (appelé « ANPP ») | ajouté, origine non confirmée |
| DWA | « liste alsacienne », 30 chunks sans réserve | 30 lignes d'origine **non confirmée** (`S1/S4 (to confirm)`) |

## Ce qui n'a pas été vérifié

Pour rester honnête sur la portée de ce tableau : seuls les `robots.txt` ont été
lus directement. **Les conditions générales de l'EMA, de DailyMed, du MIPH et de
Pharm'Net n'ont pas été lues** — elles sont signalées « à vérifier » et ne
peuvent pas être invoquées dans le rapport tant que ce n'est pas fait. La
provenance de l'export algérien et celle des 30 lignes `dwa` restent inconnues.

## À faire

- [ ] Retrouver l'URL et la date de l'export `algerian_drug_nomenclature.csv`.
- [ ] Confirmer que les 30 lignes de `dwa/nomenclature_dz_clean.csv` viennent bien de DwaDZ (`S1/S4 (to confirm)`).
- [ ] Lire les conditions de réutilisation de l'EMA et de DailyMed.
- [ ] Documenter l'origine exacte de `ema_medicines_clean.csv`.
- [ ] Décider du statut de DwaDZ : source secondaire manuelle, ou écartée.
- [ ] Vérifier que `/api/` de DwaDZ n'est jamais appelé par le code.
