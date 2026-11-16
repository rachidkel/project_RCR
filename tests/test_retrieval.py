import sys
sys.path.insert(0, "src")

from pharmeazor.retrieval import Retriever


def test_out_of_scope_dental():
    r = Retriever()
    is_oos, _ = r.is_out_of_scope("Quel médicament prendre pour mes douleurs dentaires ?")
    assert is_oos is True


def test_in_scope_paracetamol():
    r = Retriever()
    is_oos, _ = r.is_out_of_scope("Quel est le dosage du paracétamol ?")
    assert is_oos is False


def test_in_scope_amlodipine_ibuprofen():
    r = Retriever()
    is_oos, _ = r.is_out_of_scope(
        "Peut-on associer l'Amlodipine et l'Ibuprofène ?"
    )
    assert is_oos is False