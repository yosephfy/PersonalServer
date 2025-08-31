from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(os.getenv("PERSONAL_SERVER_ROOT", Path(__file__).resolve().parent.parent))

DATA_DIR = ROOT

NOTES_DIR = DATA_DIR / "notes"
TRANSACTIONS_DIR = DATA_DIR / "transactions"
SCRAPES_DIR = DATA_DIR / "scrapes"
WEIGHTS_DIR = DATA_DIR / "weights"

NOTES_CSV = NOTES_DIR / "notes.csv"
TRANSACTIONS_CSV = TRANSACTIONS_DIR / "transactions.csv"
SCRAPES_CSV = SCRAPES_DIR / "scrapes.csv"
WEIGHTS_CSV = WEIGHTS_DIR / "weights.csv"

DEFAULT_HOST = os.getenv("PERSONAL_SERVER_HOST", "127.0.0.1")
DEFAULT_PORT = int(os.getenv("PERSONAL_SERVER_PORT", "8080"))
