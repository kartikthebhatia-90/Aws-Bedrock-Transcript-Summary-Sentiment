from __future__ import annotations

from pathlib import Path

import pandas as pd

from utils.config import DEFAULT_INPUT_DATASET


def load_chat_dataset(file_path: str | Path | None = None) -> pd.DataFrame:
    path = Path(file_path) if file_path else DEFAULT_INPUT_DATASET

    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {path}")

    df = pd.read_excel(path)

    if df.empty:
        raise ValueError("Dataset is empty.")

    return df


def get_dataset_preview(file_path: str | Path | None = None, n: int = 10) -> pd.DataFrame:
    df = load_chat_dataset(file_path=file_path)
    return df.head(n)