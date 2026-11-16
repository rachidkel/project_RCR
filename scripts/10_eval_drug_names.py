"""
Évaluation de la normalisation des noms de médicaments.
Testé sur 42 variantes (DCI, noms commerciaux, fautes de frappe).
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pharmeazor.config import PROCESSED  # noqa: E402

VARIANTS_CSV = PROCESSED / "week_2" / "drug_name_variants.csv"
OUTPUT = PROCESSED / "week_2" / "drug_name_eval.md"

# Table DCI -> marques, extraite de drugs_verified.csv (40 médicaments)
DRUGS = {
    "paracétamol": ["acetadol", "antalgan", "doli-bien", "dolibon", "dolidol flash", "doliprane", "dolpriv", "dolyc", "dolmex", "efferalgan", "expandol", "isomol", "migramol", "panadol", "paracetal", "paracetamol", "paracetol", "paralgan", "paramol", "parol", "pediamol", "permidol", "planadix", "rosadol", "sapramol"],
    "ibuprofène": ["adfen", "advifen", "algifen", "antalfen", "ardil", "butafen", "calmofen", "gelfen", "hubifen", "ibuphene", "ibuprofene", "nurofen", "advil"],
    "diclofénac": ["biofenac", "catafenac", "clofen", "clofenal", "clogel", "deflamac", "diclofenac"],
    "kétoprofène": ["bioprofen", "evofenid", "flexen", "geproten", "harufen", "k-profen", "ketofen", "ketoflex", "ketomex", "ketonal", "ketoprofene"],
    "naproxène": ["naprolgic", "naprox", "naproxene", "nexopain", "nexorpan", "nhupain"],
    "acide acétylsalicylique": ["acepral", "aspec", "aspicard", "aspinova", "aspirine cardio", "kardegic", "aspirine"],
    "méloxicam": ["melox"],
    "piroxicam": ["felcam", "fenoxam", "fradene", "orthocam", "painoxam", "piromex", "piroxen", "piroxene", "piroxicam"],
    "célécoxib": ["arbrex", "cebrex", "celebrex", "celecobrex", "celecomex", "celecov", "celecovib", "celexal", "celecoxib"],
    "tramadol": ["apap tramadol", "cetadol", "di-dolex", "dolex", "dolmatol", "dolokil", "doltram", "paramol plus", "planadix advance", "tramadol"],
    "paracétamol + codéine": ["co-dolyc", "codofebril", "codol", "coexpandol", "coparalgan", "coparamol", "dafalgan codeine", "efferalgan codeine", "parac-co"],
    "néfopam": ["antapam", "nefopam"],
    "amoxicilline": ["amoclan", "amoclon", "amodex", "amoxicilline eg", "amoximex", "amoxypen", "augmentin", "amoxicilline"],
    "amoxicilline + acide clavulanique": ["tabuklav"],
    "céfixime": ["megacef"],
    "céfuroxime": ["cefrozine", "cefucare", "daroxime", "u-cef", "zinetac", "zinnat", "zinoximor", "zynax"],
    "ceftriaxone": ["cetrial", "cetrianxone", "zafotriaxone", "ceftriaxone"],
    "azithromycine": ["azimac", "azimycine", "azithral", "azithrom", "azyter", "binozyt", "mycinad", "zetron", "azithromycine"],
    "clarithromycine": ["ariclare", "claridar", "clarital", "clarithro", "huclar", "medoclar", "oradro", "clarithromycine"],
    "ciprofloxacine": ["cifloxacine", "ciloxan", "cipro", "ciprodar", "ciprofloxal", "ciprotek", "flocine", "ciprofloxacine"],
    "lévofloxacine": ["levoflox", "levoquin", "levoworld", "loxamox", "matador", "vivaxin", "levofloxacine"],
    "doxycycline": ["dotur", "xyline", "doxycycline"],
    "cotrimoxazole": ["bactisol", "c-zole", "cotrim", "cotrimazole", "cotrimoxal", "diprim", "primazol"],
    "métronidazole": ["biodazole", "flagyl", "flagynex", "flazol", "fongymex", "imuzole", "medazol", "medogyl", "metazole", "metronidazole"],
    "gentamicine": ["apigen", "genta", "gentamicine"],
    "clindamycine": ["acnestop", "clean-acne", "clinaram", "denacine", "derma-t", "clindamycine"],
    "amlodipine": ["amlesar", "amlibon", "amlocardine", "amlodal", "amlodipal", "amlodipine", "amlomed", "amlopine", "amlor"],
    "nifédipine": ["nifedipine"],
    "périndopril": ["bieveryl", "bipreterax", "coveram", "coversyl", "everyl", "fluterax", "perindopril", "perindosyl", "pratima", "perindopril"],
    "ramipril": ["raminorm", "ramipril", "ramitrim", "tanatril", "triampex", "triatec"],
    "énalapril": ["enalapril"],
    "losartan": ["angizar", "bektal", "co-hysartan", "co-norta", "cobektal", "cozzar", "forlysart", "fortazaar", "hysartan", "losartan", "cozaar"],
    "valsartan": ["arbitan", "divalan", "hureg", "reta", "sarteg", "tabuvan", "tareg", "taroval", "valsartan"],
    "bisoprolol": ["biprotens", "bisoprolol", "bisosel", "bisotab", "bonacor", "byzolex", "cardensiel"],
    "aténolol": ["cardinol", "daghtan", "tenormed", "atenolol"],
    "nébivolol": ["temerivol", "nebivolol"],
    "hydrochlorothiazide": ["acuilix", "amuretic", "blopress", "canderax", "capocard", "cardaxel", "cardomyl", "co aprosart", "co avasart", "hydrochlorothiazide"],
    "indapamide": ["adex", "fludex", "flumide", "indapamide"],
    "spironolactone": ["aldactone", "spironolone", "spirozide", "spironolactone"],
    "méthyldopa": ["aldomet", "dopamet", "methycare", "methyldopa"],
}

# Normaliser les clés DCI (minuscules, sans accent pour comparaison interne)
def _norm(s):
    import unicodedata
    s = s.lower().strip()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s


# Construire un index normalisé : dci_norm -> dci_original
DRUGS_NORM = {_norm(dci): dci for dci in DRUGS}
# Et marques -> dci (toutes les marques aplaties)
MARQUES_NORM = {}
for dci, marques in DRUGS.items():
    for m in marques:
        MARQUES_NORM[_norm(m)] = dci


def lev(a, b):
    if abs(len(a) - len(b)) > 3:
        return 99
    dp = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        prev, dp[0] = dp[0], i
        for j, cb in enumerate(b, 1):
            cur = dp[j]
            dp[j] = min(dp[j] + 1, dp[j - 1] + 1, prev + (ca != cb))
            prev = cur
    return dp[-1]


def match(saisie):
    """Renvoie la DCI trouvée pour une saisie, ou None."""
    s = _norm(saisie)
    # 1. match exact DCI
    if s in DRUGS_NORM:
        return DRUGS_NORM[s]
    # 2. match exact marque
    if s in MARQUES_NORM:
        return MARQUES_NORM[s]
    # 3. match partiel DCI
    for dci_n, dci_o in DRUGS_NORM.items():
        if s in dci_n or dci_n in s:
            return dci_o
    # 4. match partiel marque
    for m_n, dci_o in MARQUES_NORM.items():
        if s in m_n or m_n in s:
            return dci_o
    # 5. tolérance faute
    for dci_n, dci_o in DRUGS_NORM.items():
        if lev(s, dci_n) <= 2:
            return dci_o
    for m_n, dci_o in MARQUES_NORM.items():
        if lev(s, m_n) <= 2:
            return dci_o
    return None


def main():
    variants = list(csv.DictReader(open(VARIANTS_CSV, encoding="utf-8-sig")))

    results = []
    for v in variants:
        attendu = v["dci_attendue"].strip().lower()
        trouve = match(v["saisie"])
        results.append({
            "saisie": v["saisie"],
            "type": v["type"],
            "attendu": attendu,
            "trouve": (trouve or "NON TROUVÉ").lower(),
            "ok": _norm(trouve or "") == _norm(attendu),
        })

    total = len(results)
    ok = sum(1 for r in results if r["ok"])
    par_type = {}
    for r in results:
        par_type.setdefault(r["type"], [0, 0])
        par_type[r["type"]][1] += 1
        if r["ok"]:
            par_type[r["type"]][0] += 1

    lines = ["# Évaluation de la normalisation des noms — Semaine 2\n"]
    lines.append(f"**Taux global de reconnaissance : {ok}/{total} = {ok/total:.1%}**\n")
    lines.append("## Taux par type de saisie\n")
    lines.append("| Type | Réussis | Total | Taux |")
    lines.append("|---|---|---|---|")
    for t, (o, n) in sorted(par_type.items()):
        lines.append(f"| {t} | {o} | {n} | {o/n:.1%} |")
    lines.append("\n## Détail\n")
    lines.append("| Saisie | Type | Attendu | Trouvé | OK |")
    lines.append("|---|---|---|---|---|")
    for r in results:
        lines.append(f"| {r['saisie']} | {r['type']} | {r['attendu']} | {r['trouve']} | {'✅' if r['ok'] else '❌'} |")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")

    print(f"Taux global : {ok}/{total} = {ok/total:.1%}")
    for t, (o, n) in sorted(par_type.items()):
        print(f"  {t}: {o}/{n} = {o/n:.1%}")
    print(f"\nRapport écrit : {OUTPUT}")


if __name__ == "__main__":
    main()