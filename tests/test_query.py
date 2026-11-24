"""Tests unitaires et d'intégration pour l'analyse de requêtes (Livrable L2 - Mohamed Ali BAGHRICHE).

Couverture :
  - 4 critères d'acceptation stricts du plan de travail Week 3
  - Classification d'intention sur les 6 catégories (dosage, interaction, contraindication, price, out_of_scope, unknown)
  - Extraction d'entités (longest match, offsets, DCI, classes)
  - Repli flou (rapidfuzz) sur fautes de frappe réelles
  - Robustesse (chaînes vides, bruit pur, accents, ponctuation)
  - Benchmark de latence (< 5 ms par requête)
  - Évaluation sur les requêtes types du projet Q1–Q5
"""

import sys
import time

sys.path.insert(0, "src")

from pharmeazor.query import Entity, QueryAnalysis, analyze_query


# =====================================================================
# 1. CRITÈRES D'ACCEPTATION DU PLAN DE TRAVAIL WEEK 3
# =====================================================================

def test_acceptance_doliprane_resolves_to_paracetamol():
    """Critère 1 : Doliprane résout vers PARACETAMOL."""
    qa = analyze_query("Quel est le dosage de Doliprane ?")
    dcis = [e.dci for e in qa.entities if e.dci]
    assert "PARACETAMOL" in dcis
    assert qa.entities[0].dci == "PARACETAMOL"
    assert qa.out_of_scope is False


def test_acceptance_aspirine_resolves_to_acide_acetylsalicylique_and_ains():
    """Critère 2 : aspirine résout vers ACIDE ACETYLSALICYLIQUE + AINS."""
    qa = analyze_query("Est-ce que l'aspirine est efficace ?")
    assert len(qa.entities) >= 1
    asp = next(e for e in qa.entities if e.dci == "ACIDE ACETYLSALICYLIQUE")
    assert asp.dci == "ACIDE ACETYLSALICYLIQUE"
    # Vérifie la présence de la classe anti-inflammatoire dans classes ou expanded_terms
    has_ains_in_classes = any(
        "ANTI-INFLAMMATOIRES NON STEROIDIENS" in c or "AINS" in c for c in asp.classes
    )
    has_ains_in_expanded = any(
        "ANTI-INFLAMMATOIRES NON STEROIDIENS" in t or "AINS" in t for t in qa.expanded_terms
    )
    assert has_ains_in_classes or has_ains_in_expanded


def test_acceptance_douleurs_dentaires_is_out_of_scope():
    """Critère 3 : douleurs dentaires est marqué hors périmètre."""
    qa = analyze_query("Quel médicament prendre pour mes douleurs dentaires ?")
    assert qa.out_of_scope is True
    assert qa.intent == "out_of_scope"

    qa2 = analyze_query("douleurs dentaires")
    assert qa2.out_of_scope is True
    assert qa2.intent == "out_of_scope"


def test_acceptance_latency_under_5ms_and_no_crash():
    """Critère 4 : < 5 ms par requête ; les termes inconnus ne crashent jamais."""
    # Terme inconnu
    qa_unknown = analyze_query("xyzabc123456 azertyuiop foobar")
    assert qa_unknown.entities == []
    assert qa_unknown.intent in ("unknown", "out_of_scope")

    # Benchmark de latence sur 100 requêtes
    queries = [
        "Peut-on associer l'Amlodipine et l'Ibuprofène ?",
        "Quel est le dosage de Doliprane 1000 mg chez l'adulte ?",
        "Quelles sont les contre-indications du gel KOPROFEN ?",
        "Quel est le prix du sirop Doliprane ?",
        "Est-ce que l'aspirine est contre-indiquée avec le Triatec ?",
    ]
    # Préchauffage du cache
    for q in queries:
        analyze_query(q)

    t0 = time.perf_counter()
    iterations = 100
    for i in range(iterations):
        analyze_query(queries[i % len(queries)])
    elapsed_ms = ((time.perf_counter() - t0) * 1000.0) / iterations

    assert elapsed_ms < 5.0, f"Latence trop élevée : {elapsed_ms:.2f} ms (limite : 5 ms)"


