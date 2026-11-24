
from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from .config import INTERIM, PROCESSED
from .normalize import (
    MIPH_CSV,
    PHARMNET_CSV,
    _ascii_upper,
    _read_rows,
    build_dictionary,
    canonical_key,
    canonical_label,
    clean_query,
    normalize_drug,
)
from .textnorm import norm

LEXICON_JSON = PROCESSED / "week_3" / "lexicon.json"
RAW_NOMENCLATURE = PROCESSED.parent / "raw" / "nomenclature" / "algerian_drug_nomenclature.csv"
THESAURUS_JSON = INTERIM / "thesaurus" / "interactions_medicamenteuses.json"


MANUAL_DCI = {"aspirine": "ACIDE ACETYLSALICYLIQUE"}
MANUAL_CLASS = {
    "ains": "anti inflammatoires non steroidiens",
    "a i n s": "anti inflammatoires non steroidiens",
    "anti inflammatoire": "anti inflammatoires non steroidiens",
    "anti inflammatoires": "anti inflammatoires non steroidiens",
    "inhibiteurs calciques": "antagonistes des canaux calciques",
    "inhibiteur calcique": "antagonistes des canaux calciques",
    "antihypertenseur": "antihypertenseurs sauf alpha bloquants",
    "antihypertenseurs": "antihypertenseurs sauf alpha bloquants",
    "iec": "inhibiteurs de l enzyme de conversion",
    "inhibiteurs de l enzyme de conversion": "inhibiteurs de l enzyme de conversion",
    "ara ii": "antagonistes des recepteurs de l angiotensine ii",
    "sartans": "antagonistes des recepteurs de l angiotensine ii",
    "beta bloquant": "beta bloquants sauf esmolol y compris collyres",
    "beta bloquants": "beta bloquants sauf esmolol y compris collyres",
    "diuretique": "diuretiques",
    "diuretiques": "diuretiques",
    "anticoagulant": "anticoagulants oraux",
    "anticoagulants": "anticoagulants oraux",
}


DCI_TYPO_FIXES = {
    "ACIDE ACETYLSALICYTIQUE": "ACIDE ACETYLSALICYLIQUE",
    "PROPANOLOL": "PROPRANOLOL",
    "BISACODYLE": "BISACODYL",
    "SALBUTAMOLE": "SALBUTAMOL",
    "SALBUTAMO": "SALBUTAMOL",
    "CARBOCITEINE": "CARBOCISTEINE",
    "CARBOCYSTEINE": "CARBOCISTEINE",
    "HYDROXYSINE": "HYDROXYZINE",
    "DIOSMECTILE": "DIOSMECTITE",
    "ROPINIROL": "ROPINIROLE",
    "TRAVAPROST": "TRAVOPROST",
}
KEPT_APART = [  
    ["INTERFERON BETA 1A", "INTERFERON BETA 1B"],
    ["PREDNISONE", "PREDNISOLONE"],
]


@dataclass(frozen=True)
class Resolution:
    term: str
    dci: str | None
    classes: tuple[str, ...] = ()
    confidence: float = 0.0
    source: str = ""
    kind: str = "dci"  
    ambiguous: bool = False
    candidates: tuple[str, ...] = ()
    registered: bool = True  



