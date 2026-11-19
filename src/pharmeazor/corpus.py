import csv
import json
from collections import Counter

from .config import INTERIM, PROCESSED, RAW, CORPUS_PATH
from .textnorm import norm


THESAURUS_JSON = INTERIM / "thesaurus" / "interactions_medicamenteuses.json"
NOMENCLATURE_CSV = PROCESSED / "nomenclature" / "nomenclature_active.csv"
EMA_CSV = RAW / "ema" / "ema_medicines_clean.csv"
DWA_CSV = RAW / "dwa" / "nomenclature_dz_clean.csv"
PHARMNET_CSV = PROCESSED / "pharmnet" / "produits_enregistres.csv"
NOMENCLATURE_DZ_CSV = RAW / "nomenclature" / "algerian_drug_nomenclature.csv"


SOURCES = {
    "thesaurus": {
        "source_id": "S_ANSM_THESAURUS",
        "source_name": "ANSM Thésaurus des interactions médicamenteuses (sept. 2023)",
        "authority_rank": 3,
        "lang": "fr",
    },
    "nomenclature": {
        "source_id": "S_MIPH_NOMENCLATURE",
        "source_name": "Nomenclature nationale MIPH (août 2026)",
        "authority_rank": 2,
        "lang": "fr",
    },
    "ema": {
        "source_id": "S_EMA",
        "source_name": "EMA - European Medicines Agency",
        "authority_rank": 3,
        "lang": "en",
    },
    "dwa": {
        "source_id": "S_DWA",
        "source_name": "DWA Algérie - nomenclature enregistrée",
        "authority_rank": 4,
        "lang": "fr",
    },
    "pharmnet": {
        "source_id": "S_PHARMNET",
        "source_name": "Pharm'Net Algérie - répertoire des médicaments enregistrés",
        "authority_rank": 4,
        "lang": "fr",
    },
    "nomenclature_dz": {
        "source_id": "S_DZ_NOMENCLATURE",
        "source_name": "Nomenclature algérienne des médicaments ",
        "authority_rank": 2,
        "lang": "fr",
    },
}


def _clean(value):
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() in ("nan", "none") else text


def _record(source, chunk_id, doc_id, text, metadata):
    meta = SOURCES[source]
    return {
        "chunk_id": chunk_id,
        "doc_id": doc_id,
        "source_id": meta["source_id"],
        "source_name": meta["source_name"],
        "authority_rank": meta["authority_rank"],
        "lang": meta["lang"],
        "text": text.strip(),
        "metadata": metadata,
    }


def thesaurus_chunks():
    if not THESAURUS_JSON.exists():
        return
    with open(THESAURUS_JSON, encoding="utf-8") as f:
        blocs = json.load(f)

    for bloc_idx, bloc in enumerate(blocs):
        substance = _clean(bloc.get("substance_principale"))
        membres = _clean(bloc.get("membres"))[:1000]
        voir = _clean(bloc.get("voir_aussi"))
        doc_id = f"thesaurus:{norm(substance)}"
        for idx, interaction in enumerate(bloc.get("interactions", [])):
            cible = _clean(interaction.get("substance_cible"))
            niveau = _clean(interaction.get("niveau"))
            description = _clean(interaction.get("description"))
            text = f"{substance} + {cible} — {niveau} — {description}"
            if membres:
                text += f" | Classe {substance} : {membres}"
            yield _record(
                "thesaurus",
                f"{doc_id}:{bloc_idx}:{idx}",
                doc_id,
                text,
                {
                    "substance": substance,
                    "cible": cible,
                    "niveau": niveau,
                    "voir_aussi": voir,
                    "membres": membres,
                },
            )


