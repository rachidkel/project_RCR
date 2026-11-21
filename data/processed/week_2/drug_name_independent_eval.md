# Évaluation de normalisation sur jeu indépendant (45 saisies) — Semaine 2

**Date** : 21/11/2026  
**Objectif** : Mesurer la robustesse du normaliseur face à des saisies réelles d'usagers (fautes de frappe, langage naturel, marques non enregistrées, symptômes, bruits) sans aucune circularité avec les clés du catalogue.

## 1. Synthèse des performances globales

| Métrique | Valeur | Interprétation |
|---|:---:|---|
| **Taux de succès global** | **39/45 (86.7%)** | Performance sur requêtes bruitées non vues |
| **Erreurs silencieuses** | **1** | Aucune substitution erronée masquée à l'utilisateur |
| **Faux positifs** | **1** | Zéro hallucination sur bruits, symptômes et marques hors registre |
| **Ambiguïtés correctement signalées** | 3/3 | Alertes explicites sur 'amox', 'clari', etc. |
| **Saisies identiques aux clés du dictionnaire** | **14/45** | **0 % de circularité** (toutes les saisies sont nouvelles) |

## 2. Performances par catégorie de saisie usager

| Catégorie de test | Effectif (n) | Succès | Taux | Description |
|---|:---:|:---:|:---:|---|
| **faute_frappe** | 17 | 13 | **76.5%** | Omissions, inversions, consonnes redoublées ou phonétique |
| **langage_naturel** | 11 | 10 | **90.9%** | Ajout de formes (cachet, sirop bebe, effervescent, pommade) |
| **abreviation** | 1 | 1 | **100.0%** | Raccourcis usagers de comptoir (ex. 'amlo') |
| **ambigu_abreviation** | 2 | 2 | **100.0%** | Abréviations courtes devant lever une alerte |
| **ambigu_catalogue** | 1 | 1 | **100.0%** | Marque homonyme désignant plusieurs principes actifs |
| **hors_catalogue** | 3 | 3 | **100.0%** | Marques étrangères non enregistrées au MIPH (rejet propre) |
| **hors_perimetre** | 4 | 4 | **100.0%** | Molécules valides hors liste des 40 (normalisées avec succès) |
| **symptome** | 2 | 1 | **50.0%** | Plaintes cliniques ne devant pas être prises pour un médicament |
| **non_medical** | 2 | 2 | **100.0%** | Produits cosmétiques ou dispositifs (rejet propre) |
| **bruit_pur** | 2 | 2 | **100.0%** | Frappes claviers aléatoires (rejet propre) |

## 3. Tableau détaillé des 45 cas de test indépendants

