import math
import statistics
import time
from collections import Counter

from .query import analyze_query
from .retrieval import Retriever
from .textnorm import norm


QUERIES = [
    {
        "id": "Q1",
        "type": "positive",
        "question": "Quel est le dosage disponible du paracétamol ?",
        "gold": ["nomenclature:paracetamol"],
    },
{
    "id": "Q2",
    "type": "positive",
    "question": "Peut-on associer l'ibuprofène et l'aspirine ? Quel est le niveau d'interaction ?",
    "gold": [
        "thesaurus:anti inflammatoires non steroidiens:56:1",
        "thesaurus:acide acetylsalicylique:5:3",
        "thesaurus:antiagregants plaquettaires:45:2",
    ],
},
    {
        "id": "Q3",
        "type": "positive",
        "question": (
            "Pour un patient hypertendu âgé qui prend déjà régulièrement de "
            "l'Amlodipine, est-il possible de lui associer de l'Ibuprofène pour "
            "traiter des douleurs articulaires ? Quel est le niveau d'interaction "
            "documenté, quelles sont les précautions ou contre-indications "
            "spécifiques, quelle est la posologie maximale recommandée, et que "
            "disent les sources officielles à ce sujet ?"
        ),
        "gold": [
            "thesaurus:anti inflammatoires non steroidiens:56:2",
            "thesaurus:anti inflammatoires non steroidiens:56:5",
            "thesaurus:anti inflammatoires non steroidiens:56:9",
            "thesaurus:anti inflammatoires non steroidiens:56:13",
        ],
    },
    {
        "id": "Q3f",
        "type": "positive",
        "variant": True,
        "question": "interaction anti-inflammatoires non stéroïdiens et antihypertenseurs",
        "gold": [
            "thesaurus:anti inflammatoires non steroidiens:56:2",
            "thesaurus:anti inflammatoires non steroidiens:56:5",
            "thesaurus:anti inflammatoires non steroidiens:56:9",
            "thesaurus:anti inflammatoires non steroidiens:56:13",
        ],
    },
    {
        "id": "Q4",
        "type": "meta",
        "question": "Deux sources donnent une dose maximale différente : que doit répondre le système ?",
        "gold": [],
    },
    {
        "id": "Q5",
        "type": "negative",
        "question": "Quel médicament prendre pour mes douleurs dentaires ?",
        "gold": [],
    },

    # --- Antalgiques / AINS ---
    {
        "id": "Q6",
        "type": "positive",
        "question": "Quelles sont les marques de paracétamol enregistrées en Algérie ?",
        "gold": ["nomenclature:paracetamol", "pharmnet:paracetamol"],
    },
    {
        "id": "Q7",
        "type": "positive",
        "question": "Quelle est la posologie maximale de l'ibuprofène chez l'adulte ?",
        "gold": ["nomenclature:ibuprofene", "pharmnet:ibuprofene"],
    },
    {
        "id": "Q8",
        "type": "positive",
        "question": "L'aspirine est-elle contre-indiquée avec les anticoagulants oraux ?",
        "gold": [
            "thesaurus:acide acetylsalicylique:5:2",
            "thesaurus:anticoagulants oraux:49:1",
        ],
    },
    {
        "id": "Q9",
        "type": "positive",
        "question": "Quelles sont les formes disponibles du paracétamol en Algérie ?",
        "gold": ["nomenclature:paracetamol"],
    },
    # --- Antibiotiques ---
    {
        "id": "Q10",
        "type": "positive",
        "question": "Quelles sont les marques d'amoxicilline enregistrées en Algérie ?",
        "gold": ["nomenclature:amoxicilline acide clavulanique"],
    },
    {
        "id": "Q11",
        "type": "positive",
        "question": "Quels sont les dosages disponibles de la clarithromycine ?",
        "gold": ["nomenclature:clarithromycine", "pharmnet:clarithromycine"],
    },
    {
        "id": "Q12",
        "type": "positive",
        "question": "Quelles interactions médicamenteuses existent avec la clarithromycine ?",
        "gold": ["thesaurus:clarithromycine:130:0", "thesaurus:clarithromycine:130:1"],
    },
    {
        "id": "Q13",
        "type": "positive",
        "question": "Quelle est la classe thérapeutique de la clarithromycine ?",
        "gold": ["pharmnet:clarithromycine"],
    },
    # --- Antihypertenseurs ---
    {
        "id": "Q14",
        "type": "positive",
        "question": "Quelles sont les marques d'amlodipine enregistrées en Algérie ?",
        "gold": [
            "nomenclature:amlodipine besilate amlodipine",
            "nomenclature:amlodipine besilate exprime en amlodipine",
        ],
    },
    {
        "id": "Q15",
        "type": "positive",
        "question": "Quelle est la posologie de l'amlodipine ?",
        "gold": ["nomenclature:amlodipine besilate amlodipine"],
    },
    {
        "id": "Q16",
        "type": "positive",
        "question": "Peut-on associer l'amlodipine avec les AINS ?",
        "gold": [
            "thesaurus:anti inflammatoires non steroidiens:56:2",
            "thesaurus:anti inflammatoires non steroidiens:56:5",
        ],
    },
    {
        "id": "Q17",
        "type": "positive",
        "question": "Quelles sont les interactions des inhibiteurs de l'enzyme de conversion ?",
        "gold": ["thesaurus:inhibiteurs de l enzyme de conversion:305:0"],
    },
    # --- Semaine 3 (L5) : marque, synonyme/classe, faute de frappe, hors
    # périmètre et conflit entre sources. Le gold est vérifié par check_gold.py.
    {
        "id": "Q18",
        "type": "positive",
        "question": "Le DOLIPRANE est-il disponible en plusieurs dosages en Algérie ?",
        "gold": ["nomenclature:paracetamol", "pharmnet:paracetamol"],
    },
    {
        "id": "Q19",
        "type": "positive",
        "question": "Peut-on associer un AINS avec un IEC ?",
        "gold": [
            "thesaurus:anti inflammatoires non steroidiens:56:13",
            "thesaurus:inhibiteurs de l enzyme de conversion:305:2",
        ],
    },
    {
        "id": "Q20",
        "type": "positive",
        "question": "Quel est le dosage du paracétamole en Algérie ?",
        "gold": ["nomenclature:paracetamol", "pharmnet:paracetamol"],
    },
    {
        "id": "Q21",
        "type": "negative",
        "question": "Quel médicament prendre pour une angine ?",
        "gold": [],
    },
    {
        "id": "Q22",
        "type": "positive",
        "question": "Quelles marques de ramipril sont enregistrées en Algérie ?",
        "gold": [
            "nomenclature:ramipril",
            "nomenclature_dz:ramipril",
            "pharmnet:ramipril",
        ],
    },
]

