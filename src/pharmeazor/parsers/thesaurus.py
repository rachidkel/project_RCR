import fitz  # PyMuPDF
from ..config import RAW, INTERIM

NOISE = ("boulevard anatole france", "www.ansm.sante.fr")
KEYS = ("interactions", "substances", "classes")

def pdf_pages(pdf):
    doc = fitz.open(pdf)
    for i, page in enumerate(doc, 1):
        lines = [l.strip() for l in page.get_text("text", sort=True).splitlines()]
        lines = [l for l in lines if l]
        # page number: only first/last line of the page, never in the body
        if lines and lines[-1].isdigit(): lines.pop()
        if lines and lines[0].isdigit(): lines.pop(0)
        lines = [l for l in lines if not any(n in l.lower() for n in NOISE)]
        yield i, lines

def build():
    out = INTERIM / "thesaurus"
    out.mkdir(parents=True, exist_ok=True)
    pdfs = list((RAW / "ansm_thesaurus").glob("*.pdf"))
    for key in KEYS:
        match = [p for p in pdfs if key in p.name.lower()]
        if not match:
            raise FileNotFoundError(f"No PDF for '{key}' in data/raw/ansm_thesaurus")
        pdf = match[0]
        n_pages = n_lines = empty = 0
        with open(out / f"{key}.txt", "w", encoding="utf-8") as f:
            for i, lines in pdf_pages(pdf):
                n_pages += 1
                if not lines:
                    empty += 1
                f.write(f"\n=== PAGE {i} ===\n")
                f.write("\n".join(lines) + "\n")
                n_lines += len(lines)
        print(f"[ok] {pdf.name}: {n_pages} pages, {n_lines} lines, {empty} empty pages")
