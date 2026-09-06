import re
import unicodedata
from datetime import UTC, datetime


def slug_generator(v: str) -> str:
    text = v + "_" + datetime.now(UTC).isoformat()
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s\-]", "", text).strip().lower()
    text = re.sub(r"[\s\-]+", "_", text)
    return text
