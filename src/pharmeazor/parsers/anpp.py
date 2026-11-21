"""Parse ANPP RCP PDFs into structured sections.

Each RCP is a PDF with numbered sections (1.1, 1.2, 4.1 ... 4.9).  The parser
keeps the original sentences and records provenance (URL, collection date,
SHA-256).  It is deliberately rule-based: the RCP template is stable enough,
and every extracted section remains verifiable against the PDF.

Usage:
    python scripts/15_build_anpp.py
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import pymupdf

from ..config import PROCESSED, RAW
from ..textnorm import norm

ANPP_DIR = RAW / "anpp"
PDF_DIR = ANPP_DIR / "pdfs"
MANIFEST = ANPP_DIR / "manifest.json"
OUT_DIR = PROCESSED / "anpp"
OUT_JSON = OUT_DIR / "rcp_sections.json"
OUT_CSV = OUT_DIR / "rcp_documents.csv"

# Sections kept in the corpus. 1/1.1/1.2 identify the product; 4.x are clinical.
SECTIONS = {
    "1": {
        "title": "Dénomination du médicament",
        "pattern": r"D[ée]nomination du m[ée]dicament",
    },
    "1.1": {
        "title": "Dénomination commerciale",
        "pattern": r"D[ée]nomination commerciale(?:\s*,\s* dosage[^\n:]*)?",
    },
    "1.2": {
        "title": "Dénomination commune internationale",
        "pattern": r"D[ée]nomination commune(?:\s+internationale)?(?:\s*\(DCI\))?",
    },
    "4.1": {
        "title": "Indications thérapeutiques",
        "pattern": r"Indications(?:\s+th[ée]rapeutiques)?",
    },
    "4.2": {
        "title": "Posologie et mode d'administration",
        "pattern": r"Posologie(?:\s+et\s+mode\s+d[’']administration)?",
    },
    "4.3": {
        "title": "Contre-indications",
        "pattern": r"Contre[- ]?indications",
    },
    "4.4": {
        "title": "Mises en garde et précautions d'emploi",
        "pattern": r"Mises en garde(?:\s+sp[ée]ciales)?(?:\s+et\s+pr[ée]cautions[^\n:]*)?",
    },
    "4.5": {
        "title": "Interactions médicamenteuses",
        "pattern": r"Interactions(?:\s+(?:m[ée]dicamenteuses|avec)[^\n:]*)?",
    },
    "4.6": {
        "title": "Fertilité, grossesse et allaitement",
        "pattern": r"Fertilit[ée](?:\s*,?\s*[Gg]rossesse[^\n:]*)?",
    },
    "4.8": {
        "title": "Effets indésirables",
        "pattern": r"Effets ind[ée]sirables",
    },
    "4.9": {
        "title": "Surdosage",
        "pattern": r"Surdosage[^\n:]*",
    },
}

# Any RCP heading is a boundary, even when we do not keep its content.
HEADING_RE = re.compile(
    r"(?m)^\s*(\d+(?:\.\d+)*)\.?\s*("
    r"D[ÉE]NOMINATION|COMPOSITION|FORME\s+PHARMACEUTIQUE|DONN[ÉE]ES\s+CLINIQUES|"
    r"PROPRI[ÉE]T[ÉE]S\s+PHARMACOLOGIQUES|DONN[ÉE]ES\s+PHARMACEUTIQUES|"
    r"Indications|Posologie|Contre[- ]?indications|Mises\s+en\s+garde|"
    r"Interactions|Fertilit[ée]|Effets\s+ind[ée]sirables|Surdosage|"
    r"Description|Formule|Liste\s+des\s+excipients|Incompatibilit[ée]s|"
    r"Dur[ée]e\s+de\s+conservation|Pr[ée]cautions\s+particuli[èe]res|"
    r"Nature\s+et\s+(?:contenance|contenu)|"
    r"Propri[ée]t[ée]s\s+pharmacodynamiques|Propri[ée]t[ée]s\s+pharmacocin[ée]tiques|"
    r"Donn[ée]es\s+de\s+s[ée]curit[ée]"
    r")",
    re.IGNORECASE,
)

HEADER_PATTERNS = [
    re.compile(r"^\s*ANNEXE\s*I\s*$", re.IGNORECASE),
    re.compile(r"^\s*R[ÉE]SUM[ÉE]\s+DES\s+CARACT[ÉE]RISTIQUES.*$", re.IGNORECASE),
    re.compile(r"^\s*PRODUIT\s*$", re.IGNORECASE),
    re.compile(r"^\s*Version\s*:.*$", re.IGNORECASE),
    re.compile(r"^\s*Code\s*:.*$", re.IGNORECASE),
    re.compile(r"^\s*Page\s+\d+\s+sur\s+\d+\s*$", re.IGNORECASE),
    re.compile(r"^\s*\d+\s*$"),
]


def _section_regex(key: str) -> re.Pattern:
    pattern = SECTIONS[key]["pattern"]
    return re.compile(
        rf"(?m)^[ \t]*{re.escape(key)}(?:\.(?!\d))?[ \t]*({pattern})[ \t]*:?[ \t]*([^\n]*)",
        re.IGNORECASE,
    )


def _candidate_sections(text: str) -> dict[str, dict]:
    """Return the longest occurrence of each kept section (skips table-of-contents hits)."""
    boundaries = sorted(match.start() for match in HEADING_RE.finditer(text))

    matches = []
    for key in SECTIONS:
        for match in _section_regex(key).finditer(text):
            matches.append(
                {
                    "key": key,
                    "start": match.start(),
                    "end": match.end(),
                    "title": match.group(1).strip(),
                    "rest": match.group(2).strip(),
                }
            )

    matches.sort(key=lambda item: item["start"])
    for item in matches:
        next_start = next(
            (start for start in boundaries if start > item["start"]), len(text)
        )
        item["content"] = (item["rest"] + "\n" + text[item["end"]:next_start]).strip()

    best: dict[str, dict] = {}
    for item in matches:
        key = item["key"]
        if key not in best or len(item["content"]) > len(best[key]["content"]):
            best[key] = item
    return best


def _repeated_headers(text: str, min_repeats: int = 3, min_len: int = 15, max_len: int = 120) -> set[str]:
    counts: dict[str, int] = {}
    for line in text.splitlines():
        key = norm(line)
        if key:
            counts[key] = counts.get(key, 0) + 1
    return {
        key
        for key, count in counts.items()
        if count >= min_repeats and min_len <= len(key) <= max_len
    }


def _clean_content(
    text: str, repeated: set[str], product: str | None = None, keep_repeated: bool = False
) -> str:
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if any(pattern.match(stripped) for pattern in HEADER_PATTERNS):
            continue
        if not keep_repeated and norm(stripped) in repeated:
            continue
        if product and norm(stripped) == norm(product):
            continue
        stripped = stripped.replace("\uf0b7", "-").replace("•", "-")
        lines.append(stripped)
    return re.sub(r"\s+", " ", " ".join(lines)).strip()


def _first_text(sections: dict, key: str, limit: int = 240) -> str:
    text = sections.get(key, {}).get("text", "")
    return text[:limit].strip(" :;,-")


def _clean_field(text: str, limit: int = 160) -> str:
    """Trim a product/DCI field and drop trailing section bleed."""
    text = re.sub(r"\s+", " ", text or "").strip(" :;,-")
    text = re.sub(r"^\s*\d+(?:\.\d+)*\.?\s*", "", text)
    text = re.split(
        r"\s*(?:\d+\s*\.?\s*(?:COMPOSITION|FORME\s+PHARMACEUTIQUE|DONN[ÉE]ES)\b|"
        r"\bDCI\b|\bForme\s+pharmaceutique\b)",
        text,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    return text.strip(" :;,-")[:limit]


def _valid_field(text: str) -> bool:
    """Reject values that are really the next section heading."""
    return bool(text) and not re.match(
        r"^(?:D[ée]nomination|Composition|Forme\s+pharmaceutique|"
        r"Indications|Posologie|Contre[- ]?indications)\b",
        text,
        re.IGNORECASE,
    )


def _load_manifest() -> dict[str, dict]:
    if not MANIFEST.exists():
        return {}
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    by_file: dict[str, dict] = {}
    for entry in payload.get("entrees", []):
        for document in entry.get("documents", []):
            filename = document.get("fichier")
            if not filename:
                continue
            by_file[Path(filename).name] = {
                **document,
                "requested_dci": entry.get("dci", ""),
                "collected_at": entry.get("collecte_le", ""),
            }
    return by_file


def parse_pdf(path: Path, manifest_entry: dict | None = None) -> dict:
    document = pymupdf.open(path)
    text = "\n".join(page.get_text() for page in document)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    repeated = _repeated_headers(text)
    candidates = _candidate_sections(text)

    sections: dict[str, dict] = {}
    for key, item in candidates.items():
        content = _clean_content(
            item["content"], repeated, keep_repeated=key in {"1", "1.1", "1.2"}
        )
        if len(content) >= 3:
            sections[key] = {"title": SECTIONS[key]["title"], "text": content}

    requested_dci = _clean_field((manifest_entry or {}).get("requested_dci", ""))

    product = _clean_field(_first_text(sections, "1.1"))
    if not _valid_field(product):
        product = _clean_field(_first_text(sections, "1"))
    if not _valid_field(product):
        product = requested_dci or path.stem

    dci = _clean_field(_first_text(sections, "1.2"))
    if not _valid_field(dci):
        match = re.search(
            r"([A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ /\-]{2,50})\s*\(DCI\)",
            text,
            re.IGNORECASE,
        )
        dci = _clean_field(match.group(1)) if match else requested_dci
    if not _valid_field(dci):
        dci = requested_dci

    return {
        "doc_id": f"anpp:{path.stem}",
        "file": str(path),
        "url": (manifest_entry or {}).get("url", ""),
        "collected_at": (manifest_entry or {}).get("collected_at", ""),
        "sha256": (manifest_entry or {}).get("sha256", ""),
        "requested_dci": requested_dci,
        "product": product,
        "dci": dci,
        "sections": sections,
    }


def build_anpp_sections(pdf_dir: Path = PDF_DIR, manifest_path: Path = MANIFEST) -> list[dict]:
    if not pdf_dir.exists():
        raise FileNotFoundError(f"Dossier ANPP introuvable : {pdf_dir}")

    manifest = _load_manifest() if manifest_path.exists() else {}
    documents = []
    for path in sorted(pdf_dir.glob("*.pdf")):
        entry = manifest.get(path.name)
        parsed = parse_pdf(path, entry)
        if parsed["sections"]:
            documents.append(parsed)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(documents, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "doc_id",
                "product",
                "dci",
                "requested_dci",
                "sections",
                "chars",
                "url",
                "collected_at",
                "sha256",
            ]
        )
        for document in documents:
            writer.writerow(
                [
                    document["doc_id"],
                    document["product"],
                    document["dci"],
                    document["requested_dci"],
                    ", ".join(document["sections"]),
                    sum(len(section["text"]) for section in document["sections"].values()),
                    document["url"],
                    document["collected_at"],
                    document["sha256"],
                ]
            )

    return documents


if __name__ == "__main__":
    import sys

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    docs = build_anpp_sections()
    print(f"{len(docs)} RCP parsés → {OUT_JSON}")
    for document in docs:
        print(
            f"  {document['doc_id'][:16]:<16} {document['dci'][:38]:<38} "
            f"{len(document['sections'])} sections"
        )
