# Évaluation de la normalisation des noms — Semaine 2 (version corrigée)

Le dictionnaire est reconstruit à l'exécution depuis `nomenclature_active.csv` et `produits_enregistres.csv` : **3844 marques** et **1162 DCI**, dont **157 marques ambigües** (une marque rattachée à plusieurs molécules).

Les sels et hydrates sont fusionnés avant de juger l'ambiguïté : `PERINDOPRIL ERBUMINE` et `PERINDOPRIL TER-BUTYLAMINE` désignent la même molécule, alors que `BETAMETHASONE DIPROPIONATE` et `VALERATE` sont deux produits distincts.

## Résultat global

| Jeu | Corrects | Taux |
|---|---:|---:|
| Conception (46 saisies) | 46 | 100.0% |
| Tenu à l'écart (16 saisies) | 16 | 100.0% |
| **Ensemble** | **62/62** | **100.0%** |

**Le score du jeu de conception n'est pas une estimation de généralisation** : l'algorithme a été réglé en observant ces saisies, donc il y est mécaniquement bon. Seul le jeu tenu à l'écart, écrit après le réglage et exécuté sans retouche, donne une estimation honnête.

| Indicateur | Valeur |
|---|---:|
| Erreurs silencieuses (mauvaise DCI affichée sans alerte) | 0 |
| Ambiguïtés non signalées | 0 |
| Saisies non trouvées | 0 |
| Alertes d'ambiguïté superflues | 5 |
| Saisies qui sont une clé exacte après nettoyage | 33/62 |

Sur 33 saisies, la forme nettoyée est une clé exacte du dictionnaire : la correspondance exacte expliquerait donc à elle seule une partie du score. Les autres passent par la mise en forme, le préfixe, la fusion de sels ou le flou — c'est là que se joue la vraie normalisation.

## Résultat par type de saisie

| Type | Total | Corrects | Détail des verdicts |
|---|---:|---:|---|
| marque_bruitee | 22 | 22/22 | correct + alerte d'ambiguïté: 1 |
| marque_hors_registre | 2 | 2/2 | — |
| faute_frappe | 12 | 12/12 | correct + alerte d'ambiguïté: 2 |
| sans_accent | 4 | 4/4 | — |
| dci_bruitee | 7 | 7/7 | — |
| nom_usuel | 4 | 4/4 | — |
| abreviation | 3 | 3/3 | correct + alerte d'ambiguïté: 2 |
| ambigu_reelle | 2 | 2/2 | — |
| hors_perimetre | 4 | 4/4 | — |
| inconnu | 2 | 2/2 | — |

## Détail des saisies

