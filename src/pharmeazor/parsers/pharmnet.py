"""Collecte du référentiel Pharm'Net (pharmnet-dz.com).

Pharm'Net est un référentiel algérien des médicaments. Son site est une SPA
qui lit une API REST Supabase publique : on interroge donc directement cette
API (mêmes données que le site), sans scraper le HTML.

Source     : https://pharmnet-dz.com  (robots.txt : Allow /, espaces privés exclus)
API        : https://<projet>.supabase.co/rest/v1/<table>
Stages     : data/raw/pharmnet/*.json  ->  data/processed/pharmnet/*.csv

Tables collectées :
    produits               ~9 500 fiches (nom commercial, DCI, forme, dosage,
                           conditionnement, prix, enregistrement, labo...)
    dci                    ~3 000 dénominations communes internationales
    classes_therapeutiques ~28 classes
    laboratoires           ~980 laboratoires

La table `interactions` n'est pas lisible avec la clé publique (RLS) : les
interactions restent couvertes par le thésaurus ANSM.
"""

import json
import time
from datetime import datetime

import pandas as pd
import requests

from ..config import (
    PHARMNET_API_KEY,
    PHARMNET_API_URL,
    PROCESSED,
    RAW,
    REQUEST_DELAY_S,
    REQUEST_TIMEOUT_S,
)
from ..textnorm import norm

PAGE_SIZE = 1000

# table -> colonne de tri stable pour la pagination
TABLES = {
    "produits": "id",
    "dci": "code",
    "classes_therapeutiques": "code",
    "laboratoires": "id",
}

PRODUCT_COLS = [
    "id",
    "num_enregistrement",
    "nom_commercial",
    "dci_code",
    "laboratoire_id",
    "forme",
    "dosage",
    "conditionnement",
    "liste",
    "type",
    "statut_fab",
    "registre",
    "circuit_hop",
    "circuit_off",
    "stabilite_mois",
    "date_enr_initial",
    "date_enr_final",
    "prix_ppa",
    "tarif_ref",
    "code_barre",
    "en_rupture",
    "rupture_depuis",
    "notice_url",
    "rcp_url",
    "image_url",
    "observation",
    "updated_at",
    "created_at",
]

HEADERS = {
    "apikey": PHARMNET_API_KEY,
    "Authorization": f"Bearer {PHARMNET_API_KEY}",
    "Prefer": "count=exact",
    "User-Agent": "Pharmeazor/0.1 (projet academique; collecte ponctuelle)",
}


def _get(table, offset):
    """GET paginé avec 3 tentatives et pause entre les requêtes."""
    params = {
        "select": "*",
        "order": f"{TABLES[table]}.asc",
        "limit": PAGE_SIZE,
        "offset": offset,
    }
    last_error = None
    for attempt in range(3):
        try:
            r = requests.get(
                f"{PHARMNET_API_URL}/{table}",
                params=params,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT_S,
            )
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            last_error = e
            if attempt < 2:
                time.sleep(REQUEST_DELAY_S * (attempt + 1))
    raise RuntimeError(f"Échec de la collecte de '{table}' : {last_error}")


def _total_from_header(r):
    """Content-Range : '0-999/9560' -> 9560."""
    content_range = r.headers.get("content-range", "")
    if "/" not in content_range:
        return None
    total = content_range.rsplit("/", 1)[1]
    return None if total in ("", "*") else int(total)


def fetch_table(table, limit=None):
    """Télécharge une table et renvoie (lignes, total annoncé par l'API)."""
    rows, total = [], None

    def target():
        if total is None:
            return float("inf")
        return min(total, limit) if limit is not None else total

    while len(rows) < target():
        r = _get(table, len(rows))
        if total is None:
            total = _total_from_header(r)
        batch = r.json()
        if not batch:
            break
        rows.extend(batch)
        if limit is not None:
            rows = rows[:limit]
        print(f"  {table}: {len(rows)}/{total if total is not None else '?'}")
        if len(rows) < target():
            time.sleep(REQUEST_DELAY_S)
    return rows, total