# =====================================================================
# 2. CLASSIFICATION DES INTENTIONS CLINIQUES
# =====================================================================

def test_intent_dosage():
    """Vérifie la détection de l'intention dosage / posologie."""
    q1 = analyze_query("Quelle est la posologie habituelle du paracétamol ?")
    assert q1.intent == "dosage"
    assert "POSOLOGIE" in q1.expanded_terms

    q2 = analyze_query("Combien de comprimés de Triatec 5 mg par jour ?")
    assert q2.intent == "dosage"


def test_intent_interaction():
    """Vérifie la détection de l'intention interaction médicamenteuse."""
    q1 = analyze_query("Peut-on associer l'Amlodipine et l'Ibuprofène ?")
    assert q1.intent == "interaction"
    assert "INTERACTION MEDICAMENTEUSE" in q1.expanded_terms

    q2 = analyze_query("Y a-t-il une interaction entre ramipril et spironolactone ?")
    assert q2.intent == "interaction"

    # Multi-entités avec conjonction
    q3 = analyze_query("Amlodipine et Ibuprofène")
    assert q3.intent == "interaction"


def test_intent_contraindication():
    """Vérifie la détection de l'intention contre-indications et effets indésirables."""
    q1 = analyze_query("Quelles sont les contre-indications du Koprofen ?")
    assert q1.intent == "contraindication"
    assert "CONTRE-INDICATION" in q1.expanded_terms

    q2 = analyze_query("Quels sont les effets indésirables du Triatec en cas de grossesse ?")
    assert q2.intent == "contraindication"


def test_intent_price():
    """Vérifie la détection de l'intention prix / remboursement."""
    q1 = analyze_query("Quel est le prix du Doliprane 1000 mg en pharmacie ?")
    assert q1.intent == "price"

    q2 = analyze_query("Est-ce que l'Augmentin est remboursé par la Chifa ?")
    assert q2.intent == "price"


def test_intent_out_of_scope_medical_advice():
    """Vérifie le blocage des demandes d'ordonnances ou d'avis personnalisés."""
    cases = [
        "Quelle dose d'ibuprofène dois-je donner à mon fils de 3 ans ?",
        "Peux-tu me rédiger une ordonnance d'amoxicilline ?",
        "J'ai de la fièvre et mal à la gorge, est-ce une angine ?",
        "Mon père prend du ramipril et a des vertiges, que dois-je faire ?",
    ]
    for c in cases:
        qa = analyze_query(c)
        assert qa.out_of_scope is True
        assert qa.intent == "out_of_scope"


def test_intent_unknown():
    """Vérifie le comportement neutre sur simple mention de médicament sans mot-clé."""
    qa = analyze_query("Doliprane 1000")
    assert qa.intent == "unknown"
    assert qa.out_of_scope is False
    assert len(qa.entities) == 1


# =====================================================================
# 3. EXTRACTION D'ENTITÉS & OFFSETS
# =====================================================================

def test_entity_extraction_and_offsets():
    """Vérifie que les offsets de caractères correspondent exactement au texte brut."""
    raw = "Peut-on associer l'Amlodipine et l'Ibuprofène ?"
    qa = analyze_query(raw)
    assert len(qa.entities) == 2

    e1, e2 = qa.entities[0], qa.entities[1]
    assert e1.dci == "AMLODIPINE"
    assert raw[e1.start : e1.end] == e1.term

    assert e2.dci == "IBUPROFENE"
    assert raw[e2.start : e2.end] == e2.term


def test_multi_word_entity_extraction():
    """Vérifie l'extraction d'entités composées de plusieurs mots."""
    raw = "Quelle est l'indication de l'acide acétylsalicylique ?"
    qa = analyze_query(raw)
    assert len(qa.entities) >= 1
    asp = next(e for e in qa.entities if e.dci == "ACIDE ACETYLSALICYLIQUE")
    assert asp.dci == "ACIDE ACETYLSALICYLIQUE"


