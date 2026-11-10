import os
import pypdf

# 1. Définir les chemins des fichiers PDF sources
thesaurus_files = {
    "interactions": "data/raw/thesaurus/20230915-thesaurus-interactions-medicamenteuses-septembre-2023.pdf",
    "substances": "data/raw/thesaurus/20230915-thesaurus-index-des-substances-septembre-2023.pdf",
    "classes": "data/raw/thesaurus/20230915-thesaurus-index-des-classes-septembre-2023.pdf"
}

# S'assurer que le dossier de sortie existe
os.makedirs('data/processed/thesaurus_txt', exist_ok=True)

def clean_pdf_text(pdf_path, output_txt_path):
    print(f"Traitement et nettoyage de : {pdf_path}...")
    reader = pypdf.PdfReader(pdf_path)
    cleaned_lines = []
    
    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        if not text:
            continue
            
        lines = text.split('\n')
        for line in lines:
            line_stripped = line.strip()
            
            # --- Filtrage du bruit (En-têtes, pieds de page, numéros de page) ---
            # Ignorer les lignes vides ou les pieds de page typiques de l'ANSM
            if not line_stripped:
                continue
            if "boulevard Anatole France" in line_stripped:
                continue
            if "www.ansm.sante.fr" in line_stripped:
                continue
            # Ignorer les numéros de page isolés ou en-têtes standards si détectés
            if line_stripped.isdigit() and len(line_stripped) <= 3:
                continue
                
            cleaned_lines.append(line_stripped)
            
    # Sauvegarde du texte nettoyé
    full_cleaned_text = "\n".join(cleaned_lines)
    with open(output_txt_path, 'w', encoding='utf-8') as f:
        f.write(full_cleaned_text)
        
    print(f"-> Sauvegardé avec succès : {output_txt_path} ({len(cleaned_lines)} lignes conservées)")

# 2. Exécuter le nettoyage pour chaque fichier du thésaurus
for key, filename in thesaurus_files.items():
    if os.path.exists(filename):
        output_path = f"data/processed/thesaurus_txt/{key}_clean.txt"
        clean_pdf_text(filename, output_path)
    else:
        print(f"Fichier introuvable : {filename}")

print("\nTous les fichiers du thésaurus ont été nettoyés et enregistrés dans data/processed/thesaurus_txt/ !")