def nomenclature_chunks():
    if not NOMENCLATURE_CSV.exists():
        return

    groupes = {}
    with open(NOMENCLATURE_CSV, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            dci = _clean(row.get("DENOMINATION COMMUNE INTERNATIONALE"))
            if not dci:
                continue
            key = norm(dci)
            groupe = groupes.setdefault(
                key,
                {
                    "dci": dci,
                    "marques": set(),
                    "formes": set(),
                    "dosages": set(),
                    "laboratoires": set(),
                    "statuts": set(),
                },
            )
            groupe["marques"].add(_clean(row.get("NOM DE MARQUE")))
            groupe["formes"].add(_clean(row.get("FORME")))
            groupe["dosages"].add(_clean(row.get("DOSAGE")))
            groupe["laboratoires"].add(
                _clean(row.get("LABORATOIRES DETENTEUR DE LA DECISION D'ENREGISTREMENT"))
            )
            groupe["statuts"].add(_clean(row.get("status")))

    for key, groupe in groupes.items():
        marques = sorted(b for b in groupe["marques"] if b)
        formes = sorted(v for v in groupe["formes"] if v)
        dosages = sorted(v for v in groupe["dosages"] if v)
        laboratoires = sorted(v for v in groupe["laboratoires"] if v)
        statuts = sorted(v for v in groupe["statuts"] if v)
        text = (
            f"{groupe['dci']} — marques : {', '.join(marques[:20])} — "
            f"formes : {', '.join(formes[:10])} — dosages : {', '.join(dosages[:20])} — "
            f"laboratoires : {', '.join(laboratoires[:10])} — statut {', '.join(statuts)}"
        )
        doc_id = f"nomenclature:{key}"
        yield _record(
            "nomenclature",
            doc_id,
            doc_id,
            text,
            {
                "dci": groupe["dci"],
                "marques": marques,
                "formes": formes,
                "dosages": dosages,
                "laboratoires": laboratoires,
                "statuts": statuts,
            },
        )


def ema_chunks():
    if not EMA_CSV.exists():
        return
    with open(EMA_CSV, encoding="utf-8-sig", newline="") as f:
        for idx, row in enumerate(csv.DictReader(f)):
            nom = _clean(row.get("medicine_name"))
            if not nom:
                continue
            substance = _clean(row.get("active_substance"))
            atc = _clean(row.get("atc_code"))
            aire = _clean(row.get("therapeutic_area_mesh"))
            indication = _clean(row.get("therapeutic_indication"))[:400]
            statut = _clean(row.get("medicine_status"))
            text = (
                f"{nom} — substance {substance} — ATC {atc} — "
                f"{aire} — {indication} — statut {statut}"
            )
            doc_id = f"ema:{_clean(row.get('ema_product_number')) or idx}"
            yield _record(
                "ema",
                f"{doc_id}#{idx}",
                doc_id,
                text,
                {
                    "medicine": nom,
                    "substance": substance,
                    "atc_code": atc,
                    "therapeutic_area": aire,
                    "status": statut,
                },
            )


def dwa_chunks():
    if not DWA_CSV.exists():
        return
    with open(DWA_CSV, encoding="utf-8-sig", newline="") as f:
        for idx, row in enumerate(csv.DictReader(f)):
            dci = _clean(row.get("dci_clean"))
            if not dci:
                continue
            marque = _clean(row.get("brand_clean"))
            forme = _clean(row.get("forme_clean"))
            dosage = _clean(row.get("dosage_clean"))
            labo = _clean(row.get("labo_clean"))
            text = f"{marque} — {dci} — {forme} {dosage} — laboratoire {labo}"
            doc_id = f"dwa:{idx}"
            yield _record(
                "dwa",
                f"{doc_id}#{idx}",
                doc_id,
                text,
                {
                    "dci": dci,
                    "marque": marque,
                    "forme": forme,
                    "dosage": dosage,
                    "laboratoire": labo,
                },
            )


def _prix(value):
    text = _clean(value).replace(",", ".")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def pharmnet_chunks():
    if not PHARMNET_CSV.exists():
        return

    groupes = {}
    with open(PHARMNET_CSV, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            dci = _clean(row.get("dci"))
            if not dci:
                continue
            key = _clean(row.get("dci_norm")) or norm(dci)
            groupe = groupes.setdefault(
                key,
                {
                    "dci": dci,
                    "dci_code": _clean(row.get("dci_code")),
                    "classe": _clean(row.get("classe_libelle")),
                    "marques": set(),
                    "formes": set(),
                    "dosages": set(),
                    "conditionnements": set(),
                    "laboratoires": set(),
                    "listes": set(),
                    "prix": [],
                },
            )
            groupe["marques"].add(_clean(row.get("nom_commercial")))
            groupe["formes"].add(_clean(row.get("forme")))
            groupe["dosages"].add(_clean(row.get("dosage")))
            groupe["conditionnements"].add(_clean(row.get("conditionnement")))
            groupe["laboratoires"].add(_clean(row.get("laboratoire")))
            groupe["listes"].add(_clean(row.get("liste")))
            prix = _prix(row.get("prix_ppa"))
            if prix is not None:
                groupe["prix"].append(prix)

    for key, groupe in groupes.items():
        marques = sorted(v for v in groupe["marques"] if v)
        formes = sorted(v for v in groupe["formes"] if v)
        dosages = sorted(v for v in groupe["dosages"] if v)
        conditionnements = sorted(v for v in groupe["conditionnements"] if v)
        laboratoires = sorted(v for v in groupe["laboratoires"] if v)
        listes = sorted(v for v in groupe["listes"] if v)
        prix = groupe["prix"]
        text = (
            f"PHARM'NET — {groupe['dci']} — classe {groupe['classe']} — "
            f"marques : {', '.join(marques[:20])} — "
            f"formes : {', '.join(formes[:10])} — dosages : {', '.join(dosages[:20])} — "
            f"laboratoires : {', '.join(laboratoires[:10])}"
        )
        if listes:
            text += f" — liste {', '.join(listes)}"
        if prix:
            text += f" — prix {min(prix):.2f} à {max(prix):.2f} DZD"
        doc_id = f"pharmnet:{key}"
        yield _record(
            "pharmnet",
            doc_id,
            doc_id,
            text,
            {
                "dci": groupe["dci"],
                "dci_code": groupe["dci_code"],
                "classe": groupe["classe"],
                "marques": marques,
                "formes": formes,
                "dosages": dosages,
                "conditionnements": conditionnements,
                "laboratoires": laboratoires,
                "listes": listes,
                "prix_ppa_min": min(prix) if prix else None,
                "prix_ppa_max": max(prix) if prix else None,
            },
        )


def _liste_norm(value):
    tokens = norm(value).split()
    if "stup" in " ".join(tokens):
        return "Stupéfiants"
    if "ii" in tokens:
        return "Liste II"
    if "i" in tokens:
        return "Liste I"
    return ""


def nomenclature_dz_chunks():
    if not NOMENCLATURE_DZ_CSV.exists():
        return

    groupes = {}
    with open(NOMENCLATURE_DZ_CSV, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            inn = _clean(row.get("inn"))
            if not inn:
                continue
            key = norm(inn)
            groupe = groupes.setdefault(
                key,
                {
                    "inn": inn,
                    "codes": set(),
                    "marques": set(),
                    "formes": set(),
                    "dosages": set(),
                    "conditionnements": set(),
                    "laboratoires": set(),
                    "pays": set(),
                    "listes": set(),
                    "statuts": set(),
                    "types": set(),
                    "remboursables": set(),
                    "prix": set(),
                },
            )
            groupe["codes"].add(_clean(row.get("code")))
            groupe["marques"].add(_clean(row.get("brand_name")))
            groupe["formes"].add(_clean(row.get("form")))
            groupe["dosages"].add(_clean(row.get("dosage")))
            groupe["conditionnements"].add(_clean(row.get("packaging")))
            groupe["laboratoires"].add(_clean(row.get("laboratory")))
            groupe["pays"].add(_clean(row.get("laboratory_country")))
            groupe["listes"].add(_liste_norm(row.get("list")))
            groupe["statuts"].add(_clean(row.get("status")).upper())
            groupe["types"].add(_clean(row.get("type")).upper())
            groupe["remboursables"].add(_clean(row.get("reimbursable")).upper())
            groupe["prix"].add(_clean(row.get("price_decision")))

    for key, groupe in groupes.items():
        codes = sorted(v for v in groupe["codes"] if v)
        marques = sorted(v for v in groupe["marques"] if v)
        formes = sorted(v for v in groupe["formes"] if v)
        dosages = sorted(v for v in groupe["dosages"] if v)
        conditionnements = sorted(v for v in groupe["conditionnements"] if v)
        laboratoires = sorted(v for v in groupe["laboratoires"] if v)
        pays = sorted(v for v in groupe["pays"] if v)
        listes = sorted(v for v in groupe["listes"] if v)
        statuts = sorted(v for v in groupe["statuts"] if v)
        types = sorted(v for v in groupe["types"] if v)
        remboursables = sorted(v for v in groupe["remboursables"] if v)
        prix = sorted(v for v in groupe["prix"] if v)
        text = (
            f"NOMENCLATURE DZ — {groupe['inn']} — code {', '.join(codes[:3])} — "
            f"marques : {', '.join(marques[:20])} — "
            f"formes : {', '.join(formes[:10])} — dosages : {', '.join(dosages[:20])} — "
            f"laboratoires : {', '.join(laboratoires[:10])}"
        )
        if listes:
            text += f" — liste {', '.join(listes)}"
        if statuts:
            text += f" — statut {', '.join(statuts)}"
        if remboursables:
            text += f" — remboursable {', '.join(remboursables)}"
        if prix:
            text += f" — prix {', '.join(prix[:5])}"
        doc_id = f"nomenclature_dz:{key}"
        yield _record(
            "nomenclature_dz",
            doc_id,
            doc_id,
            text,
            {
                "inn": groupe["inn"],
                "codes": codes,
                "marques": marques,
                "formes": formes,
                "dosages": dosages,
                "conditionnements": conditionnements,
                "laboratoires": laboratoires,
                "pays": pays,
                "listes": listes,
                "statuts": statuts,
                "types": types,
                "remboursables": remboursables,
                "prix": prix,
            },
        )


BUILDERS = {
    "thesaurus": thesaurus_chunks,
    "nomenclature": nomenclature_chunks,
    "nomenclature_dz": nomenclature_dz_chunks,
    "ema": ema_chunks,
    "dwa": dwa_chunks,
    "pharmnet": pharmnet_chunks,
}


def build_chunks():
    for builder in BUILDERS.values():
        yield from builder()


def write_corpus(path=CORPUS_PATH, split_long=True):
    path.parent.mkdir(parents=True, exist_ok=True)
    counts = Counter()
    with open(path, "w", encoding="utf-8") as f:
        for record in build_chunks():
            if split_long:
                for sub in split_long_chunks([record]):
                    f.write(json.dumps(sub, ensure_ascii=False) + "\n")
                    counts[sub["source_id"]] += 1
            else:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                counts[record["source_id"]] += 1
    return counts


def load_corpus(path=CORPUS_PATH):
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records



def split_long_chunks(chunks, max_tokens=512, overlap=50):

    import re
    result = []
    for chunk in chunks:
        words = chunk["text"].split()
        if len(words) <= max_tokens:
            result.append(chunk)
            continue
        
        
        sentences = re.split(r'(?<=[.!?])\s+', chunk["text"])
        current, current_len = [], 0
        sub_idx = 0
        for sent in sentences:
            sent_len = len(sent.split())
            if current_len + sent_len > max_tokens and current:
                
                new_chunk = chunk.copy()
                new_chunk["chunk_id"] = f"{chunk['chunk_id']}#sub{sub_idx}"
                new_chunk["text"] = " ".join(current)
                new_chunk["metadata"] = chunk["metadata"].copy()
                new_chunk["metadata"]["parent_chunk"] = chunk["chunk_id"]
                new_chunk["metadata"]["sub_idx"] = sub_idx
                result.append(new_chunk)
                # Overlap : on garde les `overlap` derniers mots
                current = current[-overlap:] if len(current) > overlap else current
                current_len = len(current)
                sub_idx += 1
            current.append(sent)
            current_len += sent_len
        
        if current:
            new_chunk = chunk.copy()
            new_chunk["chunk_id"] = f"{chunk['chunk_id']}#sub{sub_idx}"
            new_chunk["text"] = " ".join(current)
            new_chunk["metadata"] = chunk["metadata"].copy()
            new_chunk["metadata"]["parent_chunk"] = chunk["chunk_id"]
            new_chunk["metadata"]["sub_idx"] = sub_idx
            result.append(new_chunk)
    return result



