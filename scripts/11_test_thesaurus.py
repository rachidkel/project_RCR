import json
import sys
sys.path.insert(0, "src")
from pharmeazor.config import INTERIM

def test_thesaurus():
    # 1. On ouvre ton fichier JSON
    json_path = INTERIM / "thesaurus" / "interactions_medicamenteuses.json"
    
    if not json_path.exists():
        print(f"Erreur : Le fichier {json_path} n'existe pas.")
        return

    print(f"Chargement du fichier : {json_path.name}...\n")
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 2. On cherche les interactions pour l'AMLODIPINE
    recherche = "AMLODIPINE"
    print(f"🔍 Recherche des interactions pour : {recherche}")
    
    trouve = False
    for bloc in data:
        if bloc["substance_principale"].upper() == recherche:
            trouve = True
            print(f"\n✅ Substance trouvée : {bloc['substance_principale']}")
            print(f"Il y a {len(bloc['interactions'])} interaction(s) documentée(s) :\n")
            
            for inter in bloc["interactions"]:
                print(f"  ➡️ Associé avec : {inter['substance_cible']}")
                print(f"     Niveau de risque : {inter['niveau']}")
                print(f"     Description : {inter['description'][:150]}...") # On coupe à 150 caractères
                print()
    
    if not trouve:
        print(f"\n❌ Aucune interaction trouvée pour {recherche}. Vérifie l'orthographe.")

if __name__ == "__main__":
    test_thesaurus()