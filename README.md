# Pharmeazor
 
Drug-safety assistant for pharmacists and health students. It builds a knowledge base of medicine documents from several sources, cross-checks them, detects disagreements, and answers questions **in French with exact source citations**.

Course project: **RCR, M1-AI, Université Constantine 2 - Abdelhamid Mehri (NTIC, IFA)**.

## Principles
 
1. The system never prescribes or diagnoses. It helps retrieve and check information; the decision stays with the expert.
2. No source, no display. Giving an answer that is not based on exact sources is not safe.
3. Every answer must appear with its exact sources.
4. When sources disagree, the higher authority source wins and the system says why.

## Sources

| Sources |
|---------|
|         |

## Repository structure
 
```
.
├── README.md
├── requirements.txt
├── .env.example
├── config/
├── data/
│   ├── raw/<source>/    # originals
│   ├── interim/            # text extracted from PDFs (git-ignored)
│   └── processed/<source>/   # clean tables (CSV)
├── db/                     # SQLite database (git-ignored)
├── src/pharmeazor/         # all reusable logic
│   ├── config.py           # paths and settings
│   ├── textnorm.py         # text normalization
│   └── parsers/            # one script per source, each with a build() function
├── scripts/                # thin entry points that call the parsers
├── docs/                   # mission, journal, weekly reports, notes
└── tests/
```
 
Data stages: `raw` (as downloaded, never edited) -> `interim` (converted, not yet structured) -> `processed` (final clean structured tables).

## Setup
 
Requirements: Python 3.12, Git.
 
### Ubuntu / Linux
 
```bash
git clone <repo-url> && cd <repo>
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then edit .env
```
 
### Windows 11

```powershell
git clone <repo-url>
cd <repo>
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      # then edit .env
```

## Git workflow
 
- Never commit directly to `main`.
- Branch per task: `git checkout -b <topic>/<short-name>`, commit, push, open a pull request.
- Pull `main` before starting a new branch.
- Do not commit `.env`, `.venv/`, the SQLite database or `data/interim/`.
- Do not edit files in `data/raw/`.

## Limits
 
This is an academic project. It is not a medical device and must not be used for real clinical decisions.
