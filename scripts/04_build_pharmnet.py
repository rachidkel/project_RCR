import argparse
import sys

sys.path.insert(0, "src")
from pharmeazor.parsers.pharmnet import build, build_from_raw

parser = argparse.ArgumentParser(description="Collecte Pharm'Net")
parser.add_argument(
    "--limit", type=int, default=None,
    help="nombre maximum de fiches produits (défaut : tout le catalogue)",
)
parser.add_argument(
    "--from-raw", metavar="STAMP", default=None,
    help="retraiter un snapshot existant, ex. 20261113_235452",
)
args = parser.parse_args()

if args.from_raw:
    build_from_raw(args.from_raw)
else:
    build(limit=args.limit)
