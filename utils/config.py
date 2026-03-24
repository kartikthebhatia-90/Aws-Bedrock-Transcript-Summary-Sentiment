from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Project root = parent of the utils folder
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load environment variables from .env at project root
load_dotenv(PROJECT_ROOT / ".env")

# -------------------------
# Directory paths
# -------------------------
APP_DIR = PROJECT_ROOT / "app"
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
DB_DIR = DATA_DIR / "db"

LLM_DIR = PROJECT_ROOT / "llm"
PIPELINE_DIR = PROJECT_ROOT / "pipeline"
STORAGE_DIR = PROJECT_ROOT / "storage"
UTILS_DIR = PROJECT_ROOT / "utils"

# -------------------------
# File paths
# -------------------------
ENV_FILE = PROJECT_ROOT / ".env"
README_FILE = PROJECT_ROOT / "README.md"
REQUIREMENTS_FILE = PROJECT_ROOT / "requirements.txt"

SQLITE_DB_PATH = DB_DIR / "transcript_analysis.db"
DEFAULT_INPUT_DATASET = RAW_DATA_DIR / "Chat Dataset.xlsx"

# -------------------------
# AWS / Bedrock config
# -------------------------
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-2")
AWS_BEARER_TOKEN_BEDROCK = os.getenv("AWS_BEARER_TOKEN_BEDROCK", "").strip()
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "").strip()

# -------------------------
# App-level constants
# -------------------------
APP_TITLE = "Aws Bedrock Transcript Summary Sentiment"
APP_DESCRIPTION = (
    "Demo app to convert informal chat transcripts into structured "
    "business-ready summaries, sentiment, priority, and actions."
)

SUPPORTED_SENTIMENTS = {"Positive", "Neutral", "Negative"}
SUPPORTED_PRIORITIES = {"Low", "Medium", "High"}
SUPPORTED_STATUSES = {"Resolved", "Pending", "Escalated"}

OUTPUT_COLUMNS = [
    "raw_chat",
    "predicted_topic",
    "sentiment",
    "priority",
    "formal_summary",
    "recommended_action",
    "status",
]

# -------------------------
# Helper functions
# -------------------------
def ensure_directories() -> None:
    """Create required project directories if they do not already exist."""
    required_dirs = [
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        DB_DIR,
    ]
    for directory in required_dirs:
        directory.mkdir(parents=True, exist_ok=True)


def validate_env() -> list[str]:
    """
    Returns a list of missing required environment variables.
    Keeps validation lightweight for demo purposes.
    """
    missing = []

    if not AWS_REGION:
        missing.append("AWS_REGION")

    if not BEDROCK_MODEL_ID:
        missing.append("BEDROCK_MODEL_ID")

    return missing