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

Mesurés sur les 40 questions qui ont un passage de référence (celles de `evaluation.py` et celles du jeu de test de la semaine 2) :

| Recherche | MRR avant | Hit@10 avant | MRR après | Hit@10 après | Temps médian après |
|---|---:|---:|---:|---:|---:|
| BM25 | 0,23 | 0,40 | 0,77 | 0,93 | 8 ms |
| Dense | 0,31 | 0,45 | 0,79 | 0,90 | 40 ms |
| **Hybride** | 0,35 | 0,53 | **0,82** | **0,93** | 41 ms |

« Avant » est la recherche de la semaine 2 ; « après » est le mode normalisé + graphe. En hybride, une bonne réponse figure dans les dix premiers résultats pour 37 questions sur 40, contre 21 avant.

Les deux mécanismes se complètent. La normalisation seule règle surtout les questions de marques et de dosages ; le graphe seul règle surtout les interactions. Le détail par mode est dans `data/processed/week_3/l4_enriched_retrieval.md`.

Les questions que le plan désignait (MRR en hybride) :

| Question | Avant | Après |
|---|---:|---:|
| Q1 — dosages du paracétamol | 0,04 | 0,33 |
| Q2 — ibuprofène et aspirine | 0,00 | 1,00 |
| Q3 — patient sous amlodipine, ibuprofène | 0,06 | 1,00 |
| Q16 — amlodipine et AINS | 0,00 | 0,50 |

Sur les 40 questions et les trois méthodes, une seule recule par rapport à la semaine 2 : Q10 en BM25, qui passe du rang 25 au rang 33.

Le temps médian respecte l'objectif de 50 ms. Les 5 % de requêtes les plus lentes prennent 54 ms, juste au-dessus, presque entièrement à cause de l'encodage de la question (environ 31 ms sur CPU).

## Ce que ces chiffres ne disent pas

**Ils sont optimistes.** Les bonus et les poids ont été ajustés en regardant ces 40 questions. Il faut mesurer le gain sur des questions qui n'ont pas servi au réglage avant de le présenter comme une performance générale.

**Une partie des « erreurs » n'en sont pas.** Le Thésaurus décrit chaque paire dans les deux sens, « AINS + IEC » et « IEC + AINS », en deux passages. Les listes de référence n'en contiennent souvent qu'un : quand la recherche renvoie l'autre, la mesure compte une erreur.

**Une vraie erreur a été trouvée en route.** La première version donnait un bonus au RCP de MIBRAVAL pour une question sur l'amlodipine, parce que sa DCI contient « amlodipine ». Mais MIBRAVAL associe amlodipine et valsartan, et son avertissement sur les AINS concerne le valsartan. Le système aurait répondu à une question sur un médicament avec l'interaction d'un autre. Le bonus est désormais réservé aux RCP du médicament seul. Ce cas montre ce que le contrôle des citations de la semaine 5 devra aussi intercepter.

**La recherche dense seule reste fragile** sur la question du patient sous amlodipine (MRR 0,17) : le modèle préfère d'autres passages sur l'amlodipine à la preuve par classe. L'hybride n'a pas ce défaut ; c'est le mode à utiliser.

## Vérification

`tests/test_retrieval_integration.py` contient 15 tests ; la suite complète passe (65 tests). Ils vérifient que le mode par défaut reproduit la semaine 2, qu'une question vide ne plante pas, que la paire ibuprofène + aspirine, ratée en brut, est trouvée en enrichi, que l'absence amlodipine + AINS est signalée avec des preuves toutes marquées indirectes, que chaque résultat enrichi s'explique, que le temps reste sous 50 ms, et que le découpage des passages longs du corpus fonctionne toujours.

Deux ajouts servent toute l'équipe : `tests/conftest.py` permet de lancer `pytest tests` sans réglage particulier, sous Ubuntu comme sous Windows, et `pytest` figure désormais dans `requirements.txt`. `Retriever(load_dense=False)` charge BM25 sans le modèle, ce qui rend les tests rapides.

Pour reproduire :

```bash
python scripts/05_clean_thesaurus.py
python scripts/08_build_index.py
python -m pytest tests -q
python scripts/20_eval_enriched_retrieval.py
```

Fichiers : `src/pharmeazor/enrich.py`, `src/pharmeazor/retrieval.py`, `src/pharmeazor/embeddings.py`, `tests/test_retrieval_integration.py`, `tests/conftest.py`, `scripts/20_eval_enriched_retrieval.py`.
