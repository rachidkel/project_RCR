# Évaluation de la normalisation des noms — Semaine 2 (version corrigée)

Le dictionnaire est reconstruit à l'exécution depuis `nomenclature_active.csv` et `produits_enregistres.csv` : **3844 marques** et **1162 DCI**, dont **157 marques ambigües** (une marque rattachée à plusieurs molécules).

Les sels et hydrates sont fusionnés avant de juger l'ambiguïté : `PERINDOPRIL ERBUMINE` et `PERINDOPRIL TER-BUTYLAMINE` désignent la même molécule, alors que `BETAMETHASONE DIPROPIONATE` et `VALERATE` sont deux produits distincts.

## Résultat global

| Jeu | Corrects | Taux |
|---|---:|---:|
| Conception (46 saisies) | 46 | 100.0% |
| Couverture des 40 (18 saisies) | 18 | 100.0% |
| Tenu à l'écart (16 saisies) | 16 | 100.0% |
| **Ensemble** | **80/80** | **100.0%** |

**Le score du jeu de conception n'est pas une estimation de généralisation** : l'algorithme a été réglé en observant ces saisies, donc il y est mécaniquement bon. Seul le jeu tenu à l'écart, écrit après le réglage et exécuté sans retouche, donne une estimation honnête.

| Indicateur | Valeur |
|---|---:|
| Erreurs silencieuses (mauvaise DCI affichée sans alerte) | 0 |
| Ambiguïtés non signalées | 0 |
| Saisies non trouvées | 0 |
| Alertes d'ambiguïté superflues | 5 |
| Saisies qui sont une clé exacte après nettoyage | 50/80 |

Sur 50 saisies, la forme nettoyée est une clé exacte du dictionnaire : la correspondance exacte expliquerait donc à elle seule une partie du score. Les autres passent par la mise en forme, le préfixe, la fusion de sels ou le flou — c'est là que se joue la vraie normalisation.

## Couverture de la liste des 40 médicaments

| DCI du projet | Saisies | Remarque |
|---|---:|---|
| paracétamol | 8 |  |
| ibuprofène | 4 |  |
| diclofénac | 2 |  |
| kétoprofène | 2 |  |
| naproxène | 1 |  |
| acide acétylsalicylique | 2 |  |
| méloxicam | 1 |  |
| piroxicam | 1 |  |
| célécoxib | 1 |  |
| tramadol | 1 |  |
| paracétamol + codéine | 2 |  |
| néfopam | 1 |  |
| amoxicilline | 3 |  |
| amoxicilline + acide clavulanique | 3 |  |
| céfixime | 1 |  |
| céfuroxime | 1 |  |
| ceftriaxone | 1 |  |
| azithromycine | 1 |  |
| clarithromycine | 3 |  |
| ciprofloxacine | 1 |  |
| lévofloxacine | 1 |  |
| doxycycline | 1 |  |
| cotrimoxazole (sulfaméthoxazole + triméthoprime) | 0 |  |
| métronidazole | 3 |  |
| gentamicine | 1 |  |
| clindamycine | 1 |  |
| amlodipine | 3 |  |
| nifédipine | 0 | aucune fiche dans les deux sources : impossible à résoudre |
| périndopril | 1 |  |
| ramipril | 2 |  |
| énalapril | 1 |  |
| losartan | 2 |  |
| valsartan | 1 |  |
| bisoprolol | 1 |  |
| aténolol | 1 |  |
| nébivolol | 1 |  |
| hydrochlorothiazide | 0 | toujours en association dans le référentiel : testé en ambiguïté |
| indapamide | 1 |  |
| spironolactone | 2 |  |
| méthyldopa | 1 |  |

## Résultat par type de saisie

