import json
CORPUS = "data/processed/week_2/corpus.jsonl"
A_VERIFIER = [
    "pharmnet:amoxicilline",
    "nomenclature:amoxicilline acide clavulanique",
    "pharmnet:paracetamol",
    "thesaurus:inhibiteurs de l enzyme de conversion:305:0",
    "thesaurus:anticoagulants oraux:49:1",
    "thesaurus:acide acetylsalicylique:5:2",
    "thesaurus:clarithromycine:130:0",
    "thesaurus:clarithromycine:130:1",
    "nomenclature:amlodipine besilate amlodipine",
    "nomenclature:amlodipine besilate exprime en amlodipine",
    "nomenclature:clarithromycine",
    "pharmnet:clarithromycine",
]
all_ids = set()
with open(CORPUS, encoding="utf-8") as f:
    for line in f:
        all_ids.add(json.loads(line)["chunk_id"])
for c in A_VERIFIER:
    print(("✅" if c in all_ids else "❌"), c)