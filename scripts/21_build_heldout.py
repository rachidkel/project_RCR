import hashlib
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pharmeazor.config import CORPUS_PATH, PROCESSED  # noqa: E402
from pharmeazor.textnorm import norm  # noqa: E402

OUT = PROCESSED / "week_3" / "heldout_questions.json"
ENRICH = ROOT / "src" / "pharmeazor" / "enrich.py"
REGISTRIES = ("nomenclature", "nomenclature_dz", "pharmnet")
SALT = {"potassique", "sodique", "exprime", "en", "sous", "forme", "de", "d", "monohydrate",
        "monohydratee", "hyclate", "arginine", "erbumine", "ter", "butylamine", "fopme"}

RECORDS = [json.loads(line) for line in open(CORPUS_PATH, encoding="utf-8")]
BY_ID = {r["chunk_id"]: r for r in RECORDS}


def registry(dci):
    """Fiches registre de la DCI seule (sels et formes ignorés, associations exclues)."""
    want = set(norm(dci).split())
    out = []
    for r in RECORDS:
        if r["chunk_id"].split(":", 1)[0] not in REGISTRIES:
            continue
        tokens = set(norm(r["metadata"].get("dci") or r["metadata"].get("inn") or "").split())
        if want <= tokens and not (tokens - want - SALT):
            out.append(r["chunk_id"])
    return out


def pair(a, b):
    """Passages du Thésaurus « A + B » et « B + A »."""
    a, b = norm(a), norm(b)
    out = []
    for r in RECORDS:
        if r["source_id"] != "S_ANSM_THESAURUS":
            continue
        s, c = norm(r["metadata"]["substance"]), norm(r["metadata"]["cible"])
        if (s.startswith(a) and c.startswith(b)) or (s.startswith(b) and c.startswith(a)):
            out.append(r["chunk_id"])
    return out


def rcp(product, section):
    """Sections d'un RCP de l'ANPP (y compris ses sous-parties #subN)."""
    return [r["chunk_id"] for r in RECORDS if r["chunk_id"].startswith("anpp:")
            and product in r["metadata"]["product"] and r["metadata"]["section"] == section]


Q = []


def add(qid, qtype, question, expected, gold, keys=(), note=""):
    Q.append({"id": qid, "type": qtype, "split": "heldout", "question": question,
              "expected_answer": expected, "answer_keys": list(keys),
              "gold": sorted(set(gold)), "note": note})


add("H01", "direct", "Quelles marques de losartan sont enregistrées en Algérie ?",
    "Fiches registre du losartan potassique.", registry("losartan"), keys=["LOSARTAN"])
add("H02", "direct", "Quelle est la DCI du médicament COVERSYL ?",
    "Périndopril (arginine).", [c for c in registry("perindopril") if "COVERSYL" in BY_ID[c]["text"]],
    keys=["COVERSYL"], note="Marque -> DCI.")
add("H03", "direct", "Quelle est la posologie du BIODAZOLE selon son RCP ?",
    "Section 4.2 du RCP de BIODAZOLE (métronidazole).", rcp("BIODAZOLE", "4.2"))
add("H04", "direct", "Quelles sont les contre-indications du CEBREX selon son RCP ?",
    "Section 4.3 des RCP de CEBREX 100 et 200 mg (célécoxib).", rcp("CEBREX", "4.3"))
add("H05", "cross", "Peut-on associer la doxycycline et des sels de fer ?",
    "Cyclines + fer : précaution d'emploi, prendre le fer à distance.",
    pair("cyclines", "fer"), keys=["Précaution d'emploi"], note="Interaction de classe (cyclines).")
add("H06", "cross", "Peut-on associer le tramadol et la fluoxétine ?",
    "Deux entrées : fluoxétine + tramadol, association déconseillée (baisse d'efficacité du "
    "tramadol) ; ISRS + tramadol, à prendre en compte (syndrome sérotoninergique). "
    "Le niveau à retenir est le plus grave : association déconseillée.",
    pair("tramadol", "fluoxetine")
    + pair("tramadol", "inhibiteurs selectifs de la recapture de la serotonine"),
    keys=["Association déconseillée", "A prendre en compte"],
    note="Gold corrigé après la première exécution : la version initiale ne retenait que "
         "l'entrée de classe (à prendre en compte) et omettait l'entrée directe, plus grave "
         "(association déconseillée). Poids de L4 non modifiés.")
add("H07", "cross", "Peut-on associer le diclofénac et le losartan ?",
    "AINS + ARA II : précaution d'emploi.",
    pair("anti inflammatoires non steroidiens", "antagonistes des recepteurs de l angiotensine ii"),
    keys=["Précaution d'emploi"],
    note="Paire de médicaments nouvelle, mais le passage 56:2 (AINS + ARA II) est aussi "
         "un gold de Q3 : ce passage a servi au réglage.")
add("H08", "cross", "Le méthotrexate peut-il être pris avec du kétoprofène ?",
    "AINS + méthotrexate : association déconseillée (selon la dose de méthotrexate).",
    pair("anti inflammatoires non steroidiens", "methotrexate"), keys=["Association déconseillée"])
add("H09", "cross", "Peut-on donner des sels de potassium à un patient sous amiloride ?",
    "Diurétiques épargneurs de potassium + potassium : association déconseillée.",
    pair("diuretiques epargneurs de potassium", "potassium"), keys=["Association déconseillée"],
    note="Amiloride = diurétique épargneur de potassium.")
add("H10", "cross", "Quelle précaution pour l'association nébivolol et amiodarone ?",
    "Bêta-bloquants + amiodarone : précaution d'emploi (surveillance clinique et ECG).",
    pair("beta bloquants sauf esmolol et sotalol", "amiodarone"), keys=["Précaution d'emploi"])

errors = []
for q in Q:
    if not q["gold"]:
        errors.append(f"{q['id']}: aucun passage gold")
    blob = " ".join(BY_ID[c]["text"] for c in q["gold"])
    errors += [f"{q['id']}: '{k}' absent du gold" for k in q["answer_keys"] if k.lower() not in blob.lower()]

for q in Q:
    print(f"{q['id']} [{q['type']:<6}] gold={len(q['gold'])}  {q['question']}")
if errors:
    print("\nERREURS :\n  - " + "\n  - ".join(errors))
    sys.exit(1)

frozen = hashlib.sha256(ENRICH.read_bytes()).hexdigest()[:12]
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"frozen_enrich_sha256": frozen, "questions": Q},
                          ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n{len(Q)} questions écrites : {OUT}\nempreinte de enrich.py figée : {frozen}")
