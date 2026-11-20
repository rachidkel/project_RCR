"""Collecte des RCP officiels depuis la plateforme ANPP (rcp.anpp.dz).

La plateforme est une application Laravel Livewire : la recherche part en POST
sur `/livewire/update`, avec le jeton CSRF, les cookies de session et le
« snapshot » du composant lus sur la page d'accueil. Chaque résultat pointe
vers un PDF sous `/storage/rcp-pdfs/`.

Usage :
    python scripts/14_collect_anpp.py --dry-run          # liste, sans télécharger
    python scripts/14_collect_anpp.py --limit 3          # 3 médicaments, pour tester
    python scripts/14_collect_anpp.py                    # les 40 du périmètre

Conforme à `docs/week_1/legal_sources.md` : volumétrie limitée au périmètre du
projet, une requête toutes les 3 s, User-Agent explicite, manifest daté.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pharmeazor.config import PROCESSED, RAW  # noqa: E402
from pharmeazor.textnorm import norm  # noqa: E402

BASE = "https://rcp.anpp.dz"
UPDATE_URL = f"{BASE}/livewire/update"
USER_AGENT = "Pharmeazor/0.1 (projet academique; collecte ponctuelle)"
DELAY_S = 3.0
TIMEOUT_S = 60

CSRF_RE = re.compile(r'name="csrf-token" content="([^"]+)"')
SNAPSHOT_RE = re.compile(r'wire:snapshot="([^"]+)"')
PDF_RE = re.compile(r'href="(https://rcp\.anpp\.dz/storage/rcp-pdfs/[^"]+\.pdf)"')


def drug_queries(row: dict) -> list[str]:
    """Requêtes à essayer pour un médicament : DCI puis marques du référentiel.

    La recherche de la plateforme est sensible à la casse ET aux accents :
    `PARACETAMOL` renvoie 5 RCP, `paracétamol` et `PARACÉTAMOL` en renvoient 0.
    Toutes les requêtes sont donc normalisées en majuscules sans accent.
    """
    raw = []
    dci = (row.get("DCI") or "").strip()
    if dci:
        raw.append(dci)
    brands = (row.get("Noms commerciaux trouvés") or "").split(";")
    for brand in brands[:6]:
        brand = brand.strip()
        if brand and brand.upper() != "NAN":
            raw.append(brand)
    seen, unique = set(), []
    for q in raw:
        key = norm(q).upper()
        if key and key not in seen:
            seen.add(key)
            unique.append(key)
    return unique[:7]


class AnppClient:
    """Session HTTP + handshake Livewire."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.csrf = None
        self.snapshot = None

    def connect(self):
        response = self.session.get(BASE + "/", timeout=TIMEOUT_S)
        response.raise_for_status()
        page = response.text
        csrf = CSRF_RE.search(page)
        snapshot = SNAPSHOT_RE.search(page)
        if not csrf or not snapshot:
            raise RuntimeError(
                "Jeton CSRF ou snapshot Livewire introuvable : la page a changé."
            )
        self.csrf = csrf.group(1)
        self.snapshot = html.unescape(snapshot.group(1))
        return self

    def search(self, query: str) -> list[str]:
        """Renvoie les URLs de PDF pour une requête."""
        payload = {
            "_token": self.csrf,
            "components": [
                {
                    "snapshot": self.snapshot,
                    "updates": {"query": query},
                    "calls": [{"path": "", "method": "search", "params": []}],
                }
            ],
        }
        response = self.session.post(
            UPDATE_URL,
            json=payload,
            timeout=TIMEOUT_S,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-Livewire": "true",
                "X-CSRF-TOKEN": self.csrf,
                "Referer": BASE + "/",
            },
        )
        response.raise_for_status()
        try:
            component = (response.json().get("components") or [{}])[0]
        except ValueError:
            raise RuntimeError("Réponse non JSON de /livewire/update")
        fragment = (component.get("effects") or {}).get("html") or ""
        # Le snapshot évolue après chaque action : on le réutilise.
        if component.get("snapshot"):
            self.snapshot = component["snapshot"]
        return list(dict.fromkeys(PDF_RE.findall(fragment)))


def download(client: AnppClient, url: str, folder: Path) -> dict:
    response = client.session.get(url, timeout=TIMEOUT_S)
    response.raise_for_status()
    digest = hashlib.sha256(response.content).hexdigest()
    name = url.rsplit("/", 1)[-1]
    path = folder / name
    path.write_bytes(response.content)
    return {
        "url": url,
        "fichier": str(path),
        "octets": len(response.content),
        "sha256": digest,
    }


def load_drugs(limit: int | None) -> list[dict]:
    with open(PROCESSED / "drugs_verified.csv", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return rows[:limit] if limit else rows


def main():
    parser = argparse.ArgumentParser(description="Collecte des RCP ANPP")
    parser.add_argument("--limit", type=int, default=None, help="nombre de médicaments")
    parser.add_argument("--dry-run", action="store_true", help="lister sans télécharger")
    parser.add_argument("--out", default=str(RAW / "anpp"), help="dossier de sortie")
    args = parser.parse_args()

    out = Path(args.out)
    pdfs = out / "pdfs"
    pdfs.mkdir(parents=True, exist_ok=True)
    manifest_path = out / "manifest.json"

    drugs = load_drugs(args.limit)
    client = AnppClient().connect()
    print(f"ANPP — {len(drugs)} médicaments, sortie : {out}")
    print(f"Connecté (CSRF ok), pause {DELAY_S} s entre requêtes\n")

    manifest = []
    found = 0
    for index, row in enumerate(drugs, start=1):
        dci = (row.get("DCI") or "").strip()
        urls: list[str] = []
        used = None
        for query in drug_queries(row):
            urls = client.search(query)
            time.sleep(DELAY_S)
            if urls:
                used = query
                break
        status = f"{len(urls)} RCP" if urls else "aucun RCP"
        print(f"[{index:>2}/{len(drugs)}] {dci:<38} {status}"
              + (f"  (requête : {used})" if used else ""))
        if not urls:
            manifest.append({"dci": dci, "requete": None, "documents": []})
            continue
        found += 1
        documents = []
        if not args.dry_run:
            for url in urls:
                try:
                    documents.append(download(client, url, pdfs))
                    time.sleep(DELAY_S)
                except requests.RequestException as exc:
                    documents.append({"url": url, "erreur": str(exc)})
        manifest.append(
            {
                "dci": dci,
                "requete": used,
                "source": "ANPP — plateforme RCP (rcp.anpp.dz)",
                "collecte_le": datetime.now().isoformat(timespec="seconds"),
                "documents": documents,
            }
        )

    manifest_path.write_text(
        json.dumps(
            {
                "source": "ANPP — RCP",
                "base": BASE,
                "collecte_le": datetime.now().isoformat(timespec="seconds"),
                "medicaments_demandes": len(drugs),
                "medicaments_avec_rcp": found,
                "entrees": manifest,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\n{found}/{len(drugs)} médicaments avec au moins un RCP")
    print(f"Manifest : {manifest_path}")
    if args.dry_run:
        print("Mode --dry-run : aucun fichier téléchargé.")


if __name__ == "__main__":
    main()
