# 5. Recherche enrichie

## Le problème

En semaine 2, la recherche échouait chaque fois que la question et le passage ne disaient pas la même chose avec les mêmes mots. Un pharmacien écrit « ibuprofène » ; le Thésaurus écrit « anti-inflammatoires non stéroïdiens ». Il écrit « TRIATEC » ; les registres écrivent « ramipril ». Il écrit « aspirine » ; le Thésaurus écrit « acide acétylsalicylique ». Sur ces questions, BM25 ne trouvait rien et la recherche dense guère mieux.

La semaine 3 a produit de quoi combler cet écart : un lexique qui relie marques, DCI et classes, une analyse de requête qui reconnaît les médicaments d'une question, et un graphe qui relie les classes à leurs interactions. Ce lot branche ces trois briques sur la recherche, sans rien changer à la recherche de la semaine 2.

## Ce qui change pour l'appelant

Une seule méthode, deux options :

```python
results = retriever.search(question, k=10, method="hybrid", normalize=True, expand=True)
```

Sans `normalize` ni `expand`, `search()` renvoie exactement ce qu'elle renvoyait en semaine 2 ; des tests le vérifient question par question. Avec les options, chaque résultat porte en plus un champ `signals` qui dit pourquoi il est là :

```
thesaurus:anti inflammatoires non steroidiens:56:13   ['graph:class@1', 'boost:thesaurus_pair']
```

Lu en clair : ce passage est arrivé premier dans la liste du graphe, par une classe, et sa substance comme sa cible correspondent aux deux médicaments de la question. `return_trace=True` renvoie en plus ce que la recherche a compris de la question : intention, médicaments reconnus, variantes cherchées, paires trouvées ou absentes dans le graphe.

## Comment ça marche

**La question est cherchée sous trois formes.** Telle quelle ; réécrite avec les DCI (« TRIATEC » devient « RAMIPRIL ») ; réécrite avec les classes (« AINS », « IEC »). Les trois classements sont fusionnés, la question d'origine pesant le plus. Seule la question d'origine passe par le modèle d'embedding : les deux réécritures sont des listes de termes, BM25 suffit, et encoder trois textes triplait le temps de réponse.

**Les fiches du bon médicament sont ajoutées d'office.** Pour une question sur les marques, les formes ou les équivalents, les fiches des registres de la DCI entrent dans les candidats même quand la formulation ne les a pas fait remonter. Pour une question d'interaction, jamais : les registres n'en disent rien.

**Les métadonnées départagent.** Un passage du Thésaurus dont la substance et la cible sont les deux médicaments de la question gagne un bonus. Un RCP de l'ANPP gagne un bonus s'il porte sur le médicament demandé et si sa section correspond à la question (indications, posologie, interactions, effets indésirables…), et un autre si la marque citée est celle du produit.

**Le graphe apporte les interactions de classe.** Pour chaque paire de médicaments, on cherche dans le graphe les interactions qui touchent l'un d'un côté et l'autre de l'autre, directement ou par une de leurs classes. Ibuprofène + ramipril n'a pas d'entrée propre, mais AINS + IEC en a une.

**Quand il n'y a rien, on le dit.** Le Thésaurus n'a aucune entrée pour amlodipine + AINS. Dans ce cas, la recherche note l'absence dans la trace, puis propose les interactions des AINS avec des classes proches de l'amlodipine : IEC, ARA II, bêta-bloquants, diurétiques, tous des antihypertenseurs. Ces passages sont étiquetés `related_class`. C'est une preuve indirecte, et elle ne doit jamais être présentée comme une interaction directe ; un test vérifie qu'aucun de ces passages ne porte une autre étiquette.

Un détail technique a compté : les interactions du graphe ne pointent vers aucun passage du corpus. Elles y sont rattachées par leur libellé, ce qui fonctionne pour 3 214 des 3 218 interactions.

## Résultats

Une seule évaluation fait foi : `python scripts/14_eval_week3.py`, qui écrit `data/processed/week_3/eval_week3.md`. Elle compare quatre modes (brut, normalisé, graphe, normalisé + graphe) sur trois méthodes, question par question.

**Sur des questions qui n'ont pas servi au réglage.** Les poids de ce lot ont été ajustés en regardant des questions de test. Pour mesurer le gain sans ce biais, dix questions nouvelles (H01 à H10) ont été écrites et enregistrées avant leur première évaluation, sur des médicaments et des paires absents de toutes les questions existantes : losartan, COVERSYL, BIODAZOLE, CEBREX, doxycycline + fer, tramadol + fluoxétine, diclofénac + losartan, méthotrexate + kétoprofène, amiloride + potassium, nébivolol + amiodarone. Les poids n'ont pas été modifiés depuis ; une empreinte de `enrich.py` enregistrée avec les questions le garantit.

| Hybride, 10 questions tenues à l'écart | Brut (semaine 2) | Normalisé + graphe |
|---|---:|---:|
| MRR | 0,230 | 0,848 |
| Hit@10 | 0,50 | 1,00 |

Une bonne réponse figure dans les dix premiers résultats pour les dix questions, contre cinq avant. Dix questions donnent un ordre de grandeur, pas une preuve.

