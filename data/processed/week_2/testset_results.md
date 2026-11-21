# Évaluation sur le jeu de test (41 questions) — Semaine 2

Corpus : 9977 chunks. 25 questions avec passage gold sur 41. Méthodes : bm25, dense, hybrid.

Hit@10 = au moins un chunk gold dans le top 10. Recall@k = part des chunks gold retrouvés. Les questions à gold multiple (C07, T02) ont un Recall structurellement bas : Hit@10 et MRR sont les métriques principales.

## Résultats globaux

| Méthode | hit@10 | recall@10 | recall@50 | mrr | ndcg@10 |
|---|---|---|---|---|---|
| bm25 | 0.520 | 0.422 | 0.698 | 0.331 | 0.344 |
| dense | 0.520 | 0.405 | 0.543 | 0.419 | 0.388 |
| hybrid | 0.600 | 0.443 | 0.770 | 0.413 | 0.394 |

## Par type de question (Hit@10 / MRR)

| Type | n | bm25 Hit@10 | bm25 MRR | dense Hit@10 | dense MRR | hybrid Hit@10 | hybrid MRR |
|---|---|---|---|---|---|---|---|
| direct | 10 | 0.50 | 0.25 | 0.80 | 0.60 | 0.90 | 0.54 |
| cross | 9 | 0.67 | 0.49 | 0.22 | 0.22 | 0.33 | 0.28 |
| context | 3 | 0.00 | 0.06 | 0.00 | 0.00 | 0.00 | 0.02 |
| trap | 3 | 0.67 | 0.38 | 1.00 | 0.83 | 1.00 | 0.78 |

## Détail par question

| Id | Type | Question | bm25 rang MRR | dense rang MRR | hybrid rang MRR |
|---|---|---|---|---|---|
| D01 | direct | Quel est le dosage disponible du paracétamol ? | 0.00 | 0.17 | 0.02 |
| D02 | direct | Quelles formes et quels dosages du ramipril sont enregistrés… | 1.00 | 1.00 | 1.00 |
| D03 | direct | Quelles marques de clarithromycine sont enregistrées en Algé… | 0.02 | 1.00 | 1.00 |
| D04 | direct | Quelle est la DCI du médicament TRIATEC ? | 0.33 | 0.06 | 0.33 |
| D05 | direct | Quelle est la DCI du médicament DOLIPRANE ? | 0.04 | 0.06 | 0.10 |
| D06 | direct | Le bisoprolol est-il enregistré en Algérie, et sous quelles … | 0.33 | 1.00 | 1.00 |
| D07 | direct | Quelles sont les indications thérapeutiques du DOLIPRANE 2.4… | 0.50 | 1.00 | 1.00 |
| D08 | direct | Quelles sont les contre-indications du gel KOPROFEN selon so… | 0.09 | 1.00 | 0.25 |
| D09 | direct | Quels sont les effets indésirables du gel KOPROFEN selon son… | 0.17 | 0.50 | 0.50 |
| D10 | direct | Quelles sont les contre-indications du BIOFENAC selon son RC… | 0.07 | 0.20 | 0.20 |
| C01 | cross | Peut-on associer l'ibuprofène et le ramipril ? Quel est le n… | 0.00 | 0.00 | 0.00 |
| C02 | cross | Peut-on associer l'ibuprofène et l'aspirine ? Quel est le ni… | 0.00 | 0.00 | 0.00 |
| C03 | cross | Peut-on associer le ramipril et la spironolactone ? | 0.12 | 0.00 | 0.04 |
| C04 | cross | Peut-on associer la ciprofloxacine et la caféine ? Quel nive… | 1.00 | 0.00 | 0.05 |
| C05 | cross | Peut-on prendre des sels de calcium avec la ciprofloxacine ? | 1.00 | 0.00 | 0.33 |
| C06 | cross | Quelle précaution pour l'association amlodipine et simvastat… | 1.00 | 0.00 | 0.09 |
| C07 | cross | Quels équivalents enregistrés en Algérie si l'amoxicilline +… | 1.00 | 1.00 | 1.00 |
| C08 | cross | Quels équivalents enregistrés si le TRIATEC est en rupture ? | 0.25 | 1.00 | 1.00 |
| C09 | cross | Quelles associations avec la clarithromycine sont déconseill… | 0.04 | 0.00 | 0.02 |
| P01 | context | Pour un patient hypertendu âgé qui prend déjà de l'amlodipin… | 0.09 | 0.00 | 0.03 |
| P02 | context | Un patient de 72 ans prend du ramipril et de l'hydrochloroth… | 0.05 | 0.00 | 0.02 |
| P03 | context | Un patient hypertendu sous bisoprolol peut-il prendre de l'i… | 0.02 | 0.00 | 0.01 |
| T02 | trap | Quels dosages d'amlodipine sont enregistrés en Algérie ? | 0.14 | 0.50 | 0.33 |
| T03 | trap | Combien de marques de ramipril sont enregistrées en Algérie … | 1.00 | 1.00 | 1.00 |
| T04 | trap | Dans quelle classe thérapeutique se trouve la clarithromycin… | 0.00 | 1.00 | 1.00 |