METHODS = ("bm25", "dense", "hybrid")
MAX_K = 100
MODES = ("raw", "normalized", "graph", "normalized+graph")

# Métadonnées d'évaluation : entités attendues, intention attendue et
# abstention attendue. Elles servent aux métriques d'analyse (L5) et restent
# séparées du gold de retrieval pour ne pas coupler les deux mesures.
QUERY_META = {
    "Q1": {"gold_entities": ["PARACETAMOL"], "gold_intent": "dosage", "should_abstain": False},
    "Q2": {"gold_entities": ["IBUPROFENE", "ACIDE ACETYLSALICYLIQUE"],
           "gold_intent": "interaction", "should_abstain": False},
    "Q3": {"gold_entities": ["AMLODIPINE", "IBUPROFENE"],
           "gold_intent": "interaction", "should_abstain": False},
    "Q3f": {"gold_entities": ["ANTI-INFLAMMATOIRES NON STEROIDIENS",
                              "ANTIHYPERTENSEURS SAUF ALPHA-BLOQUANTS"],
            "gold_intent": "interaction", "should_abstain": False},
    # Question méta (conflit de sources) : aucune intention clinique, et ce
    # n'est pas une demande de conseil personnalisé.
    "Q4": {"gold_entities": [], "gold_intent": "unknown", "should_abstain": False},
    "Q5": {"gold_entities": [], "gold_intent": "out_of_scope", "should_abstain": True},
    "Q6": {"gold_entities": ["PARACETAMOL"], "gold_intent": "unknown", "should_abstain": False},
    "Q7": {"gold_entities": ["IBUPROFENE"], "gold_intent": "dosage", "should_abstain": False},
    "Q8": {"gold_entities": ["ACIDE ACETYLSALICYLIQUE", "ANTICOAGULANTS ORAUX"],
           "gold_intent": "contraindication", "should_abstain": False},
    "Q9": {"gold_entities": ["PARACETAMOL"], "gold_intent": "unknown", "should_abstain": False},
    "Q10": {"gold_entities": ["AMOXICILLINE"], "gold_intent": "unknown", "should_abstain": False},
    "Q11": {"gold_entities": ["CLARITHROMYCINE"], "gold_intent": "dosage", "should_abstain": False},
    "Q12": {"gold_entities": ["CLARITHROMYCINE"], "gold_intent": "interaction",
            "should_abstain": False},
    "Q13": {"gold_entities": ["CLARITHROMYCINE"], "gold_intent": "unknown",
            "should_abstain": False},
    "Q14": {"gold_entities": ["AMLODIPINE"], "gold_intent": "unknown", "should_abstain": False},
    "Q15": {"gold_entities": ["AMLODIPINE"], "gold_intent": "dosage", "should_abstain": False},
    "Q16": {"gold_entities": ["AMLODIPINE", "ANTI-INFLAMMATOIRES NON STEROIDIENS"],
            "gold_intent": "interaction", "should_abstain": False},
    "Q17": {"gold_entities": ["INHIBITEURS DE L ENZYME DE CONVERSION"],
            "gold_intent": "interaction", "should_abstain": False},
    "Q18": {"gold_entities": ["PARACETAMOL"], "gold_intent": "dosage", "should_abstain": False},
    "Q19": {"gold_entities": ["ANTI-INFLAMMATOIRES NON STEROIDIENS",
                              "INHIBITEURS DE L ENZYME DE CONVERSION"],
            "gold_intent": "interaction", "should_abstain": False},
    "Q20": {"gold_entities": ["PARACETAMOL"], "gold_intent": "dosage", "should_abstain": False},
    "Q21": {"gold_entities": [], "gold_intent": "out_of_scope", "should_abstain": True},
    "Q22": {"gold_entities": ["RAMIPRIL"], "gold_intent": "unknown", "should_abstain": False},
}

