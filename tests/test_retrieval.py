import sys
sys.path.insert(0, "src")

from pharmeazor.retrieval import Retriever


def test_out_of_scope_dental():
    r = Retriever(load_dense=False)
    is_oos, _ = r.is_out_of_scope("Quel médicament prendre pour mes douleurs dentaires ?")
    assert is_oos is True


def test_in_scope_paracetamol():
    r = Retriever(load_dense=False)
    is_oos, _ = r.is_out_of_scope("Quel est le dosage du paracétamol ?")
    assert is_oos is False


def test_in_scope_amlodipine_ibuprofen():
    r = Retriever(load_dense=False)
    is_oos, _ = r.is_out_of_scope(
        "Peut-on associer l'Amlodipine et l'Ibuprofène ?"
    )
    assert is_oos is False


def test_thesaurus_exact_lookup():
    from pharmeazor.thesaurus import load_lookup
    th = load_lookup()
    hits = th.lookup("aspirine + ibuprofene")
    assert len(hits) > 0
    # Vérifie que l'interaction AINS + aspirine est bien retrouvée
    assert any("anti inflammatoires non steroidiens" in h.substance.lower() or "acide acetylsalicylique" in h.target.lower() for h in hits)


def test_medical_advice_refusal():
    r = Retriever(load_dense=False)
    is_oos, reason = r.is_out_of_scope("Quelle dose d'ibuprofène dois-je donner à mon fils de 3 ans ?")
    assert is_oos is True
    assert "Demande de conseil médical" in reason


def test_unregistered_drug_detection():
    r = Retriever(load_dense=False)
    is_oos, reason = r.is_out_of_scope("Quelle est la capitale de l'Algérie ?")
    assert is_oos is True