def _save_raw(stamp, table, rows):
    raw_dir = RAW / "pharmnet"
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"{stamp}_{table}.json"
    path.write_text(
        json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    return path


def _clean(rows):
    """DataFrame avec noms de colonnes en minuscules et chaînes nettoyées."""
    df = pd.DataFrame(rows)
    if df.empty:
        return df

    if "Tarif_Ref" in df.columns and "tarif_ref" in df.columns:
        df = df.drop(columns=["Tarif_Ref"])
    df.columns = [str(c).strip().lower() for c in df.columns]

    for c in df.columns:
        # pandas 3 infère le dtype « str » : tester aussi is_string_dtype.
        if df[c].dtype == object or pd.api.types.is_string_dtype(df[c]):
            df[c] = (
                df[c]
                .astype("string")
                .str.replace(r"\s+", " ", regex=True)
                .str.strip()
                .replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
            )
    return df


def _build_products(produits, dci, classes, labos):
    df = _clean(produits)
    df = df[[c for c in PRODUCT_COLS if c in df.columns]]

    for c in ("prix_ppa", "tarif_ref", "stabilite_mois"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
            # 0 DZD n'est pas un prix plausible : c'est une valeur manquante.
            df.loc[df[c] <= 0, c] = pd.NA

    dci = _clean(dci).rename(
        columns={
            "code": "dci_code",
            "denomination": "dci",
            "sous_classe": "dci_sous_classe",
            "classe_code": "classe_code",
            "description": "dci_description",
        }
    )
    dci = dci.drop(columns=["created_at"], errors="ignore")

    classes = _clean(classes).rename(
        columns={"code": "classe_code", "libelle": "classe_libelle",
                 "couleur": "classe_couleur"}
    )

    labos = _clean(labos).rename(
        columns={
            "id": "laboratoire_id",
            "nom": "laboratoire",
            "pays": "laboratoire_pays",
            "est_local": "laboratoire_local",
            "verifie": "laboratoire_verifie",
            "fusionne_vers": "laboratoire_fusionne_vers",
        }
    )
    labos = labos[
        [
            c
            for c in (
                "laboratoire_id",
                "laboratoire",
                "laboratoire_pays",
                "laboratoire_local",
                "laboratoire_verifie",
                "laboratoire_fusionne_vers",
            )
            if c in labos.columns
        ]
    ].drop_duplicates("laboratoire_id")

    df = df.merge(dci, on="dci_code", how="left")
    df = df.merge(classes, on="classe_code", how="left")
    df = df.merge(labos, on="laboratoire_id", how="left")

    # Source corrompue : 47 laboratoires ont une date dans le champ « pays ».
    # Ce ne sont pas des pays, on les remplace par une valeur manquante.
    if "laboratoire_pays" in df.columns:
        date_like = df["laboratoire_pays"].str.match(r"^\d{4}-\d{2}-\d{2}", na=False)
        df.loc[date_like, "laboratoire_pays"] = pd.NA

    df["nom_commercial_norm"] = df["nom_commercial"].map(norm)
    df["dci_norm"] = df["dci"].fillna(df["dci_code"]).map(norm)

    ordered = [
        "id",
        "num_enregistrement",
        "nom_commercial",
        "nom_commercial_norm",
        "dci_code",
        "dci",
        "dci_norm",
        "dci_sous_classe",
        "classe_code",
        "classe_libelle",
        "laboratoire_id",
        "laboratoire",
        "laboratoire_pays",
        "laboratoire_local",
        "laboratoire_verifie",
        "forme",
        "dosage",
        "conditionnement",
        "liste",
        "type",
        "statut_fab",
        "registre",
        "circuit_hop",
        "circuit_off",
        "stabilite_mois",
        "date_enr_initial",
        "date_enr_final",
        "prix_ppa",
        "tarif_ref",
        "code_barre",
        "en_rupture",
        "rupture_depuis",
        "notice_url",
        "rcp_url",
        "image_url",
        "observation",
        "updated_at",
        "created_at",
    ]
    return df[[c for c in ordered if c in df.columns]]


def _write_processed(payloads):
    """Écrit les CSV nettoyés à partir des données brutes en mémoire."""
    out = PROCESSED / "pharmnet"
    out.mkdir(parents=True, exist_ok=True)

    produits = _build_products(
        payloads["produits"],
        payloads["dci"],
        payloads["classes_therapeutiques"],
        payloads["laboratoires"],
    )
    produits.to_csv(out / "produits.csv", index=False, encoding="utf-8-sig")
    actifs = produits[produits["registre"] == "ENREGISTRE"]
    actifs.to_csv(
        out / "produits_enregistres.csv", index=False, encoding="utf-8-sig"
    )

    for key, name in (
        ("dci", "dci.csv"),
        ("classes_therapeutiques", "classes_therapeutiques.csv"),
        ("laboratoires", "laboratoires.csv"),
    ):
        df = _clean(payloads[key])
        df.to_csv(out / name, index=False, encoding="utf-8-sig")

    print(f"\n[ok] produits                : {len(produits)} lignes")
    print(f"     dont enregistrés        : {len(actifs)}")
    print(f"     DCI / classes / labos   : {len(payloads['dci'])} / "
          f"{len(payloads['classes_therapeutiques'])} / "
          f"{len(payloads['laboratoires'])}")
    print(f"     colonnes produits       : {len(produits.columns)}")
    print(f"[ok] Dossier : {out}")


def build(limit=None):
    """Collecte et nettoie les tables Pharm'Net.

    limit : nombre maximum de fiches produits (None = tout le catalogue).
    """
    if limit is not None and limit <= 0:
        raise ValueError("limit doit être un entier strictement positif")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print(f"Pharm'Net — collecte du {stamp}")
    payloads, counts = {}, {}
    for table in TABLES:
        table_limit = limit if table == "produits" else None
        rows, total = fetch_table(table, limit=table_limit)
        expected = total
        if total is not None and table_limit is not None:
            expected = min(total, table_limit)
        if expected is not None and len(rows) != expected:
            raise RuntimeError(
                f"{table}: {len(rows)} lignes reçues, {expected} attendues"
            )
        path = _save_raw(stamp, table, rows)
        print(f"  [raw] {path.relative_to(RAW.parent)} ({len(rows)} lignes)")
        payloads[table] = rows
        counts[table] = len(rows)

    manifest = {
        "source": "Pharm'Net",
        "site": "https://pharmnet-dz.com",
        "api": PHARMNET_API_URL,
        "collected_at": datetime.now().isoformat(timespec="seconds"),
        "tables": counts,
    }
    manifest_path = RAW / "pharmnet" / f"{stamp}_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"  [raw] {manifest_path.name}")

    _write_processed(payloads)


def build_from_raw(stamp):
    """Reconstruit les CSV depuis un snapshot brut, sans nouvel appel réseau."""
    raw_dir = RAW / "pharmnet"
    payloads = {}
    for table in TABLES:
        path = raw_dir / f"{stamp}_{table}.json"
        if not path.exists():
            raise FileNotFoundError(f"Snapshot introuvable : {path}")
        payloads[table] = json.loads(path.read_text(encoding="utf-8"))

    print(f"Pharm'Net — retraitement du snapshot {stamp}")
    _write_processed(payloads)
