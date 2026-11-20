# ANPP — plateforme RCP (rcp.anpp.dz)

Source **prioritaire** du cahier des charges : les RCP officiels validés en
Algérie. C'est elle qui apporte ce qui manque à tout le reste du corpus —
indications, contre-indications, posologie, interactions, effets indésirables.

## Accès

- Base : <https://rcp.anpp.dz>
- `robots.txt` : `User-agent: *` / `Disallow:` → tout est autorisé (vérifié le 20/11/2026).
- Aucune inscription, aucun jeton privé : la recherche est publique.

## Comment la recherche fonctionne

Le site est une application Laravel **Livewire**. Un simple `?q=` ne renvoie
rien : il faut reproduire l'appel du navigateur.

1. `GET /` → cookies de session, jeton CSRF (`name="csrf-token"`) et
   « snapshot » du composant (`wire:snapshot`).
2. `POST /livewire/update` en JSON :

```json
{
  "_token": "<csrf>",
  "components": [{
    "snapshot": "<snapshot Livewire>",
    "updates": { "query": "PARACETAMOL" },
    "calls": [{ "path": "", "method": "search", "params": [] }]
  }]
}
```

3. La réponse contient un fragment HTML où les documents apparaissent en
   `/storage/rcp-pdfs/<laboratoire>/<uuid>.pdf`.

En-têtes nécessaires : `X-Livewire: true`, `X-CSRF-TOKEN`, `Referer`.

## Deux pièges vérifiés

**La recherche est sensible à la casse et aux accents.**

| Requête | Résultats |
|---|---:|
| `PARACETAMOL` | 5 RCP |
| `paracetamol` | 0 |
| `paracétamol` | 0 |
| `PARACÉTAMOL` | 0 |
| `DOLIPRANE` | 7 RCP |
| `IBUPROFENE` | 1 RCP |

Toutes les requêtes doivent donc être en **majuscules sans accent**
(`textnorm.norm(...).upper()`).

**La couverture est partielle.** La plateforme ne contient pas toutes les
marques du référentiel : `EFFERALGAN` et `ALGIFEN` renvoient 0 alors que ces
produits sont enregistrés. Il faut essayer la DCI puis plusieurs marques, et
accepter qu'un médicament reste sans RCP.

## Collecte

```powershell
python scripts/14_collect_anpp.py --dry-run            # liste, sans télécharger
python scripts/14_collect_anpp.py --limit 3            # test sur 3 médicaments
python scripts/14_collect_anpp.py                      # les 40 du périmètre
```

Fichiers produits :

```
data/raw/anpp/pdfs/<uuid>.pdf     # les RCP, jamais modifiés
data/raw/anpp/manifest.json       # DCI, requête utilisée, URL, date, SHA-256
```

Le script respecte une pause de 3 s entre requêtes et ne dépasse pas 7 requêtes
par médicament. Volumétrie limitée au périmètre du projet.

## Ce que contient un RCP

Exemple vérifié (paracétamol, 10 pages, 25 711 caractères) :

```
1. Indications thérapeutiques   → OUI
4.2. Posologie et mode d'administration → OUI
Contre-indications              → OUI
Interactions                    → OUI
```

Extrait réel : « La dose habituelle est de 15 mg/kg par administration […]
Les doses maximales sont de 15 mg/kg par prise et de 60 mg/kg/jour. »

## Suite à faire

- [ ] `src/pharmeazor/parsers/anpp.py` : découper chaque PDF en rubriques
      (indications, contre-indications, posologie, interactions, effets
      indésirables) et produire un JSON par médicament.
- [ ] `src/pharmeazor/corpus.py` : ajouter la source `S_ANPP_RCP` avec
      `authority_rank: 1` — le RCP officiel passe avant la nomenclature et les
      sources étrangères.
- [ ] Évaluer le taux de rubriques correctement retrouvées sur **20 notices**
      vérifiées à la main (critère de réussite du cahier des charges).
- [ ] Reconstruire `corpus.jsonl` puis les index (07 → 08).
- [ ] Compléter la ligne ANPP de `docs/week_1/legal_sources.md`.