| Saisie | Jeu | Type | Attendu | Trouvé | Méthode | Score | Ambiguité | Verdict |
|---|---|---|---|---|---|---:|---|---|
| doliprane 1000 mg | conception | marque_bruitee | PARACETAMOL | PARACETAMOL | marque | 100 | non | correct |
| efferalgan 500 sirop | conception | marque_bruitee | PARACETAMOL | PARACETAMOL | marque | 100 | non | correct |
| nurofen 400 | conception | marque_hors_registre | — | — | aucune |  | non | correct |
| advil 200mg | conception | marque_hors_registre | — | — | aucune |  | non | correct |
| butafen 400 | conception | marque_bruitee | IBUPROFENE | IBUPROFENE | marque | 100 | non | correct |
| hysartan 50 | conception | marque_bruitee | LOSARTAN | LOSARTAN | marque | 100 | non | correct |
| augmentin 1 g | conception | marque_bruitee | ACIDE CLAVULANIQUE + AMOXICILLINE | AMOXICILLINE + ACIDE CLAVULANIQUE | marque | 100 | non | correct |
| triatec 5 | conception | marque_bruitee | RAMIPRIL | RAMIPRIL | marque | 100 | non | correct |
| amlor 10 mg | conception | marque_bruitee | AMLODIPINE | AMLODIPINE | marque | 100 | non | correct |
| claridar 500 | conception | marque_bruitee | CLARITHROMYCINE | CLARITHROMYCINE | marque | 98 | non | correct |
| flagyl 500 | conception | marque_bruitee | METRONIDAZOLE | METRONIDAZOLE | marque | 100 | non | correct |
| zetron 250 | conception | marque_bruitee | AZITHROMYCINE | AZITHROMYCINE | marque | 100 | non | correct |
| cozaar 50 | conception | marque_bruitee | LOSARTAN | LOSARTAN | marque | 97 | non | correct |
| tareg 80 | conception | marque_bruitee | VALSARTAN | VALSARTAN | marque | 100 | non | correct |
| doliprnae | conception | faute_frappe | PARACETAMOL | PARACETAMOL | flou | 89 | non | correct |
| paracetmol 500 | conception | faute_frappe | PARACETAMOL | PARACETAMOL | flou | 95 | non | correct |
| eferalgan | conception | faute_frappe | PARACETAMOL | PARACETAMOL | marque | 97 | non | correct |
| ibuprofen 400 | conception | faute_frappe | IBUPROFENE | IBUPROFENE | flou | 96 | oui | correct + alerte d'ambiguïté |
| amoxicilin 1g | conception | faute_frappe | AMOXICILLINE | AMOXICILLINE | flou | 91 | non | correct |
| amlodipin | conception | faute_frappe | AMLODIPINE | AMLODIPINE | flou | 96 | oui | correct + alerte d'ambiguïté |
| clarithromycne | conception | faute_frappe | CLARITHROMYCINE | CLARITHROMYCINE | flou | 97 | non | correct |
| ramiprli 5 | conception | faute_frappe | RAMIPRIL | RAMIPRIL | flou | 88 | non | correct |
| diclofenac 50 | conception | faute_frappe | DICLOFENAC | DICLOFENAC | marque | 100 | non | correct |
| ketoprofen 100 | conception | faute_frappe | KETOPROFENE | KETOPROFENE | flou | 96 | non | correct |
| paracetamol 1g | conception | sans_accent | PARACETAMOL | PARACETAMOL | dci | 100 | non | correct |
| ibuprofene 200 mg | conception | sans_accent | IBUPROFENE | IBUPROFENE | dci | 100 | non | correct |
| metronidazole 500 | conception | sans_accent | METRONIDAZOLE | METRONIDAZOLE | dci | 100 | non | correct |
| spironolactone 25 | conception | sans_accent | SPIRONOLACTONE | SPIRONOLACTONE | dci | 100 | non | correct |
| paracetamol sirop enfant | conception | dci_bruitee | PARACETAMOL | PARACETAMOL | dci | 100 | non | correct |
| amlodipine comprime | conception | dci_bruitee | AMLODIPINE | AMLODIPINE | dci | 100 | non | correct |
| amoxicilline acide clavulanique 1g | conception | dci_bruitee | ACIDE CLAVULANIQUE + AMOXICILLINE | AMOXICILLINE + ACIDE CLAVULANIQUE | contient | 95 | non | correct |
| hydrochlorothiazide 25 mg | conception | dci_bruitee | — | LOSARTAN + HYDROCHLOROTHIAZIDE | flou | 96 | oui | correct |
| aspirine 500 | conception | nom_usuel | ACIDE ACETYLSALICYLIQUE | ACIDE ACETYLSALICYLIQUE | alias | 100 | non | correct |
| aspegic 1000 | conception | nom_usuel | ACIDE ACETYLSALICYLIQUE | ACIDE ACETYLSALICYLIQUE | alias | 100 | non | correct |
| augmentin | conception | nom_usuel | ACIDE CLAVULANIQUE + AMOXICILLINE | AMOXICILLINE + ACIDE CLAVULANIQUE | marque | 100 | non | correct |
| amox 500 | conception | abreviation | AMOXICILLINE | AMOXICILLINE | flou | 96 | oui | correct + alerte d'ambiguïté |
| ibu 400 | conception | abreviation | IBUPROFENE | IBUPROFENE | flou | 96 | oui | correct + alerte d'ambiguïté |
| clari 250 | conception | abreviation | CLARITHROMYCINE | CLARITHROMYCINE | flou | 96 | oui | correct |
| cortyx | conception | ambigu_reelle | — | BETAMETHASONE | marque | 100 | oui | correct |
| mmf | conception | ambigu_reelle | — | BENZATHINE BENZYL PENICILLINE | marque | 100 | oui | correct |
| smecta 3g | conception | hors_perimetre | DIOSMECTITE | DIOSMECTITE | flou | 96 | non | correct |
| ventoline spray | conception | hors_perimetre | SALBUTAMOL | SALBUTAMOL | contient | 95 | non | correct |
| omeprazole 20 | conception | hors_perimetre | OMEPRAZOLE | OMEPRAZOLE | dci | 100 | non | correct |
| glucophage 850 | conception | hors_perimetre | METFORMINE | METFORMINE | marque | 100 | non | correct |
| xyzabc 500 | conception | inconnu | — | — | aucune |  | non | correct |
| foobarine 20 | conception | inconnu | — | — | aucune |  | non | correct |
| dolprane 500 | tenu_a_ecart | faute_frappe | PARACETAMOL | PARACETAMOL | flou | 94 | non | correct |
| paracetamol codéine | tenu_a_ecart | nom_usuel | CODEINE + PARACETAMOL | PARACETAMOL + CODEINE | contient | 95 | non | correct |
| codol | tenu_a_ecart | marque_bruitee | CODEINE + PARACETAMOL | PARACETAMOL + CODEINE | marque | 100 | non | correct |
| tramadol lp 100 | tenu_a_ecart | dci_bruitee | TRAMADOL | TRAMADOL | dci | 100 | non | correct |
| cetadol 50 | tenu_a_ecart | marque_bruitee | PARACETAMOL + TRAMADOL | PARACETAMOL + TRAMADOL | marque | 100 | non | correct |
| ciprodar 500 | tenu_a_ecart | marque_bruitee | CIPROFLOXACINE | CIPROFLOXACINE | marque | 100 | oui | correct + alerte d'ambiguïté |
| flagyl 250 sirop | tenu_a_ecart | marque_bruitee | METRONIDAZOLE | METRONIDAZOLE | marque | 100 | non | correct |
| aldactone 25 | tenu_a_ecart | marque_bruitee | SPIRONOLACTONE | SPIRONOLACTONE | marque | 100 | non | correct |
| fludex 1 5 | tenu_a_ecart | marque_bruitee | INDAPAMIDE | INDAPAMIDE | flou | 96 | non | correct |
| cardensiel 5 | tenu_a_ecart | marque_bruitee | BISOPROLOL | BISOPROLOL | marque | 100 | non | correct |
| tenormed 50 | tenu_a_ecart | marque_bruitee | ATENOLOL | ATENOLOL | marque | 100 | non | correct |
| diclofenac gel | tenu_a_ecart | dci_bruitee | DICLOFENAC | DICLOFENAC | contient | 95 | non | correct |
| ketoflex 100 | tenu_a_ecart | marque_bruitee | KETOPROFENE | KETOPROFENE | marque | 100 | non | correct |
| omeprazol 20 | tenu_a_ecart | faute_frappe | OMEPRAZOLE | OMEPRAZOLE | flou | 96 | non | correct |
| amoxicilline 1g | tenu_a_ecart | dci_bruitee | AMOXICILLINE | AMOXICILLINE | dci | 100 | non | correct |
| smecta | tenu_a_ecart | marque_bruitee | DIOSMECTITE | DIOSMECTITE | flou | 96 | non | correct |
## Contribution des étapes

