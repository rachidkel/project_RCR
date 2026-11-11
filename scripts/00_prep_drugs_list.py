import sys
sys.path.insert(0, "src")
import pandas as pd
from pharmeazor.config import RAW, PROCESSED

xlsx = RAW / "drugs" / "Projet2_Liste_40_medicaments.xlsx"
out = PROCESSED / "drugs.csv"
out.parent.mkdir(parents=True, exist_ok=True)

df = pd.read_excel(xlsx, sheet_name="Médicaments")
df = df.dropna(how="all")
for col in df.columns:
    df[col] = df[col].astype(str).str.strip()

df.to_csv(out, index=False, encoding="utf-8-sig")
print(f"OK : {len(df)} lignes → {out}")
print(f"Colonnes : {list(df.columns)}")