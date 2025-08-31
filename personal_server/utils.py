from __future__ import annotations

import csv
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, Optional


ISO_FORMAT = "%Y-%m-%dT%H-%M-%S.%fZ"


def utc_now_str() -> str:
    return datetime.now(timezone.utc).strftime(ISO_FORMAT)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def slugify(text: str, max_length: int = 80) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9\-\_\s]+", "", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:max_length].strip("-") or "item"


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def append_csv_row(csv_path: Path, fieldnames: Iterable[str], row: Dict[str, object]) -> None:
    is_new = not csv_path.exists()
    ensure_dir(csv_path.parent)
    with csv_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(fieldnames))
        if is_new:
            writer.writeheader()
        writer.writerow({k: _normalize_value(row.get(k)) for k in writer.fieldnames})


def _normalize_value(v: object) -> str:
    if v is None:
        return ""
    if isinstance(v, (str, int, float)):
        return str(v)
    return json.dumps(v, ensure_ascii=False)


def short_id(prefix: str = "") -> str:
    # time-based unique id, with milliseconds
    ms = int(time.time() * 1000)
    return f"{prefix}{ms}"