def build_lexicon() -> dict:
    dico = build_dictionary()
    blocks = (
        json.loads(THESAURUS_JSON.read_text(encoding="utf-8")) if THESAURUS_JSON.exists() else []
    )

    
    classes: dict[str, dict] = {}
    dci_classes: dict[str, set[str]] = {}
    class_by_norm: dict[str, str] = {}
    for b in blocks:
        members = [m.strip() for m in (b.get("membres") or "").split(",") if m.strip()]
        if not members:
            continue
        cname = _ascii_upper(b["substance_principale"].strip())
        class_by_norm[norm(b["substance_principale"])] = cname
        labels = []
        for m in members:
            k = canonical_key(m)
            if not k:
                continue
            label = dico.labels.get(k, canonical_label(m))
            labels.append(label)
            dci_classes.setdefault(label, set()).add(cname)
        classes[cname] = {"members": sorted(set(labels)), "aliases": []}

    aliases: dict[str, dict] = {}
    conflicts: list[dict] = []

    def put(term: str, entry: dict) -> None:
        key = norm(term)
        if not key:
            return
        old = aliases.get(key)
        if old and old["dci"] != entry["dci"] and old.get("kind") != "class":
            conflicts.append({"alias": key, "kept": old["dci"], "rejected": entry["dci"],
                              "sources": [old["source"], entry["source"]]})
            return  
        aliases.setdefault(key, entry)

    def classes_for(label: str) -> list[str]:
        return sorted(dci_classes.get(label, ()))

    
    for key, label in dico.labels.items():
        put(label, {"dci": label, "classes": classes_for(label), "confidence": 1.0, "source": "dci"})
    for path in (MIPH_CSV, PHARMNET_CSV):
        col = ("NOM DE MARQUE", "DENOMINATION COMMUNE INTERNATIONALE") if path == MIPH_CSV else (
            "nom_commercial", "dci")
        for _brand, raw_dci in _read_rows(str(path), *col):
            k = canonical_key(raw_dci or "")
            if k and k in dico.labels:
                label = dico.labels[k]
                put(raw_dci, {"dci": label, "classes": classes_for(label), "confidence": 1.0,
                              "source": "dci_variant"})

    
    for brand, keys in dico.brand_to_keys.items():
        labels = sorted(dico.labels.get(k, k) for k in keys)
        if len(labels) == 1:
            put(brand, {"dci": labels[0], "classes": classes_for(labels[0]),
                        "confidence": 0.98, "source": "nomenclature"})
        else:
            aliases.setdefault(norm(brand), {"dci": None, "classes": [], "confidence": 0.0,
                                             "source": "nomenclature", "candidates": labels})
            conflicts.append({"alias": norm(brand), "kept": None, "rejected": labels,
                              "sources": ["nomenclature"], "reason": "marque ambiguë"})

    if RAW_NOMENCLATURE.exists():
        for brand, raw_inn in _read_rows(str(RAW_NOMENCLATURE), "brand_name", "inn"):
            k = canonical_key(raw_inn or "")
            if not k:
                continue
            label = dico.labels.get(k, canonical_label(raw_inn))
            for term in (raw_inn, brand):
                if norm(term) and norm(term) not in aliases:
                    aliases[norm(term)] = {"dci": label, "classes": classes_for(label),
                                           "confidence": 0.9, "source": "nomenclature_raw",
                                           "registered": False}

    
    for term, label in MANUAL_DCI.items():
        aliases[norm(term)] = {"dci": label, "classes": classes_for(label), "confidence": 1.0,
                               "source": "manual"}
    missing = []
    for term, target in MANUAL_CLASS.items():
        cname = class_by_norm.get(target)
        if cname is None:
            missing.append(term)
            continue
        if term not in {norm(a) for a in classes[cname]["aliases"]}:
            classes[cname]["aliases"].append(term.upper())
        aliases[norm(term)] = {"dci": None, "classes": [cname], "confidence": 1.0,
                               "source": "manual", "kind": "class"}
    if missing:
        conflicts.append({"alias": missing, "reason": "classe cible absente du Thésaurus"})

    
    fix = lambda label: DCI_TYPO_FIXES.get(label, label)  
    for c in classes.values():
        c["members"] = sorted({fix(m) for m in c["members"]})
    dci_classes = {}
    for cname, c in classes.items():
        for m in c["members"]:
            dci_classes.setdefault(m, set()).add(cname)
    resolved_now = set()
    for key, e in aliases.items():
        if e.get("kind") == "class":
            continue
        if e.get("candidates"):
            cands = sorted({fix(c) for c in e["candidates"]})
            if len(cands) == 1:  
                e["dci"], e["confidence"] = cands[0], 0.98
                e.pop("candidates")
                resolved_now.add(key)
            else:
                e["candidates"] = cands
        elif e["dci"]:
            e["dci"] = fix(e["dci"])
        if e["dci"]:
            e["classes"] = sorted(dci_classes.get(e["dci"], ()))
    conflicts = [c for c in conflicts if c.get("alias") not in resolved_now]
    return {"version": 1, "aliases": dict(sorted(aliases.items())),
            "classes": dict(sorted(classes.items())), "conflicts": conflicts,
            "data_quality": {"typo_fixes": DCI_TYPO_FIXES, "kept_apart": KEPT_APART,
                             "ambiguous_resolved_by_typo_fix": len(resolved_now)}}