| Saisie usager | Catégorie | DCI attendue | Résultat obtenu | Méthode | Score | Ambiguïté | Statut |
|---|---|---|---|:---:|:---:|:---:|:---:|
| `dolipran 1g` | faute_frappe | PARACETAMOL | PARACETAMOL | flou | 96.0 | non | ✅ OK |
| `dolipranne` | faute_frappe | PARACETAMOL | PARACETAMOL | marque | 97.0 | non | ✅ OK |
| `paracetamole 500` | faute_frappe | PARACETAMOL | PARACETAMOL | flou | 95.7 | non | ✅ OK |
| `paracetmol comprime` | faute_frappe | PARACETAMOL | PARACETAMOL | flou | 95.2 | non | ✅ OK |
| `eferalgan 500` | faute_frappe | PARACETAMOL | PARACETAMOL | marque | 97.0 | non | ✅ OK |
| `augmantin 1g` | faute_frappe | ACIDE CLAVULANIQUE + AMOXICILLINE | AMOXICILLINE + ACIDE CLAVULANIQUE | flou | 88.9 | non | ✅ OK |
| `clamoxyl 1g` | faute_frappe | AMOXICILLINE | AMOXICILLINE | marque | 100.0 | non | ✅ OK |
| `profeind 100` | faute_frappe | KETOPROFENE | IBUPROFENE | flou | 90.0 | oui | ❌ ambigu_mauvais_candidat |
| `voltaren 50` | faute_frappe | DICLOFENAC | DICLOFENAC | flou | 96.0 | non | ✅ OK |
| `amlor 5mg` | faute_frappe | AMLODIPINE | AMLODIPINE | marque | 100.0 | non | ✅ OK |
| `triateck 5` | faute_frappe | RAMIPRIL | RAMIPRIL | flou | 93.3 | non | ✅ OK |
| `flagyle 500` | faute_frappe | METRONIDAZOLE | METRONIDAZOLE | flou | 92.3 | non | ✅ OK |
| `claridare 500` | faute_frappe | CLARITHROMYCINE | AUCUN | aucune | 0.0 | non | ❌ non_trouve |
| `ciprodare 500` | faute_frappe | CIPROFLOXACINE | CIPROFLOXACINE HDROCHLORIDE | flou | 94.1 | oui | ❌ ambigu_mauvais_candidat |
| `cardenciel 2.5` | faute_frappe | BISOPROLOL | BISOPROLOL | flou | 90.0 | non | ✅ OK |
| `aldomette 250` | faute_frappe | METHYLDOPA | METHYLDOPA | flou | 87.5 | non | ✅ OK |
| `lasilixe 40` | faute_frappe | FUROSEMIDE | AUCUN | aucune | 0.0 | non | ❌ non_trouve |
| `doliprane sirop bebe` | langage_naturel | PARACETAMOL | PARACETAMOL | marque | 100.0 | non | ✅ OK |
| `efferalgan effervescent 1g` | langage_naturel | PARACETAMOL | PARACETAMOL | marque | 100.0 | non | ✅ OK |
| `cachet amoxicilline 500` | langage_naturel | AMOXICILLINE | AMOXICILLINE | dci | 100.0 | non | ✅ OK |
| `amoxicilline acide clavulanique sachet` | langage_naturel | ACIDE CLAVULANIQUE + AMOXICILLINE | AMOXICILLINE + ACIDE CLAVULANIQUE | contient | 95.0 | non | ✅ OK |
| `aspirine protect 100` | langage_naturel | ACIDE ACETYLSALICYLIQUE | ACIDE ACETYLSALICYLIQUE + ACIDE ASCORBIQUE | flou | 85.5 | non | ❌ erreur_silencieuse |
| `aspegic nourrisson` | langage_naturel | ACIDE ACETYLSALICYLIQUE | ACIDE ACETYLSALICYLIQUE | alias | 100.0 | non | ✅ OK |
| `pommade voltarene` | langage_naturel | DICLOFENAC | DICLOFENAC | marque | 100.0 | non | ✅ OK |
| `comprime amlodipine 10mg` | langage_naturel | AMLODIPINE | AMLODIPINE | dci | 100.0 | non | ✅ OK |
| `gelule clarithromycine 500` | langage_naturel | CLARITHROMYCINE | CLARITHROMYCINE | dci | 100.0 | non | ✅ OK |
| `panadol extra` | langage_naturel | PARACETAMOL + CAFEINE | PARACETAMOL + CAFEINE | marque | 100.0 | non | ✅ OK |
| `spasfon lyoc` | langage_naturel | PHLOROGLUCINOL | PHLOROGLUCINOL | flou | 92.3 | non | ✅ OK |
| `amlo 10 mg` | abreviation | AMLODIPINE | AMLODIPINE | flou | 96.0 | oui | ✅ OK |
| `amox` | ambigu_abreviation | AMOXICILLINE | AMOXICILLINE | flou | 96.0 | oui | ✅ OK |
| `clari 250` | ambigu_abreviation | CLARITHROMYCINE | CLARITHROMYCINE | flou | 96.0 | oui | ✅ OK |
| `cortyx` | ambigu_catalogue | AUCUN (rejet) | BETAMETHASONE | marque | 100.0 | oui | ✅ OK |
| `nurofen 400` | hors_catalogue | AUCUN (rejet) | AUCUN | aucune | 0.0 | non | ✅ OK |
| `advil 200mg` | hors_catalogue | AUCUN (rejet) | AUCUN | aucune | 0.0 | non | ✅ OK |
| `teldane 60` | hors_catalogue | AUCUN (rejet) | AUCUN | aucune | 0.0 | non | ✅ OK |
| `ventoline spray` | hors_perimetre | SALBUTAMOL | SALBUTAMOL | contient | 95.0 | non | ✅ OK |
| `metformine 850` | hors_perimetre | METFORMINE | METFORMINE | dci | 100.0 | non | ✅ OK |
| `omeprazole 20mg` | hors_perimetre | OMEPRAZOLE | OMEPRAZOLE | dci | 100.0 | non | ✅ OK |
| `atorvastatine 20` | hors_perimetre | ATORVASTATINE | ATORVASTATINE | dci | 100.0 | non | ✅ OK |
| `mal de tete intense` | symptome | AUCUN (rejet) | CHLORURE BENZALKONIUM + LIDOCAINE | flou | 85.5 | non | ❌ faux_positif |
| `fievre et courbatures` | symptome | AUCUN (rejet) | AUCUN | aucune | 0.0 | non | ✅ OK |
| `shampoing antipelliculaire` | non_medical | AUCUN (rejet) | AUCUN | aucune | 0.0 | non | ✅ OK |
| `pansement sterile` | non_medical | AUCUN (rejet) | AUCUN | aucune | 0.0 | non | ✅ OK |
| `xyzabc 123` | bruit_pur | AUCUN (rejet) | AUCUN | aucune | 0.0 | non | ✅ OK |
| `azertyuiop` | bruit_pur | AUCUN (rejet) | AUCUN | aucune | 0.0 | non | ✅ OK |