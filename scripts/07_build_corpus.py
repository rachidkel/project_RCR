import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, "src")
from pharmeazor.config import CORPUS_PATH
from pharmeazor.corpus import write_corpus


counts = write_corpus()
total = sum(counts.values())
print(f"Corpus : {total} chunks → {CORPUS_PATH}\n")
for source_id, n in sorted(counts.items(), key=lambda kv: -kv[1]):
    print(f"  {n:>6}  {source_id}")