def save_lexicon(path: Path = LEXICON_JSON) -> dict:
    lex = build_lexicon()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(lex, ensure_ascii=False, indent=1), encoding="utf-8")
    load_lexicon.cache_clear()
    return lex



@lru_cache(maxsize=1)
def load_lexicon(path: Path = LEXICON_JSON) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _class_lookup(lex: dict) -> dict[str, str]:
    out = {}
    for cname, c in lex["classes"].items():
        out[norm(cname)] = cname
        for a in c["aliases"]:
            out[norm(a)] = cname
    return out


def resolve(term: str, fuzzy: bool = True) -> Resolution | None:
    """Terme libre (DCI, marque, sel, classe, synonyme) -> Resolution, ou None."""
    lex = load_lexicon()
    for candidate in (norm(term), clean_query(term)):
        entry = lex["aliases"].get(candidate)
        if entry:
            kind = entry.get("kind", "dci")
            amb = entry["dci"] is None and kind == "dci"
            return Resolution(term, entry["dci"], tuple(entry["classes"]), entry["confidence"],
                              entry["source"], kind, amb, tuple(entry.get("candidates", ())),
                              entry.get("registered", True))
    cname = _class_lookup(lex).get(norm(term))
    if cname:
        return Resolution(term, None, (cname,), 1.0, "class", "class")
    if fuzzy:
        m = normalize_drug(term)
        if m.found:
            if m.ambiguous:  
                return Resolution(term, None, (), 0.0, f"fuzzy:{m.method}", "dci", True,
                                  (m.label, *m.alternatives))
            if _is_prefix_of_combination(term, m):  
                return Resolution(term, None, (), 0.0, f"fuzzy:{m.method}", "dci", True, (m.label,))
            entry = lex["aliases"].get(norm(m.label), {})
            return Resolution(term, m.label, tuple(entry.get("classes", ())), round(m.score / 100, 2),
                              f"fuzzy:{m.method}", "dci", False, (), entry.get("registered", True))
    return None


def _is_prefix_of_combination(term: str, match) -> bool:
  
    if "+" not in (match.label or ""):
        return False
    query = clean_query(term)
    return any(
        brand.startswith(query + " ") and match.key in keys
        for brand, keys in build_dictionary().brand_to_keys.items()
    )


def class_members(cls: str) -> list[str]:
    cname = _class_lookup(load_lexicon()).get(norm(cls))
    return list(load_lexicon()["classes"][cname]["members"]) if cname else []


def aliases_for(dci: str) -> list[str]:
    target = _ascii_upper(dci).strip()
    return sorted(a for a, e in load_lexicon()["aliases"].items() if e["dci"] == target)


def stats() -> dict:
    lex = load_lexicon()
    kinds = {}
    for e in lex["aliases"].values():
        kinds[e["source"]] = kinds.get(e["source"], 0) + 1
    return {"aliases": len(lex["aliases"]), "by_source": kinds, "classes": len(lex["classes"]),
            "conflicts": len(lex["conflicts"]),
            "ambiguous_brands": sum(1 for e in lex["aliases"].values() if e.get("candidates"))}