| Type | Total | Corrects | Détail des verdicts |
|---|---:|---:|---|
| marque_bruitee | 38 | 38/38 | correct + alerte d'ambiguïté: 1 |
| marque_hors_registre | 2 | 2/2 | — |
| faute_frappe | 12 | 12/12 | correct + alerte d'ambiguïté: 2 |
| sans_accent | 4 | 4/4 | — |
| dci_bruitee | 8 | 8/8 | — |
| nom_usuel | 4 | 4/4 | — |
| abreviation | 3 | 3/3 | correct + alerte d'ambiguïté: 2 |
| ambigu_reelle | 2 | 2/2 | — |
| hors_perimetre | 4 | 4/4 | — |
| inconnu | 2 | 2/2 | — |
| absent_du_corpus | 1 | 1/1 | — |

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
| naprox 500 | couverture_40 | marque_bruitee | NAPROXENE | NAPROXENE | marque | 100 | non | correct |
| melox 15 mg | couverture_40 | marque_bruitee | MELOXICAM | MELOXICAM | marque | 100 | non | correct |
| piroxen 20 | couverture_40 | marque_bruitee | PIROXICAM | PIROXICAM | marque | 100 | non | correct |
| arbrex 200 | couverture_40 | marque_bruitee | CELECOXIB | CELECOXIB | marque | 100 | non | correct |
| antapam 20 mg | couverture_40 | marque_bruitee | NEFOPAM | NEFOPAM | marque | 100 | non | correct |
| megacef 200 | couverture_40 | marque_bruitee | CEFIXIME | CEFIXIME | marque | 100 | non | correct |
| zinnat 500 | couverture_40 | marque_bruitee | CEFUROXIME | CEFUROXIME | marque | 100 | non | correct |
| cetrial 1g | couverture_40 | marque_bruitee | CEFTRIAXONE | CEFTRIAXONE | marque | 100 | non | correct |
| levoflox 500 | couverture_40 | marque_bruitee | LEVOFLOXACINE | LEVOFLOXACINE | marque | 100 | non | correct |
| xyline 100 | couverture_40 | marque_bruitee | DOXYCYCLINE | DOXYCYCLINE | marque | 100 | non | correct |
| bactisol 480 | couverture_40 | marque_bruitee | SULFAMETHOXAZOLE + TRIMETHOPRIME | SULFAMETHOXAZOLE + TRIMETHOPRIME | marque | 100 | non | correct |
| apigen 80 mg | couverture_40 | marque_bruitee | GENTAMICINE | GENTAMICINE | marque | 100 | non | correct |
| clinaram 300 | couverture_40 | marque_bruitee | CLINDAMYCINE | CLINDAMYCINE | marque | 100 | non | correct |
| nifedipine lp 20 | couverture_40 | absent_du_corpus | — | — | aucune |  | non | correct |
| coversyl 5 | couverture_40 | marque_bruitee | PERINDOPRIL | PERINDOPRIL | marque | 100 | non | correct |
| enalapril 10 mg | couverture_40 | dci_bruitee | ENALAPRIL | ENALAPRIL | dci | 100 | non | correct |
| temerivol 5 | couverture_40 | marque_bruitee | NEBIVOLOL | NEBIVOLOL | marque | 100 | non | correct |
| aldomet 250 | couverture_40 | marque_bruitee | METHYLDOPA | METHYLDOPA | marque | 100 | non | correct |
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
| marque | 42 |
| flou | 17 |
| dci | 10 |
| aucune | 5 |
| contient | 4 |
| alias | 2 |

Repères de comparaison sur les mêmes saisies : correspondance exacte sur la saisie brute = 0 %, nettoyage (dosage/forme) + correspondance exacte = 50/80 = 62.5%. Le reste est apporté par la mise en forme des marques, les préfixes, la fusion des sels, les alias et le flou — c'est-à-dire par la normalisation elle-même.

Une attente du jeu tenu à l'écart était fausse et a été corrigée après vérification : `CETADOL` est une association tramadol/paracétamol, pas du tramadol seul. La correction est signalée ici pour que le chiffre reste vérifiable.


## Ce que la version précédente ne mesurait pas

- Le dictionnaire y était recopié à la main depuis les listes de marques extraites du même référentiel que les entrées de test : la correspondance exacte suffisait, donc le score ne pouvait pas être mauvais.
- Aucune saisie n'était bruitée : ni dosage, ni forme galénique, ni faute de frappe, alors que c'est la forme réelle d'une question de comptoir.
- Une marque rattachée à deux molécules était tranchée en silence.
- Le dictionnaire manuel contenait des marques absentes du référentiel (« ibuphene »), donc le test validait des chaînes, pas un comportement.
