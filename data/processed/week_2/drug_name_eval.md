# Évaluation de la normalisation des noms — Semaine 2

**Taux global de reconnaissance : 42/42 = 100.0%**

## Taux par type de saisie

| Type | Réussis | Total | Taux |
|---|---|---|---|
| dci | 11 | 11 | 100.0% |
| faute | 6 | 6 | 100.0% |
| majuscules | 3 | 3 | 100.0% |
| minuscules | 3 | 3 | 100.0% |
| nom_commercial | 13 | 13 | 100.0% |
| nom_usuel | 1 | 1 | 100.0% |
| sans_accent | 5 | 5 | 100.0% |

## Détail

| Saisie | Type | Attendu | Trouvé | OK |
|---|---|---|---|---|
| paracétamol | dci | paracétamol | paracétamol | ✅ |
| paracetamol | sans_accent | paracétamol | paracétamol | ✅ |
| PARACETAMOL | majuscules | paracétamol | paracétamol | ✅ |
| paracetmol | faute | paracétamol | paracétamol | ✅ |
| paracétamole | faute | paracétamol | paracétamol | ✅ |
| DOLIPRANE | nom_commercial | paracétamol | paracétamol | ✅ |
| doliprane | minuscules | paracétamol | paracétamol | ✅ |
| Dolipran | faute | paracétamol | paracétamol | ✅ |
| EFFERALGAN | nom_commercial | paracétamol | paracétamol | ✅ |
| ibuprofène | dci | ibuprofène | ibuprofène | ✅ |
| ibuprofene | sans_accent | ibuprofène | ibuprofène | ✅ |
| IBUPROFENE | majuscules | ibuprofène | ibuprofène | ✅ |
| ibuprofn | faute | ibuprofène | ibuprofène | ✅ |
| ADVIL | nom_commercial | ibuprofène | ibuprofène | ✅ |
| advil | minuscules | ibuprofène | ibuprofène | ✅ |
| diclofénac | dci | diclofénac | diclofénac | ✅ |
| diclofenac | sans_accent | diclofénac | diclofénac | ✅ |
| BIOFENAC | nom_commercial | diclofénac | diclofénac | ✅ |
| kétoprofène | dci | kétoprofène | kétoprofène | ✅ |
| ketoprofene | sans_accent | kétoprofène | kétoprofène | ✅ |
| KETOFEN | nom_commercial | kétoprofène | kétoprofène | ✅ |
| acide acétylsalicylique | dci | acide acétylsalicylique | acide acétylsalicylique | ✅ |
| aspirine | nom_usuel | acide acétylsalicylique | acide acétylsalicylique | ✅ |
| ASPIRINE CARDIO | nom_commercial | acide acétylsalicylique | acide acétylsalicylique | ✅ |
| KARDEGIC | nom_commercial | acide acétylsalicylique | acide acétylsalicylique | ✅ |
| amoxicilline | dci | amoxicilline | amoxicilline | ✅ |
| AMOXICILLINE | sans_accent | amoxicilline | amoxicilline | ✅ |
| amoxicilin | faute | amoxicilline | amoxicilline | ✅ |
| AUGMENTIN | nom_commercial | amoxicilline | amoxicilline | ✅ |
| augmentin | minuscules | amoxicilline | amoxicilline | ✅ |
| clarithromycine | dci | clarithromycine | clarithromycine | ✅ |
| CLARIDAR | nom_commercial | clarithromycine | clarithromycine | ✅ |
| ciprofloxacine | dci | ciprofloxacine | ciprofloxacine | ✅ |
| CIPRO | nom_commercial | ciprofloxacine | ciprofloxacine | ✅ |
| amlodipine | dci | amlodipine | amlodipine | ✅ |
| AMLODIPINE | majuscules | amlodipine | amlodipine | ✅ |
| amlodipin | faute | amlodipine | amlodipine | ✅ |
| AMLOR | nom_commercial | amlodipine | amlodipine | ✅ |
| ramipril | dci | ramipril | ramipril | ✅ |
| TRIATEC | nom_commercial | ramipril | ramipril | ✅ |
| losartan | dci | losartan | losartan | ✅ |
| COZAAR | nom_commercial | losartan | losartan | ✅ |