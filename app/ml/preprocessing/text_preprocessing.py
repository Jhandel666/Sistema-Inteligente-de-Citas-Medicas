import re


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-záéíóúñ0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text
