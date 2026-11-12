import sys
import json
import re
from pathlib import Path

sys.path.insert(0, "src")
from pharmeazor.config import RAW, INTERIM


import pymupdf 



PDFS = {
    "interactions_medicamenteuses": RAW / "ansm_thesaurus" / "20230915-thesaurus-interactions-medicamenteuses-septembre-2023.pdf",
    "index_substances":           RAW / "ansm_thesaurus" / "20230915-thesaurus-index-des-substances-septembre-2023.pdf",
    "index_classes":              RAW / "ansm_thesaurus" / "20230915-thesaurus-index-des-classes-septembre-2023.pdf",
}


REGEX_NIVEAUX = re.compile(
    r"(CONTRE[- ]?INDICATION|Association DECONSEILLEE|Précaution d'emploi|A prendre en compte|CI - ASDEC - APEC|CI - PE|ASDEC - PE|ASDEC - APEC)", 
    re.IGNORECASE
)


NOISE_LINES = re.compile(
    r"^(THESAURUS|DES INTERACTIONS|SEPTEMBRE 2023|INDEX DES|PHARMACO-THERAPEUTIQUES|\d+$)",
    re.IGNORECASE,
)


def parser_interactions(pdf_path):
    
    doc = pymupdf.open(pdf_path)
    
    
    texte_complet = ""
    for page in doc:
        texte_complet += page.get_text("text") + "\n"

    
    texte_complet = re.sub(r"THESAURUS DES INTERACTIONS MÉDICAMENTEUSES\s*\nSEPTEMBRE 2023", "", texte_complet)
    texte_complet = re.sub(r"\n\d+\n", "\n", texte_complet)  

    
    blocs_bruts = re.split(r"\n(?=[A-ZÀ-Ÿ][A-ZÀ-Ÿ\s\-']{2,}\n)", texte_complet)

    resultats = []
    
    for bloc in blocs_bruts:
        bloc = bloc.strip()
        if not bloc: 
            continue
        
        lignes = bloc.split("\n")
        nom_substance = lignes[0].strip()
        
        faux_positifs = ["CONTRE-INDICATION", "ASDEC - PE", "ASDEC - APEC", "CI - PE", "CI - ASDEC", "CI - ASDEC - APEC"]
        if len(nom_substance) < 3 or NOISE_LINES.match(nom_substance) or "INTERACTIONS" in nom_substance or nom_substance.upper() in faux_positifs:
            continue

        interactions = []
        
        
        interactions_brutes = re.findall(
            r"\+\s*([^\n]+)(.*?)(?=\n\+|\Z)", 
            bloc, 
            re.DOTALL
        )
        
        for cible_brute, contenu_brut in interactions_brutes:
            cible = cible_brute.strip()
            
            
            contenu = re.sub(r"\s+", " ", contenu_brut).strip()
            
        
            niveau = "Non précisé"
            match_niveau = REGEX_NIVEAUX.search(contenu)
            
            if match_niveau:
                niveau = match_niveau.group(1).strip().capitalize()
                
                description = contenu[:match_niveau.start()].strip()
    
                details_apres = contenu[match_niveau.end():].strip()
                if details_apres:
                    description += " " + details_apres
            else:
                description = contenu
            
            
            if len(description) > 5:
                interactions.append({
                    "substance_cible": cible,
                    "niveau": niveau,
                    "description": description
                })
                
        if interactions:
            resultats.append({
                "substance_principale": nom_substance,
                "interactions": interactions
            })

    return resultats


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