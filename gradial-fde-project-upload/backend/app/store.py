"""Tiny JSON-file backed store for demo purposes.

In a real Gradial-style deployment this would be Postgres, but for a
portfolio project a file store keeps the whole thing runnable with zero
infrastructure while still surviving a server restart.
"""
import json
import os
import threading
from typing import Dict, List, Optional

from .models import CampaignRequest

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DATA_FILE = os.path.join(DATA_DIR, "db.json")

_lock = threading.Lock()


def _ensure_file():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)


def _read_all() -> Dict[str, dict]:
    _ensure_file()
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def _write_all(data: Dict[str, dict]):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


def save(req: CampaignRequest):
    with _lock:
        data = _read_all()
        data[req.id] = json.loads(req.model_dump_json())
        _write_all(data)


def get(request_id: str) -> Optional[CampaignRequest]:
    with _lock:
        data = _read_all()
    raw = data.get(request_id)
    return CampaignRequest(**raw) if raw else None


def list_all() -> List[CampaignRequest]:
    with _lock:
        data = _read_all()
    items = [CampaignRequest(**v) for v in data.values()]
    items.sort(key=lambda r: r.created_at, reverse=True)
    return items