def test_combination_entity_extraction():
    """Vérifie l'extraction d'associations médicamenteuses comme Augmentin."""
    qa = analyze_query("Quel est le dosage d'Augmentin 1 g ?")
    assert len(qa.entities) == 1
    assert qa.entities[0].dci == "AMOXICILLINE + ACIDE CLAVULANIQUE"
    assert "AMOXICILLINE" in qa.expanded_terms
    assert "ACIDE CLAVULANIQUE" in qa.expanded_terms


# =====================================================================
# 4. REPLI FLOU (FUZZY FALLBACK SUR FAUTES DE FRAPPE)
# =====================================================================

def test_fuzzy_fallback_on_typos():
    """Vérifie la résilience face aux fautes de frappe courantes d'usagers."""
    typos = [
        ("dolipran 1000", "PARACETAMOL"),
        ("paracetamole", "PARACETAMOL"),
        ("augmantin", "AMOXICILLINE + ACIDE CLAVULANIQUE"),
        ("triateck 5", "RAMIPRIL"),
        ("voltaren 50", "DICLOFENAC"),
    ]
    for query, expected_dci in typos:
        qa = analyze_query(query)
        assert len(qa.entities) >= 1, f"Échec d'extraction pour {query}"
        assert qa.entities[0].dci == expected_dci, (
            f"Mauvaise DCI pour {query} : obtenu {qa.entities[0].dci}, attendu {expected_dci}"
        )


# =====================================================================
# 5. ROBUSTESSE ET CAS LIMITES
# =====================================================================

def test_empty_and_whitespace_query():
    """Vérifie qu'une requête vide ne lève jamais d'exception."""
    for empty in ("", "   ", "\n\t"):
        qa = analyze_query(empty)
        assert qa.raw == empty
        assert qa.entities == []
        assert qa.intent == "unknown"
        assert qa.out_of_scope is False


def test_special_characters_and_accents():
    """Vérifie la robustesse avec ponctuation et majuscules accentuées."""
    qa = analyze_query("ÉFFÉRALGAN 500mg, comprimé effervescent !!!")
    assert len(qa.entities) >= 1
    assert qa.entities[0].dci == "PARACETAMOL"


# =====================================================================
# 6. ÉVALUATION SUR LES REQUÊTES TYPES DU PROJET (Q1 à Q5)
# =====================================================================

def test_project_queries_q1_to_q5():
    """Vérifie l'analyse sur les 5 premières questions canoniques du projet."""
    # Q1
    q1 = analyze_query("Quel est le dosage disponible du paracétamol ?")
    assert q1.intent == "dosage"
    assert any(e.dci == "PARACETAMOL" for e in q1.entities)
    assert q1.out_of_scope is False

    # Q2
    q2 = analyze_query("Peut-on associer l'ibuprofène et l'aspirine ? Quel est le niveau d'interaction ?")
    assert q2.intent == "interaction"
    dcis_q2 = {e.dci for e in q2.entities}
    assert "IBUPROFENE" in dcis_q2
    assert "ACIDE ACETYLSALICYLIQUE" in dcis_q2
    assert q2.out_of_scope is False

    # Q3
    q3 = analyze_query(
        "Pour un patient hypertendu âgé qui prend déjà régulièrement de "
        "l'Amlodipine, est-il possible de lui associer de l'Ibuprofène ?"
    )
    assert q3.intent == "interaction"
    dcis_q3 = {e.dci for e in q3.entities}
    assert "AMLODIPINE" in dcis_q3
    assert "IBUPROFENE" in dcis_q3

    # Q4
    q4 = analyze_query("Quel est le prix du DOLIPRANE 1000 mg ?")
    assert q4.intent == "price"
    assert any(e.dci == "PARACETAMOL" for e in q4.entities)

    # Q5
    q5 = analyze_query("Quel médicament prendre pour mes douleurs dentaires ?")
    assert q5.intent == "out_of_scope"
    assert q5.out_of_scope is True