**Pourquoi deux chiffres circulaient (0,820 et 0,571).** La semaine 3 a publié MRR 0,820 dans cette section et 0,571 dans la section 6. Les deux étaient justes et ne mesuraient pas la même chose. L'évaluation les recalcule désormais dans la même exécution :

| Hybride, MRR | Normalisé | Normalisé + graphe |
|---|---:|---:|
| 40 questions ayant servi au réglage (ancien chiffre de cette section) | 0,719 | **0,820** |
| 19 questions de la section 6 | **0,571** | 0,679 |
| 10 questions tenues à l'écart | 0,764 | 0,848 |

Sur les mêmes questions, passer du mode normalisé au mode normalisé + graphe vaut environ 0,11 (0,571 → 0,679) ; à mode égal, les questions de la section 6 sont plus difficiles d'environ 0,14 (0,679 contre 0,820). Le 0,571 mesurait la moitié du mécanisme, le 0,820 le mécanisme complet sur des questions qui avaient servi à le régler.

Les questions que le plan désignait (hybride, MRR, brut → normalisé + graphe) : Q1 0,02 → 0,33 ; Q2 0,00 → 1,00 ; Q3 0,04 → 1,00 ; Q16 0,00 → 0,50.

**Temps de réponse.** En hybride normalisé + graphe : médiane 40 ms, 95e percentile 44 ms, sous l'objectif de 50 ms. L'essentiel vient de l'encodage de la question par le modèle (environ 31 ms sur CPU).

## Ce que ces chiffres ne disent pas

**Une question se dégrade, et ce n'est pas une affaire de poids.** H09 (« sels de potassium chez un patient sous amiloride ») : BM25 brut trouve la bonne réponse au premier rang, le mode normalisé la fait tomber au septième. Le lexique résout « amiloride » vers l'association « amiloride + hydrochlorothiazide » et ne reconnaît pas « potassium » comme un médicament : les réécritures cherchent donc le mauvais produit. La correction relève du lexique ; les poids de la recherche n'ont pas été touchés, sans quoi le jeu ne serait plus tenu à l'écart.

**Une réponse de référence était fausse, et la recherche avait raison.** La première version de H06 (tramadol + fluoxétine) n'attendait que l'entrée de classe, ISRS + tramadol, niveau « à prendre en compte ». Le Thésaurus contient aussi une entrée directe, fluoxétine + tramadol, niveau « association déconseillée » : plus grave. La recherche plaçait ces passages en tête ; c'est la référence qui sous-estimait le risque. Elle a été corrigée après la première exécution, et la correction est notée dans le fichier des questions. C'est exactement l'erreur que le système ne doit jamais commettre : présenter un niveau d'interaction adouci.

**Un passage de H07 n'est pas neuf.** La paire diclofénac + losartan est nouvelle, mais le passage attendu (AINS + ARA II) était déjà une réponse de référence de Q3. La question est tenue à l'écart, ce passage ne l'est pas.

**Les références des questions plus anciennes restent incomplètes.** Le Thésaurus décrit chaque paire dans les deux sens (« AINS + IEC » et « IEC + AINS »), et les références des questions de la section 6 n'en contiennent souvent qu'un : quand la recherche renvoie l'autre, la mesure compte une erreur. Les références de H01 à H10 contiennent les deux sens.

**Une erreur évitée pendant le développement.** La première version donnait un bonus au RCP de MIBRAVAL pour une question sur l'amlodipine, parce que sa DCI contient « amlodipine ». MIBRAVAL associe amlodipine et valsartan, et son avertissement sur les AINS concerne le valsartan. Le bonus est réservé aux RCP du médicament seul. Le contrôle des citations de la semaine 5 devra intercepter ce type d'attribution.

**La recherche dense seule reste fragile** sur Q3 (patient sous amlodipine) : 0,17 contre 1,00 en hybride. L'hybride est le mode à utiliser.

## Vérification

`tests/test_retrieval_integration.py` contient 15 tests. Ils vérifient que le mode par défaut reproduit la semaine 2, qu'une question vide ne plante pas, que la paire ibuprofène + aspirine, ratée en brut, est trouvée en enrichi, que l'absence amlodipine + AINS est signalée avec des preuves toutes marquées indirectes, que chaque résultat enrichi s'explique, que le temps reste sous 50 ms, et que le découpage des passages longs du corpus fonctionne toujours. Le mode normalisé + graphe est aussi testé dans `tests/test_evaluation.py`.

`tests/conftest.py` permet de lancer `pytest tests` sans réglage particulier, sous Ubuntu comme sous Windows. `Retriever(load_dense=False)` charge BM25 sans le modèle, ce qui rend les tests rapides.

Pour reproduire :

```bash
python scripts/05_clean_thesaurus.py
python scripts/08_build_index.py
python scripts/21_build_heldout.py      # recrée les 10 questions (empreinte attendue : 929badcfdcda)
python -m pytest tests -q
python scripts/14_eval_week3.py
```

Fichiers : `src/pharmeazor/enrich.py`, `src/pharmeazor/retrieval.py`, `src/pharmeazor/embeddings.py`, `tests/test_retrieval_integration.py`, `tests/conftest.py`, `scripts/21_build_heldout.py`, `data/processed/week_3/heldout_questions.json`.
