import csv
import sys

sys.path.insert(0, "src")
import pytest

from pharmeazor.config import PROCESSED
from pharmeazor.lexicon import (
    aliases_for, build_lexicon, class_members, load_lexicon, resolve, stats,
)


@pytest.fixture(scope="module", autouse=True)
def _lexicon_built():
    from pharmeazor.lexicon import save_lexicon
    save_lexicon()


def test_doliprane_is_paracetamol():
    assert resolve("Doliprane").dci == "PARACETAMOL"


def test_aspirine_is_acide_acetylsalicylique():
    assert resolve("aspirine").dci == "ACIDE ACETYLSALICYLIQUE"


def test_ibuprofene_belongs_to_ains():
    r = resolve("ibuprofène")
    assert r.dci == "IBUPROFENE"
    assert "ANTI-INFLAMMATOIRES NON STEROIDIENS" in r.classes


def test_at_least_95_percent_of_the_40_drugs_resolved():
    with open(PROCESSED / "drugs_verified.csv", encoding="utf-8-sig", newline="") as f:
        names = [row["DCI"] for row in csv.DictReader(f)]
    ok = [n for n in names if (r := resolve(n)) and r.dci and not r.ambiguous]
    assert len(ok) / len(names) >= 0.95, [n for n in names if n not in ok]


def test_ambiguous_aliases_are_logged_not_overwritten():
    lex = load_lexicon()
    ambiguous = [(a, e) for a, e in lex["aliases"].items() if e.get("candidates")]
    assert ambiguous, "aucune marque ambiguë : suspect"
    for alias, e in ambiguous:
        assert e["dci"] is None and len(e["candidates"]) >= 2
        assert any(c["alias"] == alias for c in lex["conflicts"])
    r = resolve(ambiguous[0][0], fuzzy=False)
    assert r.ambiguous and r.dci is None



@pytest.mark.parametrize("term,dci", [
    ("Efferalgan", "PARACETAMOL"),
    ("Augmentin", "AMOXICILLINE + ACIDE CLAVULANIQUE"),
    ("Triatec", "RAMIPRIL"),
    ("CETIRIZINE DICHLORHYDRATE", "CETIRIZINE"),
    ("RIVASTIGMINE TARTRATE EXPRIME EN RIVASTIGMINE", "RIVASTIGMINE"),
])
def test_brands_and_salts(term, dci):
    r = resolve(term)
    assert r and r.dci == dci, (term, r)


@pytest.mark.parametrize("term,cls", [
    ("AINS", "ANTI-INFLAMMATOIRES NON STEROIDIENS"),
    ("inhibiteurs calciques", "ANTAGONISTES DES CANAUX CALCIQUES"),
    ("antihypertenseurs", "ANTIHYPERTENSEURS SAUF ALPHA-BLOQUANTS"),
    ("IEC", "INHIBITEURS DE L'ENZYME DE CONVERSION".replace("'", " ").replace("L ENZYME", "L'ENZYME")),
])
def test_classes_and_synonyms(term, cls):
    r = resolve(term)
    assert r and r.kind == "class" and r.dci is None
    assert norm_eq(r.classes[0], cls)


def norm_eq(a, b):
    from pharmeazor.textnorm import norm
    return norm(a) == norm(b)


def test_class_members_and_reverse_aliases():
    assert "IBUPROFENE" in class_members("AINS")
    assert "AMLODIPINE" in class_members("inhibiteurs calciques")
    assert "doliprane" in aliases_for("PARACETAMOL")


def test_unregistered_but_known_substance_is_flagged():
    r = resolve("nifédipine")
    assert r and r.dci == "NIFEDIPINE" and r.registered is False


def test_unknown_term_never_crashes():
    assert resolve("zzzzqqqq") is None
    assert resolve("") is None


def test_regression_week2_variants_unchanged():

    from pharmeazor.normalize import canonical_key
    path = PROCESSED / "week_2" / "drug_name_variants.csv"
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["attendu"] and r["verdict"] == "ok"]
    bad = []
    for r in rows:
        res, want = resolve(r["saisie"]), canonical_key(r["attendu"])
        ok = res and (
            (res.dci and canonical_key(res.dci) == want)
            or (res.ambiguous and want in {canonical_key(c) for c in res.candidates})
        )
        if not ok:
            bad.append((r["saisie"], r["attendu"], res.dci if res else None))
    assert not bad, bad


def test_typo_in_source_nomenclature_is_merged():
    assert resolve("aspegic 1000").dci == "ACIDE ACETYLSALICYLIQUE"
    assert "ACIDE ACETYLSALICYTIQUE" not in {e["dci"] for e in load_lexicon()["aliases"].values()}


def test_partial_brand_is_not_silently_turned_into_a_combination():
    """« Dafalgan » seul n'est pas « Dafalgan Codéine » (paracétamol + codéine)."""
    r = resolve("Dafalgan")
    assert r.dci is None and r.ambiguous
    assert "PARACETAMOL + CODEINE" in r.candidates

    assert "CODEINE" in resolve("Dafalgan codeine").dci


def test_aspirin_is_not_forced_into_ains():
   
    r = resolve("aspirine")
    assert r.dci == "ACIDE ACETYLSALICYLIQUE"
    assert "ANTI-INFLAMMATOIRES NON STEROIDIENS" not in r.classes