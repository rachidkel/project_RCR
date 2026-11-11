import re
import pandas as pd
from ..config import RAW, PROCESSED
from ..textnorm import norm

SHEETS = {"nomenclature": "nomenclature_active"}
STATUS = {"nomenclature_active": "actif"}


def read_sheet(xlsx, sheet):
    raw = pd.read_excel(xlsx, sheet_name=sheet, header=None, dtype=str)

    hdr_idx = None
    for i in range(min(50, len(raw))):
        row_str = " ".join(str(v).upper() for v in raw.iloc[i] if pd.notna(v))
        if "DCI" in row_str or "NOM DE MARQUE" in row_str:
            hdr_idx = i
            break

    if hdr_idx is None:
        raise ValueError(f"En-tête introuvable dans la feuille '{sheet}'")

    cols = []
    for i, c in enumerate(raw.iloc[hdr_idx]):
        c_clean = re.sub(r"\s+", " ", str(c)).strip()
        cols.append(f"col_{i}" if c_clean in ("", "nan") else c_clean)

    df = raw.iloc[hdr_idx + 1:].copy()
    df.columns = cols
    df = df.dropna(axis=1, how="all").dropna(axis=0, how="all")

    for c in df.columns:
        df[c] = df[c].astype(str).str.strip().replace({"nan": None, "None": None})

    return df.reset_index(drop=True)


def build():
    files = sorted((RAW / "nomenclature").glob("*.xlsx"))
    if not files:
        raise FileNotFoundError("Aucun .xlsx dans data/raw/nomenclature")

    xlsx = files[-1]
    out = PROCESSED / "nomenclature"
    out.mkdir(parents=True, exist_ok=True)

    print(f"Source : {xlsx.name}")
    for sheet in pd.ExcelFile(xlsx).sheet_names:
        n = norm(sheet)
        stem = next((v for k, v in SHEETS.items() if k in n), None)
        if stem is None:
            print(f"  [skip] feuille '{sheet}'")
            continue

        try:
            df = read_sheet(xlsx, sheet)
            df.insert(0, "status", STATUS[stem])
            df.to_csv(out / f"{stem}.csv", index=False, encoding="utf-8-sig")
            print(f"  [ok] {len(df)} lignes → {stem}.csv")
            print(f"       Colonnes : {list(df.columns)}")
        except Exception as e:
            print(f"  [erreur] {sheet} : {e}")