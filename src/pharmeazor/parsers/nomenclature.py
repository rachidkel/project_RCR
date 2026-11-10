import re
import pandas as pd
from ..config import RAW, PROCESSED
from ..textnorm import norm

# normalized sheet-name fragment -> output file stem
SHEETS = {"nomenclature": "nomenclature_active",
          "renouvel": "non_renouveles",
          "retrait": "retraits"}
STATUS = {"nomenclature_active": "actif",
          "non_renouveles": "non_renouvele",
          "retraits": "retire"}

def read_sheet(xlsx, sheet):
    raw = pd.read_excel(xlsx, sheet_name=sheet, header=None, dtype=str)
    # header row = first row among the first 40 that is almost as full as the fullest one
    counts = raw.head(40).notna().sum(axis=1)
    hdr = int(counts[counts >= counts.max() * 0.7].index[0])

    cols = []
    for i, c in enumerate(raw.iloc[hdr]):
        c = re.sub(r"\s+", " ", str(c)).strip()
        cols.append(f"col_{i}" if c in ("", "nan") else c)

    df = raw.iloc[hdr + 1:].copy()
    df.columns = cols
    df = df.dropna(axis=1, how="all").dropna(axis=0, how="all")
    for c in df.columns:
        df[c] = df[c].str.strip()
    return df.reset_index(drop=True), hdr

def build():
    files = sorted((RAW / "nomenclature").glob("*.xlsx"))
    if not files:
        raise FileNotFoundError("No .xlsx in data/raw/nomenclature")
    xlsx = files[-1]
    out = PROCESSED / "nomenclature"
    out.mkdir(parents=True, exist_ok=True)

    print(f"Source: {xlsx.name}")
    for sheet in pd.ExcelFile(xlsx).sheet_names:
        n = norm(sheet)
        stem = next((v for k, v in SHEETS.items() if k in n), None)
        if stem is None:
            print(f"  [skip] sheet '{sheet}'")
            continue
        df, hdr = read_sheet(xlsx, sheet)
        df.insert(0, "status", STATUS[stem])
        df.to_csv(out / f"{stem}.csv", index=False, encoding="utf-8-sig")
        print(f"  [ok] '{sheet}' header at row {hdr}, {len(df)} rows -> {stem}.csv")
        print(f"       columns: {list(df.columns)}")
