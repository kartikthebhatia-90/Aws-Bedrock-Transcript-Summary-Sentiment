from __future__ import annotations

import re


def normalize_whitespace(text: str) -> str:
    """
    Collapse repeated whitespace, tabs, and newlines into clean readable spacing.
    """
    text = text.replace("\r", "\n")
    text = re.sub(r"\n+", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def clean_transcript(text: str) -> str:
    """
    Basic cleaning for transcript input before sending to the LLM.
    Keeps the pipeline intentionally lightweight for demo purposes.
    """
    if text is None:
        raise ValueError("Transcript cannot be None.")

    if not isinstance(text, str):
        text = str(text)

    cleaned = normalize_whitespace(text)

    if not cleaned:
        raise ValueError("Transcript is empty after cleaning.")

    return cleaned


def preprocess_transcript(text: str) -> str:
    """
    Main preprocessing entry point used by the pipeline.
    """
    return clean_transcript(text)