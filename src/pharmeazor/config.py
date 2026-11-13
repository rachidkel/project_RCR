from pathlib import Path
import os
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

DATA = ROOT / "data"
RAW = DATA / "raw"
INTERIM = DATA / "interim"
PROCESSED = DATA / "processed"
DB_PATH = ROOT / "db" / "pharmeazor.sqlite"

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "openai/gpt-oss-120b"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
REQUEST_DELAY_S = 3
REQUEST_TIMEOUT_S = 60

# Pharm'Net — API REST publique Supabase utilisée par le site pharmnet-dz.com.
# La clé « publishable » est publique (elle est incluse dans le HTML du site) ;
# elle ne donne accès qu'aux données publiques via les règles RLS.
PHARMNET_API_URL = os.getenv(
    "PHARMNET_API_URL", "https://yqhaaitrqqpvtcnomljm.supabase.co/rest/v1"
)
PHARMNET_API_KEY = os.getenv(
    "PHARMNET_API_KEY", "sb_publishable_kCraKHzowqNyXwv9jfC81w_BQI7dIpK"
)