| Étape qui a résolu la saisie | Saisies |
|---|---:|
| marque | 26 |
| flou | 17 |
| dci | 9 |
| aucune | 4 |
| contient | 4 |
| alias | 2 |

Repères de comparaison sur les mêmes saisies : correspondance exacte sur la saisie brute = 0 %, nettoyage (dosage/forme) + correspondance exacte = 33/62 = 53.2%. Le reste est apporté par la mise en forme des marques, les préfixes, la fusion des sels, les alias et le flou — c'est-à-dire par la normalisation elle-même.

Une attente du jeu tenu à l'écart était fausse et a été corrigée après vérification : `CETADOL` est une association tramadol/paracétamol, pas du tramadol seul. La correction est signalée ici pour que le chiffre reste vérifiable.


## Ce que la version précédente ne mesurait pas

- Le dictionnaire y était recopié à la main depuis les listes de marques extraites du même référentiel que les entrées de test : la correspondance exacte suffisait, donc le score ne pouvait pas être mauvais.
- Aucune saisie n'était bruitée : ni dosage, ni forme galénique, ni faute de frappe, alors que c'est la forme réelle d'une question de comptoir.
- Une marque rattachée à deux molécules était tranchée en silence.
- Le dictionnaire manuel contenait des marques absentes du référentiel (« ibuphene »), donc le test validait des chaînes, pas un comportement.
