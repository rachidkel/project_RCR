"""Parse the downloaded ANPP RCP PDFs into structured sections.

Usage:
    python scripts/15_build_anpp.py

Input : data/raw/anpp/pdfs/*.pdf + data/raw/anpp/manifest.json
Output: data/processed/anpp/rcp_sections.json
        data/processed/anpp/rcp_documents.csv
"""
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, "src")

from pharmeazor.parsers.anpp import build_anpp_sections  # noqa: E402


def main():
    documents = build_anpp_sections()
    total_sections = sum(len(document["sections"]) for document in documents)
    print(f"{len(documents)} RCP, {total_sections} sections extraites")
    for document in documents:
        keys = ", ".join(document["sections"])
        print(f"  {document['product'][:45]:<45} {document['dci'][:35]:<35} [{keys}]")


if __name__ == "__main__":
    main()
