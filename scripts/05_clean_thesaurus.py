import sys
import json
import re
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, "src")
from pharmeazor.config import RAW, INTERIM


import pymupdf



PDFS = {
    "interactions_medicamenteuses": RAW / "ansm_thesaurus" / "20230915-thesaurus-interactions-medicamenteuses-septembre-2023.pdf",
    "index_substances":           RAW / "ansm_thesaurus" / "20230915-thesaurus-index-des-substances-septembre-2023.pdf",
    "index_classes":              RAW / "ansm_thesaurus" / "20230915-thesaurus-index-des-classes-septembre-2023.pdf",
}


REGEX_NIVEAUX = re.compile(
    r"(CONTRE[- ]?INDICATION"
    r"|Association\s+(?:déconseillée|deconseillee|DECONSEILLEE)"
    r"|Précaution\s+d'emploi"
    r"|A\s+prendre\s+en\s+compte"
    r"|CI\s*-\s*ASDEC\s*-\s*APEC"
    r"|CI\s*-\s*ASDEC"
    r"|CI\s*-\s*PE"
    r"|ASDEC\s*-\s*APEC"
    r"|ASDEC\s*-\s*PE"
    r"|ASDEC|APEC|PE|CI)",
    re.IGNORECASE,
)


NOISE_LINES = re.compile(
    r"^(THESAURUS|DES INTERACTIONS|SEPTEMBRE 2023|INDEX DES|PHARMACO-THERAPEUTIQUES|\d+$)",
    re.IGNORECASE,
)

PAGE_RE = re.compile(r"^===\s*PAGE\s+\d+\s*===$", re.IGNORECASE)
NOISE_SUBSTR = ("boulevard anatole france", "www.ansm.sante.fr")

HEADING_RE = re.compile(r"^[A-ZÀ-Ÿ0-9 ’'\-/().,]+$")

LEVEL_LABELS = re.compile(
    r"^(?:CONTRE[- ]?INDICATION|CI|PE|APEC|ASDEC"
    r"|CI\s*-\s*ASDEC\s*-\s*APEC|CI\s*-\s*ASDEC|CI\s*-\s*PE"
    r"|ASDEC\s*-\s*APEC|ASDEC\s*-\s*PE"
    r"|Association\s+(?:déconseillée|deconseillee|DECONSEILLEE)"
    r"|Précaution\s+d'emploi"
    r"|A\s+prendre\s+en\s+compte)$",
    re.IGNORECASE,
)


def _normaliser_niveau(brut):
    n = brut.upper()
    tokens = set(re.split(r"[\s\-]+", n))
    if "CONTRE" in n or "CI" in tokens:
        return "Contre-indication"
    if "CONSEILL" in n or "ASDEC" in n:
        if "APEC" in n or "PRENDRE EN COMPTE" in n:
            return "Association déconseillée + A prendre en compte"
        return "Association déconseillée"
    if "APEC" in n or "PRENDRE EN COMPTE" in n:
        return "A prendre en compte"
    if "PRÉCAUTION" in n or "PRECAUTION" in n or "PE" in tokens:
        return "Précaution d'emploi"
    return brut.strip().capitalize()


HEADING_MIN_SIZE = 9.5
HEADING_MAX_LEN = 120
HEADING_BAD_CHARS = ".:;!?■"


def _titre_valide(texte):
    if not texte or texte.startswith("+"):
        return False
    if len(texte) > HEADING_MAX_LEN:
        return False
    if any(c in texte for c in HEADING_BAD_CHARS):
        return False
    if sum(c.isalpha() for c in texte) < 3:
        return False
    return True


def _premier_bloc(lignes):
    for i, (texte, _) in enumerate(lignes):
        if texte.startswith("+"):
            for j in range(i - 1, -1, -1):
                if lignes[j][1] >= HEADING_MIN_SIZE and _titre_valide(lignes[j][0]):
                    return j
            return i
    return 0


def _page_lines(page):
    lignes = []
    for bloc in page.get_text("dict").get("blocks", []):
        for ligne in bloc.get("lines", []):
            spans = ligne.get("spans", [])
            if not spans:
                continue
            texte = "".join(s.get("text", "") for s in spans).strip()
            if not texte:
                continue
            taille = max((s.get("size", 0) for s in spans), default=0)
            lignes.append((texte, taille))
    return lignes


