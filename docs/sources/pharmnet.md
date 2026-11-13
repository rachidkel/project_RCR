# Pharm'Net — référentiel algérien des médicaments

- Site : <https://pharmnet-dz.com>
- Collecte : API REST Supabase publique utilisée par le site
  (`/rest/v1/produits`, `dci`, `classes_therapeutiques`, `laboratoires`).
- Commande : `python scripts/04_build_pharmnet.py` (option `--limit N` pour
  ne collecter que N fiches produits, conformément au principe de « petites
  quantités »).
- Retraitement hors ligne : `python scripts/04_build_pharmnet.py --from-raw
  20261113_235452` reconstruit les CSV depuis un snapshot, sans appel réseau.
- Cadence : 1 requête toutes les 3 s (`REQUEST_DELAY_S`), 1 000 lignes par page.

Le site est une SPA : les données affichées proviennent de cette API, il n'est
donc pas nécessaire de parser le HTML. La clé « publishable » est publique
(incluse dans le HTML) et ne donne accès qu'aux données publiques via les
règles RLS de Supabase. `robots.txt` autorise tout sauf les espaces privés
(`/administration`, `/connexion`, etc.).

## Fichiers produits

`data/raw/pharmnet/<horodatage>_<table>.json` — réponse brute, jamais modifiée,
plus un `manifest.json` (source, date, nombre de lignes).

`data/processed/pharmnet/`

| Fichier | Contenu |
|---------|---------|
| `produits.csv` | Toutes les fiches produits enrichies (DCI, classe, laboratoire) |
| `produits_enregistres.csv` | Sous-ensemble `registre = ENREGISTRE` (5 387 lignes) |
| `dci.csv` | Dénominations communes internationales (3 083) |
| `classes_therapeutiques.csv` | Classes thérapeutiques (28) |
| `laboratoires.csv` | Laboratoires (979) |

## Colonnes principales de `produits.csv`

| Colonne | Sens |
|---------|------|
| `num_enregistrement` | Numéro d'enregistrement algérien |
| `nom_commercial` | Nom de marque |
| `nom_commercial_norm` / `dci_norm` | Formes normalisées pour le matching |
| `dci_code`, `dci`, `dci_sous_classe` | DCI et code officiel |
| `classe_code`, `classe_libelle` | Classe thérapeutique |
| `laboratoire`, `laboratoire_pays`, `laboratoire_local`, `laboratoire_verifie` | Laboratoire et origine |
| `forme`, `dosage`, `conditionnement` | Présentation |
| `liste` | Liste I / II / stupéfiant |
| `registre` | `ENREGISTRE`, `NON_RENOUVELE` ou `RETIRE` |
| `prix_ppa`, `tarif_ref` | Prix public algérien et tarif de référence (DZD) |
| `code_barre` | Identifiant historique de la fiche |
| `notice_url`, `rcp_url` | Documents, quasiment absents de la base publique |
| `image_url` | Photo de la boîte |

## Limites

- Pas de RCP ni de notice : `notice_url` est vide partout et `rcp_url` ne
  contient qu'une seule valeur. Pour le texte des documents, utiliser l'ANPP
  ou une autre source.
- La table `interactions` n'est pas accessible avec la clé publique (RLS) :
  les interactions restent couvertes par le thésaurus ANSM.
- Les prix sont souvent absents (`prix_ppa` renseigné pour ~1 500 fiches) et
  peuvent changer : toujours indiquer la date de collecte.
- La base contient aussi des médicaments retirés ou non renouvelés ; filtrer
  sur `registre = ENREGISTRE` pour le marché courant.

## Qualité des données (audit du 13/11/2026)

**Points propres :**

- 9 560 identifiants uniques, aucune ligne dupliquée à l'identique.
- 100 % des `dci_code`, `classe_code` et `laboratoire_id` trouvent leur
  référence : aucune clé orpheline.
- Toutes les dates sont analysables (`date_enr_*`, `created_at`, `updated_at`).
- Aucun espace en trop, espace double, caractère insécable ou mojibake après
  nettoyage.
- Prix numériques positifs (110 à 7 840 DZD), aucune valeur aberrante.

**Nettoyages appliqués par le collecteur :**

- 233 fiches avaient une date dans `laboratoire_pays` (donnée corrompue à la
  source) : remplacée par une valeur manquante.
- `tarif_ref = 0` (8 288 lignes) signifie « non renseigné », pas « gratuit » :
  remplacé par une valeur manquante.
- Espaces multiples et espaces de bord supprimés dans tous les champs texte.
- `laboratoire_verifie` ajouté aux fiches produits.

**Faiblesses restantes, à connaître avant exploitation :**

| Problème | Ampleur | Conséquence |
|----------|---------|-------------|
| `code_barre` non unique | 243 doublons (225 groupes) | Ne pas l'utiliser seul comme clé : privilégier `id` ou filtrer `registre` |
| `num_enregistrement` non unique | 46 doublons (44 groupes) | Même produit en version RETIRE et NON_RENOUVELE |
| `prix_ppa` manquant | 8 046 / 9 560 (dont 4 202 / 5 387 enregistrés) | Ne jamais afficher un prix absent ni le déduire |
| `tarif_ref` manquant | 8 288 / 9 560 | Idem |
| `liste` manquante | 1 603 | Plan de classement inconnu |
| `type` / `statut_fab` manquants | 2 726 / 2 678 | Correspond presque exactement aux fiches RETIRE |
| `laboratoire_pays` manquant | 1 066 | Pays d'origine inconnu |
| Pas de notice/RCP | 9 560 / 9 559 | Texte réglementaire à chercher ailleurs (ANPP) |
| `en_rupture` toujours `False` | 9 560 | Information de rupture non fiable, ne pas l'afficher |
| Noms de DCI non uniques | 3 083 codes pour 1 807 noms | Joindre sur `dci_code`, pas sur le nom |

Conclusion : les données sont **propres et cohérentes structurellement**, mais
**incomplètes** (documents, prix, rupture). Elles conviennent au catalogue et
au matching DCI/marque ; elles ne suffisent pas seules pour une réponse
clinique citée.
