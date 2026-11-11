import re
import pandas as pd
from rapidfuzz import fuzz
from .config import PROCESSED
from .textnorm import norm


def _load_nomenclature():
    path = PROCESSED / "nomenclature" / "nomenclature_active.csv"
    df = pd.read_csv(path)
    col_dci = "DENOMINATION COMMUNE INTERNATIONALE"
    col_brand = "NOM DE MARQUE"
    df = df[[col_dci, col_brand]].copy()
    df.columns = ["dci_officielle", "nom_marque"]
    df = df.dropna(subset=["dci_officielle"])
    df["dci_norm"] = df["dci_officielle"].apply(norm)
    df["nom_marque"] = df["nom_marque"].astype(str).str.strip()
    return df[df["nom_marque"].str.upper() != "NAN"]


def _chercher(dci_norm, df_nom, seuil=82):

    exact = df_nom[df_nom["dci_norm"] == dci_norm]
    if not exact.empty:
        return exact, "exact"

    
    contains = df_nom[df_nom["dci_norm"].str.contains(
        rf"(?:^|\s){re.escape(dci_norm)}(?:\s|$)", regex=True, na=False
    )]
    if not contains.empty:
        return contains, "contient"


    df = df_nom.copy()
    df["score"] = df["dci_norm"].apply(lambda x: fuzz.token_set_ratio(dci_norm, x))
    cand = df[df["score"] >= seuil].sort_values("score", ascending=False)
    return cand, ("fuzzy" if not cand.empty else "aucun")

def _traiter(dci, df_nom):

    if re.search(r"[+/]", dci):
        
        dci_composee_norm = norm(dci)
        cand_composee, methode_composee = _chercher(dci_composee_norm, df_nom)

        if not cand_composee.empty and methode_composee in ("exact", "contient"):
            marques = sorted(set(cand_composee["nom_marque"].tolist()))
            noms = sorted(set(cand_composee["dci_officielle"].tolist()))
            return "oui", marques, f"DCI composée : {noms[0]}"


        parties = [p.strip() for p in re.split(r"[+/]", dci) if p.strip()]
        statuts, marques_set, rems = [], set(), []
        for p in parties:
            s, m, r = _traiter(p, df_nom)
            statuts.append(s)
            marques_set.update(m)
            if r:
                rems.append(f"{p} : {r}")

        if all(s == "oui" for s in statuts):
            return "oui", sorted(marques_set), "Composants : " + " | ".join(rems)
        if any(s == "oui" for s in statuts):
            return "à vérifier", sorted(marques_set), "Composants partiels : " + " | ".join(rems)
        return "non", [], "Aucun composant trouvé"


    cand, methode = _chercher(norm(dci), df_nom)
    if cand.empty:
        return "non", [], ""

    marques = sorted(set(cand["nom_marque"].tolist()))
    noms = sorted(set(cand["dci_officielle"].tolist()))

    if methode == "exact":
        return "oui", marques, f"DCI : {noms[0]}"
    if methode == "contient":
        return "oui", marques, f"DCI : {', '.join(noms[:3])}"
    return "à vérifier", marques, f"Approx. : {', '.join(noms[:3])}"

def run_matching():
    drugs_path = PROCESSED / "drugs.csv"
    if not drugs_path.exists():
        raise FileNotFoundError(
            "Lancez d'abord : python scripts/00_prep_drugs_list.py"
        )

    df_drugs = pd.read_csv(drugs_path)
    df_nom = _load_nomenclature()
    print(f"Nomenclature : {len(df_nom)} lignes | Médicaments : {len(df_drugs)}\n")

    rows = []
    for _, r in df_drugs.iterrows():
        dci = str(r["DCI (nom de la substance)"]).strip()
        statut, marques, rem = _traiter(dci, df_nom)
        rows.append({
            "N°": r["N°"],
            "Classe": r["Classe"],
            "DCI": dci,
            "Code ATC": r["Code ATC (indicatif)"],
            "Présent ?": statut,
            "Noms commerciaux trouvés": " ; ".join(marques[:10]),
            "Nb marques": len(marques),
            "Remarques (auto)": rem,
        })

    out = PROCESSED / "drugs_verified.csv"
    pd.DataFrame(rows).to_csv(out, index=False, encoding="utf-8-sig")
    print(pd.DataFrame(rows)["Présent ?"].value_counts())
    print(f"\nFichier : {out}")


if __name__ == "__main__":
    run_matching()