def parser_interactions(pdf_path):
    doc = pymupdf.open(pdf_path)

    lignes = []
    for page in doc:
        for texte, taille in _page_lines(page):
            if PAGE_RE.match(texte):
                continue
            if NOISE_LINES.match(texte):
                continue
            if any(n in texte.lower() for n in NOISE_SUBSTR):
                continue
            lignes.append((texte, taille))

    resultats = []
    courant = None
    interaction = None
    precedent_titre = False
    capture_membres = False

    for texte, taille in lignes[_premier_bloc(lignes):]:
        if taille >= HEADING_MIN_SIZE and _titre_valide(texte):
            if precedent_titre and courant is not None:
                courant["substance_principale"] = (
                    courant["substance_principale"] + " " + texte
                ).strip()
            else:
                courant = {
                    "substance_principale": texte,
                    "voir_aussi": "",
                    "membres": "",
                    "interactions": [],
                }
                resultats.append(courant)
                interaction = None
            precedent_titre = True
            capture_membres = False
            continue
        precedent_titre = False

        if texte.startswith("+"):
            if courant is None:
                continue
            interaction = {
                "substance_cible": texte.lstrip("+").strip(),
                "niveau": "Non précisé",
                "description": "",
            }
            courant["interactions"].append(interaction)
            capture_membres = False
            continue

        if texte.upper().startswith("VOIR"):
            if courant is not None:
                courant["voir_aussi"] = (courant["voir_aussi"] + " " + texte).strip()
            continue

        if interaction is None:
            if courant is not None and (capture_membres or texte.startswith("(")):
                courant["membres"] = (courant["membres"] + " " + texte).strip()
                capture_membres = not texte.rstrip().endswith(")")
            continue

        if LEVEL_LABELS.match(texte):
            if interaction["niveau"] == "Non précisé":
                interaction["niveau"] = _normaliser_niveau(texte)
            continue

        interaction["description"] += " " + texte
        if interaction["niveau"] == "Non précisé":
            match_niveau = REGEX_NIVEAUX.search(texte)
            if match_niveau:
                interaction["niveau"] = _normaliser_niveau(match_niveau.group(1))

    propre = []
    for bloc in resultats:
        interactions = []
        for it in bloc["interactions"]:
            description = re.sub(r"\s+", " ", it["description"]).strip()
            if len(description) > 5:
                interactions.append({
                    "substance_cible": it["substance_cible"],
                    "niveau": it["niveau"],
                    "description": description,
                })
        if interactions:
            membres = bloc["membres"].strip()
            if membres.startswith("("):
                membres = membres[1:]
            if membres.endswith(")"):
                membres = membres[:-1]
            propre.append({
                "substance_principale": bloc["substance_principale"],
                "voir_aussi": bloc["voir_aussi"],
                "membres": membres.strip(),
                "interactions": interactions,
            })

    return propre


def sauvegarder_json(resultats, out_path):
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(resultats, f, ensure_ascii=False, indent=2)


def sauvegarder_txt_brut(pdf_path, out_path, entete):
    """Génère un fichier texte brut avec en-tête de provenance (pour le rapport)."""
    doc = pymupdf.open(pdf_path)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(entete)
        for num_page, page in enumerate(doc, start=1):
            f.write(f"\n\n=== PAGE {num_page} ===\n\n")
            for ligne in page.get_text("text").splitlines():
                if not NOISE_LINES.match(ligne.strip()):
                    f.write(ligne + "\n")


def main():
    out_dir = INTERIM / "thesaurus"
    out_dir.mkdir(parents=True, exist_ok=True)

    for nom, pdf_path in PDFS.items():
        if not pdf_path.exists():
            print(f"[skip] {nom} : fichier introuvable")
            continue

        print(f"\n=== Traitement de {nom} ===")

        
        if nom == "interactions_medicamenteuses":
            print("  Parsing structuré en cours...")
            try:
                resultats = parser_interactions(pdf_path)
                json_path = out_dir / f"{nom}.json"
                sauvegarder_json(resultats, json_path)

                n_substances = len(resultats)
                n_interactions = sum(len(b["interactions"]) for b in resultats)
                n_avec_niveau = sum(
                    1 for b in resultats for i in b["interactions"] if i["niveau"] != "Non précisé"
                )
                print(f"  [ok] {n_substances} substances trouvées.")
                print(f"       {n_interactions} interactions extraites.")
                print(f"       {n_avec_niveau} avec niveau de risque identifié.")
                print(f"       → {json_path}")
            except Exception as e:
                print(f"  [erreur] {e}")

        
        entete = (
            "---\n"
            f"source: ANSM Thésaurus ({nom})\n"
            "url: https://ansm.sante.fr/\n"
            "collected: 2026-11-11\n"
            "authority_rank: 3\n"
            "lang: fr\n"
            "---\n"
        )
        txt_path = out_dir / f"{nom}.txt"
        sauvegarder_txt_brut(pdf_path, txt_path, entete)
        print(f"  [ok] TXT brut généré → {txt_path}")

    print("\n=== Terminé ===")
    print(f"Fichiers générés dans : {out_dir}")


if __name__ == "__main__":
    main()