## Lookup exact du Thésaurus vs BM25 (questions d'interaction)

| Id | Exact Hit@10 | BM25 Hit@10 | Exact MRR | BM25 MRR | Top-1 exact |
|---|---:|---:|---:|---:|---|
| C01 | 0 | 0 | 0.08 | 0.00 | `thesaurus:anti inflammatoires non steroidiens:56:18` |
| C02 | 1 | 0 | 1.00 | 0.00 | `thesaurus:anti inflammatoires non steroidiens:56:3` |
| C03 | 1 | 1 | 0.20 | 0.12 | `thesaurus:diuretiques epargneurs de potassium seuls ou associes:191:0` |
| C04 | 1 | 1 | 1.00 | 1.00 | `thesaurus:cafeine:108:0` |
| C05 | 1 | 1 | 1.00 | 1.00 | `thesaurus:calcium:110:1` |
| C06 | 1 | 1 | 1.00 | 1.00 | `thesaurus:amlodipine:32:0` |
| C09 | 0 | 0 | 0.04 | 0.04 | `thesaurus:inhibiteurs puissants du cyp3a4:311:0` |
| P01 | 0 | 0 | 0.00 | 0.09 | `—` |
| P02 | 0 | 0 | 0.08 | 0.05 | `thesaurus:anti inflammatoires non steroidiens:56:18` |
| P03 | 0 | 0 | 0.06 | 0.02 | `thesaurus:anti inflammatoires non steroidiens:56:18` |

Exact Hit@10 moyen : 0.50 — BM25 Hit@10 moyen : 0.40.

## Questions hors périmètre (filtre actuel `is_out_of_scope`)

| Id | Question | Refusée ? | Raison |
|---|---|---|---|
| O01 | Quel médicament prendre pour mes douleurs dentaires ? | oui | Aucun médicament de la liste détecté. |
| O02 | Quelle dose d'ibuprofène dois-je donner à mon fils de 3 ans  | oui | Demande de conseil médical personnalisé, d'ordonnance ou de diagnostic. |
| O03 | J'ai de la fièvre et mal à la gorge, est-ce une angine ? | oui | Demande de conseil médical personnalisé, d'ordonnance ou de diagnostic. |
| O04 | Peux-tu me rédiger une ordonnance d'amoxicilline pour mon vo | oui | Demande de conseil médical personnalisé, d'ordonnance ou de diagnostic. |
| O05 | Quel est le meilleur complément alimentaire pour mieux dormi | oui | Aucun médicament de la liste détecté. |
| O06 | Quelle est la capitale de l'Algérie ? | oui | Aucun médicament de la liste détecté. |
| O07 | Mon père prend du ramipril et se plaint de vertiges, que doi | oui | Demande de conseil médical personnalisé, d'ordonnance ou de diagnostic. |
| U06 | Quel est le prix et le taux de remboursement du DOLIPRANE 10 | oui | Aucun médicament de la liste détecté. |

Refus corrects : 8/8 évaluées (8 questions hors périmètre au total).
