# 6. Évaluation et benchmark

## Le problème

La semaine 3 ajoute trois mécanismes à la recherche : normalisation des requêtes,
boost par métadonnées et expansion par le graphe. Le lot L4 a mesuré leurs gains,
mais sur les questions qui ont servi à régler leurs poids, et avec un rapport
encore partiel. Il fallait une évaluation reproductible, sur un jeu de questions
explicite, couvrant aussi les garde-fous : reconnaître les entités, classer
l'intention et savoir s'abstenir.

## Protocole

- **23 questions** : Q1–Q22 et la variante Q3f, dont **19 positives avec passage
  gold** et 4 questions sans gold (méta, hors périmètre).
- **5 questions ajoutées** pour couvrir les cas du plan : marque (Q18), synonyme
  de classe (Q19), faute de frappe (Q20), hors périmètre (Q21) et conflit entre
  sources (Q22).
- **Trois modes** : `raw` (recherche de la semaine 2, inchangée), `normalized`
  (variantes DCI/classes + boost métadonnées) et `graph` (expansion L3).
- **Trois méthodes** : BM25, dense et hybride, top-100.
- **Gold vérifié** : les 40 identifiants de passage et les 12 contrôles de la
  semaine 2 sont validés dans `corpus.jsonl` par `scripts/check_gold.py`.

Toutes les métriques sont calculées par `run_week3_evaluation` ; une seule
commande régénère ce rapport.

## Résultats

| Méthode | Mode | MRR@100 | Hit@10 | Recall@10 | nDCG@10 | Médiane (ms) |
|---|---|---:|---:|---:|---:|---:|
| BM25 | raw | 0,100 | 0,211 | 0,145 | 0,086 | 0,5 |
| BM25 | normalized | 0,521 | 0,789 | 0,763 | 0,576 | 4,8 |
| BM25 | graph | 0,305 | 0,474 | 0,421 | 0,309 | 0,7 |
| Dense | raw | 0,165 | 0,316 | 0,263 | 0,161 | 18,4 |
| Dense | normalized | **0,576** | 0,737 | 0,737 | **0,614** | 22,9 |
| Dense | graph | 0,384 | 0,632 | 0,579 | 0,408 | 18,6 |
| Hybride | raw | 0,242 | 0,316 | 0,316 | 0,255 | 18,6 |
| Hybride | normalized | 0,571 | **0,789** | **0,763** | **0,614** | 25,0 |
| Hybride | graph | 0,464 | 0,632 | 0,579 | 0,476 | 18,7 |

Lecture :

1. **La normalisation est le gain principal.** En BM25, le MRR passe de 0,100 à
   0,521 et le Hit@10 de 0,211 à 0,789 : les marques, les fautes de frappe et les
   classes sont enfin retrouvées. Le mode normalisé est aussi le seul à faire
   remonter Q1, Q7, Q8, Q11, Q13, Q14, Q15 et Q19 au rang 1.
2. **Le graphe règle les interactions de classe.** Q2 (ibuprofène + aspirine),
   Q3 (amlodipine + ibuprofène), Q16 (amlodipine + AINS) et Q19 (AINS + IEC)
   passent à un MRR de 1,0 ou 0,5. C'est exactement la mission Q3 du projet :
   la preuve est trouvée au niveau des classes, pas par une fausse arête directe.
3. **Les deux signaux sont complémentaires.** La normalisation seule laisse Q2,
   Q3 et Q16 sous 0,5 ; le graphe seul laisse les questions d'identité (marques,
   dosages) à leur niveau brut. Le mode hybride normalisé offre le meilleur
   compromis Hit@10 (0,789) pour une latence médiane de 25 ms, sous l'objectif
   de 50 ms.

## Questions ajoutées (L5)

| Question | Attendu | Résultat (hybride, meilleur mode) |
|---|---|---|
| Q18 — DOLIPRANE, plusieurs dosages ? | PARACETAMOL | MRR 0,50 (normalisé et graphe) |
| Q19 — AINS + IEC ? | AINS + IEC | MRR 1,00 (normalisé et graphe) |
| Q20 — « paracétamole » (faute) | PARACETAMOL | MRR 0,50 (normalisé) |
| Q21 — médicament pour une angine | abstention | abstention correcte |
| Q22 — marques de ramipril | 3 registres | MRR 1,00 (tous modes) |

La faute de frappe est récupérée par le repli flou de L2, puis le boost de
registre fait remonter la fiche DCI. Q22 montre aussi que le désaccord entre
sources ne dégrade pas la recherche : les trois fiches registre sont trouvées.

## Métriques d'analyse

| Métrique | Valeur | Détail |
|---|---:|---|
| Entity F1 | 0,957 | 22 questions sur 23 parfaites |
| Intent accuracy | 0,957 | 22 sur 23 |
| Abstention accuracy | 0,957 | 22 sur 23 |

**Cas d'erreur concret (Q4).** La question méta « Deux sources donnent une dose
maximale différente : que doit répondre le système ? » produit deux faux
positifs de L2 :

- le mot « différente » est rapproché en flou de `FER` (entité inventée) ;
- la tournure « que doit répondre » déclenche le motif de conseil médical, donc
  `out_of_scope=True`.

Conséquence : Entity F1 = 0 et abstention fausse. La correction appartient au
lot L2 : ajouter « différente » aux mots non médicamenteux et restreindre le
motif « que doit » aux formulations de conseil (« que doit-il faire »). Le cas
est conservé comme test de non-régression dans l'évaluation.

## Régressions

Sept couples (question, méthode, mode) reculent par rapport au mode brut. Les
plus visibles :

- **Q3 en BM25 normalisé** : 0,250 → 0,048. La question est longue et contient
  beaucoup de mots cliniques ; les variantes DCI/classes pèsent trop lourd face
  à la formulation d'origine.
- **Q10 en normalisé et graphe** (BM25, dense, hybride) : la fiche
  « amoxicilline + acide clavulanique » est concurrencée par les nombreuses
  associations contenant « amoxicilline ».
- **Q17 en BM25 normalisé** : 0,038 → 0,034, écart marginal.

Piste : pondérer les variantes selon l'intention (moins de poids « classes » sur
les questions longues de type interaction) et n'injecter la fiche registre que
si la question porte sur l'identité du médicament. C'est un réglage L4, pas une
correction L5 ; il devra être validé sur des questions non utilisées pour le
réglage.

## Limites

- **Mesure optimiste** : les poids de L4 ont été ajustés sur ces mêmes questions.
  Le gain réel devra être confirmé sur un jeu tenu à l'écart.
- **Gold partiel** : le Thésaurus décrit chaque paire dans les deux sens ; le gold
  ne contient souvent qu'un des deux passages, ce qui sous-estime le rappel.
- **Échantillon** : 19 questions positives suffisent pour comparer les modes,
  pas pour conclure sur une performance clinique générale.
- **Latence** : mesurée sur CPU, sans mise en cache entre questions.

## Reproduction

```powershell
.venv\Scripts\python.exe scripts\check_gold.py
.venv\Scripts\python.exe scripts\14_eval_week3.py
.venv\Scripts\python.exe -m pytest tests -q
```

Le rapport détaillé est dans `data/processed/week_3/eval_week3.md` ; la
comparaison BM25/dense/hybride de la semaine 2 est régénérée dans
`data/processed/week_2/retrieval_comparison.md`.