for _query in QUERIES:
    _query.update(QUERY_META.get(_query["id"], {}))


def _recall_at(ranked, gold, k):
    if not gold:
        return None
    return len(set(ranked[:k]) & set(gold)) / len(gold)


def _hit_at(ranked, gold, k):
    return 1.0 if set(ranked[:k]) & set(gold) else 0.0


def _mrr(ranked, gold, max_k=MAX_K):
    gold_set = set(gold)
    for rank, chunk_id in enumerate(ranked[:max_k], start=1):
        if chunk_id in gold_set:
            return 1.0 / rank
    return 0.0


def _ndcg_at(ranked, gold, k):
    gold_set = set(gold)
    if not gold_set:
        return None
    dcg = sum(
        1.0 / math.log2(rank + 2)
        for rank, chunk_id in enumerate(ranked[:k])
        if chunk_id in gold_set
    )
    idcg = sum(1.0 / math.log2(rank + 2) for rank in range(min(len(gold_set), k)))
    return dcg / idcg if idcg else 0.0


def _ranked(retriever, question, method, k=MAX_K):
    if method == "dense":
        return [chunk_id for chunk_id, _ in retriever.search_dense(question, k)]
    if method == "bm25":
        return [chunk_id for chunk_id, _ in retriever.search_bm25(question, k)]
    return [chunk_id for chunk_id, _ in retriever.search_hybrid(question, k, pool=k)]


def _labels(values):
    """Normalise des DCI/classes et découpe les associations (« A + B »)."""
    labels = set()
    for value in values or ():
        for part in str(value).split("+"):
            key = norm(part)
            if key:
                labels.add(key)
    return labels


def predicted_entities(analysis):
    """DCI prédites, plus les classes seulement pour les entités sans DCI.

    Une DCI porte des dizaines de classes parentes : les compter toutes
    gonflerait artificiellement le rappel. On évalue donc la DCI quand elle
    existe, et la classe quand la question ne cite qu'une classe (« AINS »).
    """
    labels = set()
    for entity in analysis.entities:
        if entity.dci:
            labels |= _labels([entity.dci])
        else:
            labels |= _labels(entity.classes)
    return labels


def entity_prf(predicted, gold):
    """Précision, rappel et F1 d'ensembles d'entités normalisés."""
    predicted, gold = set(predicted), set(gold)
    if not predicted and not gold:
        return 1.0, 1.0, 1.0
    true_positives = len(predicted & gold)
    precision = true_positives / len(predicted) if predicted else 0.0
    recall = true_positives / len(gold) if gold else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


def analysis_metrics(analysis, query):
    """Métriques L5 d'une analyse : entités, intention et abstention."""
    gold_entities = _labels(query.get("gold_entities", []))
    predicted = predicted_entities(analysis)
    precision, recall, f1 = entity_prf(predicted, gold_entities)
    gold_intent = query.get("gold_intent")
    gold_abstain = bool(query.get("should_abstain", False))
    return {
        "predicted_entities": sorted(predicted),
        "gold_entities": sorted(gold_entities),
        "entity_precision": precision,
        "entity_recall": recall,
        "entity_f1": f1,
        "predicted_intent": analysis.intent,
        "gold_intent": gold_intent,
        "intent_correct": analysis.intent == gold_intent,
        "predicted_abstain": bool(analysis.out_of_scope),
        "gold_abstain": gold_abstain,
        "abstention_correct": bool(analysis.out_of_scope) == gold_abstain,
    }


