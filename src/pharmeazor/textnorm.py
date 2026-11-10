import re, unicodedata

def norm(s) -> str:
    """lowercase, no accents, only [a-z0-9] separated by single spaces."""
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()
