
from pharmeazor.graph import KnowledgeGraph


def create_graph():
    kg = KnowledgeGraph()

    kg.add_dci(
        "AMLODIPINE",
        classes=[
            "ANTIHYPERTENSEURS SAUF ALPHA-BLOQUANTS",
            "ANTAGONISTES DES CANAUX CALCIQUES",
        ],
    )

    kg.add_dci(
        "IBUPROFENE",
        classes=["ANTI-INFLAMMATOIRES NON STEROIDIENS"],
    )

    kg.add_interaction(
        "INTERACTION_1",
        "AINS avec diurétiques",
        classes=["DIURETIQUES"],
        source="ANSM Thesaurus",
    )

    return kg


def test_amlodipine_class():
    kg = create_graph()

    neighbors = kg.neighbors("AMLODIPINE")

    assert any(
        item["entity"] == "ANTIHYPERTENSEURS SAUF ALPHA-BLOQUANTS"
        and item["relation"] == "member_of"
        for item in neighbors
    )


def test_ibuprofen_class():
    kg = create_graph()

    neighbors = kg.neighbors("IBUPROFENE")

    assert any(
        item["entity"] == "ANTI-INFLAMMATOIRES NON STEROIDIENS"
        for item in neighbors
    )


def test_interaction_class():
    kg = create_graph()

    interactions = kg.interactions_for("IBUPROFENE")

    assert isinstance(interactions, list)


def test_absence_explanation():
    kg = create_graph()

    result = kg.explain_absence("AINS", "AMLODIPINE")

    assert result["direct_relation_found"] is False
    assert "medical risk" in result["message"]


def test_paths():
    kg = create_graph()

    result = kg.paths(
        "AMLODIPINE",
        "ANTIHYPERTENSEURS SAUF ALPHA-BLOQUANTS",
    )

    assert result


def test_statistics():
    kg = create_graph()

    stats = kg.stats()

    assert stats["nodes"] > 0
    assert stats["edges"] > 0