def _ranked_mode(retriever, question, mode, method, k=MAX_K):
    """Classe les passages selon le mode : brut (sem. 2), normalisé ou graphe."""
    if mode == "raw":
        return _ranked(retriever, question, method, k)
    if mode == "normalized":
        options = {"normalize": True}
    elif mode == "graph":
        options = {"expand": True}
    elif mode == "normalized+graph":
        options = {"normalize": True, "expand": True}
    else:
        raise ValueError(f"Mode inconnu : {mode}")
    results = retriever.search(question, k, method=method, **options)
    return [result["chunk_id"] for result in results]


def _aggregate_retrieval(per_query, queries):
    positives = [
        q for q in queries
        if q["type"] == "positive" and not q.get("variant") and q.get("gold")
    ]
    if not positives:
        return {}
    return {
        metric: sum(per_query[q["id"]][metric] for q in positives) / len(positives)
        for metric in ("recall@10", "recall@50", "hit@10", "mrr", "ndcg@10")
    }


def _aggregate_analysis(analysis_per_query):
    rows = list(analysis_per_query.values())
    if not rows:
        return {}
    return {
        "entity_f1": sum(r["entity_f1"] for r in rows) / len(rows),
        "intent_accuracy": sum(r["intent_correct"] for r in rows) / len(rows),
        "abstention_accuracy": sum(r["abstention_correct"] for r in rows) / len(rows),
    }


def _run_legacy(retriever, queries, k=MAX_K):
    """Rapport historique semaine 2 : trois méthodes, mode brut."""
    per_query = {}

    for query in queries:
        per_query[query["id"]] = {}
        for method in METHODS:
            ranked = _ranked(retriever, query["question"], method, k)
            per_query[query["id"]][method] = {
                "ranked": ranked,
                "recall@10": _recall_at(ranked, query["gold"], 10),
                "recall@50": _recall_at(ranked, query["gold"], 50),
                "hit@10": _hit_at(ranked, query["gold"], 10),
                "mrr": _mrr(ranked, query["gold"]),
                "ndcg@10": _ndcg_at(ranked, query["gold"], 10),
                "sources@10": Counter(
                    retriever.by_id[cid]["source_id"]
                    for cid in ranked[:10]
                    if cid in retriever.by_id
                ),
            }

    positives = [
        q for q in queries if q["type"] == "positive" and not q.get("variant")
    ]
    aggregate = {}
    for method in METHODS:
        aggregate[method] = {
            metric: sum(per_query[q["id"]][method][metric] for q in positives) / len(positives)
            for metric in ("recall@10", "recall@50", "hit@10", "mrr", "ndcg@10")
        }

    return {
        "queries": queries,
        "per_query": per_query,
        "aggregate": aggregate,
        "corpus_size": len(retriever.records),
        "source_counts": Counter(r["source_id"] for r in retriever.records),
    }


def _run_mode(retriever, queries, mode, method, k=MAX_K):
    """Évalue un mode (raw/normalized/graph) pour une méthode de recherche."""
    per_query = {}
    analysis_per_query = {}

    for query in queries:
        started = time.perf_counter()
        ranked = _ranked_mode(retriever, query["question"], mode, method, k)
        latency_ms = (time.perf_counter() - started) * 1000
        per_query[query["id"]] = {
            "ranked": ranked,
            "recall@10": _recall_at(ranked, query["gold"], 10),
            "recall@50": _recall_at(ranked, query["gold"], 50),
            "hit@10": _hit_at(ranked, query["gold"], 10),
            "mrr": _mrr(ranked, query["gold"]),
            "ndcg@10": _ndcg_at(ranked, query["gold"], 10),
            "latency_ms": latency_ms,
            "sources@10": Counter(
                retriever.by_id[cid]["source_id"]
                for cid in ranked[:10]
                if cid in retriever.by_id
            ),
        }
        analysis_per_query[query["id"]] = analysis_metrics(
            analyze_query(query["question"]), query
        )

    latencies = sorted(row["latency_ms"] for row in per_query.values())
    count = len(latencies)
    return {
        "mode": mode,
        "method": method,
        "k": k,
        "per_query": per_query,
        "aggregate": _aggregate_retrieval(per_query, queries),
        "analysis": analysis_per_query,
        "analysis_aggregate": _aggregate_analysis(analysis_per_query),
        "latency": {
            "median_ms": statistics.median(latencies) if latencies else 0.0,
            "p95_ms": latencies[int(0.95 * (count - 1))] if latencies else 0.0,
        },
        "corpus_size": len(retriever.records),
        "source_counts": Counter(r["source_id"] for r in retriever.records),
    }


