
import csv, json, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from pharmeazor.config import PROCESSED
from pharmeazor.lexicon import resolve, save_lexicon, load_lexicon, stats

lex = save_lexicon()
s = stats(); print(json.dumps(s, ensure_ascii=False, indent=2))

rows, ok = [], 0
with open(PROCESSED / "drugs_verified.csv", encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f):
        res = resolve(r["DCI"])
        good = bool(res and res.dci and not res.ambiguous)
        reg = "oui" if (res and res.registered) else "non"
        ok += good
        rows.append((r["Classe"], r["DCI"], res.dci if res else "—", len(res.classes) if res else 0, ("oui" if good else "NON") + f" (enreg. actif : {reg})"))
n = len(rows)
md = ["| Classe | DCI (liste) | Résolue en | Nb classes Thésaurus | Résolu |", "|---|---|---|---:|---|"]
md += [f"| {a} | {b} | {c} | {d} | {e} |" for a, b, c, d, e in rows]
md.append(f"\n**Couverture : {ok}/{n} = {100*ok/n:.1f} %**")
out = PROCESSED / "week_3" / "lexicon_coverage.md"
out.write_text("\n".join(md), encoding="utf-8")
print("\n".join(md[-1:]), "->", out)
for a, b, c, d, e in rows:
    if not e.startswith("oui") or "actif : non" in e: print("  à regarder:", a, "|", b, "|", c, "| classes:", d)