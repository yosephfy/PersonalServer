from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from . import config
from .utils import append_csv_row, ensure_dir, slugify, utc_now_str, write_text, short_id


@dataclass
class NoteRecord:
    id: str
    title: str
    filename: str
    created_at: str
    tags: str = ""


def save_note(title: str, content: str, tags: Optional[str] = None) -> NoteRecord:
    ensure_dir(config.NOTES_DIR)
    ts = utc_now_str()
    sid = short_id("note-")
    base = f"{ts}-{slugify(title) or 'note'}"
    filename = f"{base}.md"
    path = config.NOTES_DIR / filename
    frontmatter = f"---\ntitle: {title}\ncreated_at: {ts}\ntags: {tags or ''}\n---\n\n"
    write_text(path, frontmatter + content)

    rec = NoteRecord(id=sid, title=title, filename=filename, created_at=ts, tags=tags or "")
    append_csv_row(
        config.NOTES_CSV,
        fieldnames=["id", "title", "filename", "created_at", "tags"],
        row=rec.__dict__,
    )
    return rec


@dataclass
class TransactionRecord:
    id: str
    date: str
    amount: str
    merchant: str
    category: str
    account: str
    notes: str
    raw_json: str


def save_transaction(payload: Dict) -> TransactionRecord:
    ensure_dir(config.TRANSACTIONS_DIR)
    # Normalize keys with sensible defaults
    date = str(payload.get("date") or payload.get("timestamp") or utc_now_str())
    amount = str(payload.get("amount") or payload.get("value") or "")
    merchant = str(payload.get("merchant") or payload.get("payee") or "")
    category = str(payload.get("category") or payload.get("type") or "")
    account = str(payload.get("account") or payload.get("source") or "")
    notes = str(payload.get("notes") or payload.get("memo") or "")

    rec = TransactionRecord(
        id=short_id("txn-"),
        date=date,
        amount=amount,
        merchant=merchant,
        category=category,
        account=account,
        notes=notes,
        raw_json=payload,
    )
    append_csv_row(
        config.TRANSACTIONS_CSV,
        fieldnames=["id", "date", "amount", "merchant", "category", "account", "notes", "raw_json"],
        row=rec.__dict__,
    )
    return rec


@dataclass
class ScrapeRecord:
    id: str
    url: str
    fetched_at: str
    filename_html: str
    filename_txt: str
    title: str


def save_scrape(url: str, html: str, text: str, title: str) -> ScrapeRecord:
    ensure_dir(config.SCRAPES_DIR)
    ts = utc_now_str()
    sid = short_id("scrape-")
    base = f"{ts}-{slugify(title or 'page')}"
    html_name = f"{base}.html"
    txt_name = f"{base}.txt"
    write_text(config.SCRAPES_DIR / html_name, html)
    write_text(config.SCRAPES_DIR / txt_name, text)

    rec = ScrapeRecord(
        id=sid,
        url=url,
        fetched_at=ts,
        filename_html=html_name,
        filename_txt=txt_name,
        title=title,
    )
    append_csv_row(
        config.SCRAPES_CSV,
        fieldnames=["id", "url", "fetched_at", "filename_html", "filename_txt", "title"],
        row=rec.__dict__,
    )
    return rec


@dataclass
class WeightRecord:
    id: str
    date: str
    weight_kg: str
    weight_lb: str
    body_fat_pct: str
    source: str
    notes: str
    raw_json: str


def _to_float(value) -> Optional[float]:
    try:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        s = str(value).strip()
        # extract first number (supports 82.5kg or 180 lb)
        import re

        m = re.search(r"[-+]?[0-9]*\.?[0-9]+", s)
        if m:
            return float(m.group(0))
    except Exception:
        return None
    return None


def save_weight(payload: Dict) -> WeightRecord:
    ensure_dir(config.WEIGHTS_DIR)

    date = str(payload.get("date") or payload.get("timestamp") or utc_now_str())
    source = str(payload.get("source") or payload.get("device") or "")
    notes = str(payload.get("notes") or payload.get("memo") or "")

    # Accept flexible inputs: weight, weight_kg, weight_lb, kg, lb, unit
    unit = str(payload.get("unit") or "").lower().strip()
    w_val = (
        payload.get("weight")
        or payload.get("weight_kg")
        or payload.get("kg")
        or payload.get("weight_lb")
        or payload.get("lb")
    )

    # Determine base unit if embedded in string like "180 lb"
    base = str(w_val or "").lower()
    if not unit:
        if "lb" in base or "pound" in base:
            unit = "lb"
        elif "kg" in base:
            unit = "kg"

    val = _to_float(w_val)
    kg = lb = None
    if val is not None:
        if unit == "lb" or unit == "lbs":
            lb = val
            kg = lb / 2.2046226218
        else:
            # default to kg
            kg = val
            lb = kg * 2.2046226218

    # Body fat percentage can be body_fat, bodyFat, bf
    bf_val = payload.get("body_fat_pct") or payload.get("body_fat") or payload.get("bodyFat") or payload.get("bf")
    bf = _to_float(bf_val)

    rec = WeightRecord(
        id=short_id("wt-"),
        date=date,
        weight_kg=f"{kg:.3f}" if kg is not None else "",
        weight_lb=f"{lb:.3f}" if lb is not None else "",
        body_fat_pct=f"{bf:.2f}" if bf is not None else "",
        source=source,
        notes=notes,
        raw_json=payload,
    )

    append_csv_row(
        config.WEIGHTS_CSV,
        fieldnames=[
            "id",
            "date",
            "weight_kg",
            "weight_lb",
            "body_fat_pct",
            "source",
            "notes",
            "raw_json",
        ],
        row=rec.__dict__,
    )

    return rec