def run_evaluation(retriever=None, mode="raw", method=None, queries=None, k=MAX_K):
    """Évalue la recherche, en conservant l'API historique de la semaine 2.

    Sans argument (``run_evaluation()``), le comportement est inchangé : trois
    méthodes en mode brut. Pour la semaine 3, passer ``mode`` et ``method`` :

        run_evaluation(mode="normalized", method="hybrid")
        run_evaluation(mode="graph", method="bm25")
    """
    retriever = retriever or Retriever()
    queries = queries or QUERIES
    if method is None and mode == "raw":
        return _run_legacy(retriever, queries, k)
    return _run_mode(retriever, queries, mode, method or "hybrid", k)


def run_week3_evaluation(retriever=None, methods=METHODS, modes=MODES, queries=None,
                         k=MAX_K):
    """Balaye les modes et méthodes ; renvoie aussi les métriques d'analyse L5."""
    retriever = retriever or Retriever()
    queries = queries or QUERIES
    results = {
        (mode, method): _run_mode(retriever, queries, mode, method, k)
        for mode in modes
        for method in methods
    }
    first = next(iter(results.values()))
    return {
        "queries": queries,
        "modes": tuple(modes),
        "methods": tuple(methods),
        "k": k,
        "results": results,
        "analysis": first["analysis"],
        "analysis_aggregate": first["analysis_aggregate"],
        "corpus_size": first["corpus_size"],
        "source_counts": first["source_counts"],
    }


def render_markdown(results):
    lines = []
    lines.append("# Comparaison BM25 vs recherche sémantique — Semaine 2\n")
    total = f"{results['corpus_size']:,}".replace(",", " ")
    sources = ", ".join(
        f"{source_id} ({count:,})".replace(",", " ")
        for source_id, count in results["source_counts"].most_common()
    )
    positives = [
        q for q in results["queries"]
        if q["type"] == "positive" and not q.get("variant") and q.get("gold")
    ]
    lines.append(f"Corpus : {total} chunks — {sources}. Top-{MAX_K} évalué.\n")
    lines.append(
        f"## Résultats agrégés ({len(positives)} questions réelles avec passage gold)\n"
    )
    lines.append("| Méthode | Recall@10 | Recall@50 | Hit@10 | MRR@100 | nDCG@10 |")
    lines.append("|---|---|---|---|---|---|")
    for method in METHODS:
        agg = results["aggregate"][method]
        lines.append(
            f"| {method} | {agg['recall@10']:.3f} | {agg['recall@50']:.3f} | "
            f"{agg['hit@10']:.3f} | {agg['mrr']:.3f} | {agg['ndcg@10']:.3f} |"
        )

    lines.append("\n## Détail par question\n")
    lines.append("| Question | Méthode | Recall@10 | Recall@50 | MRR | nDCG@10 |")
    lines.append("|---|---|---|---|---|---|")
    for query in results["queries"]:
        if query["type"] != "positive":
            continue
        label = query["id"] + (" (variante)" if query.get("variant") else "")
        for method in METHODS:
            row = results["per_query"][query["id"]][method]
            lines.append(
                f"| {label} | {method} | {row['recall@10']:.3f} | "
                f"{row['recall@50']:.3f} | {row['mrr']:.3f} | {row['ndcg@10']:.3f} |"
            )

    lines.append(
        "\n*Q3f est une variante diagnostique de Q3 (requête courte et ciblée) : "
        "elle n'entre pas dans l'agrégat et sert à isoler l'effet de la formulation.*"
    )

    lines.append("\n## Composition des sources dans le top-10\n")
    for query in results["queries"]:
        if query["type"] != "positive":
            continue
        lines.append(f"### {query['id']}\n")
        for method in METHODS:
            sources = results["per_query"][query["id"]][method]["sources@10"]
            pretty = ", ".join(f"{sid} ({n})" for sid, n in sources.most_common())
            lines.append(f"- **{method}** : {pretty}")
        lines.append("")

    lines.append("## Requêtes méta / hors périmètre\n")
    for query in results["queries"]:
        if query["type"] == "positive":
            continue
        lines.append(f"### {query['id']} ({query['type']})\n")
        lines.append(f"> {query['question']}\n")
        for method in METHODS:
            ranked = results["per_query"][query["id"]][method]["ranked"]
            top = ranked[:3]
            lines.append(f"- **{method}** top-3 : {', '.join(top)}")
        lines.append("")

    return "\n".join(lines)
