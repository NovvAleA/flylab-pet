"""Persistent, extensible settings shared by the fly and its controller."""

from __future__ import annotations

import json
from pathlib import Path


CONFIG_DIR = Path.home() / ".config" / "flylab"
CONFIG_FILE = CONFIG_DIR / "desktop-fly.json"
DEFAULTS = {
    "version": 1,
    "appearance": "fly",
    "speed_multiplier": 1.0,
    "left_item": "coffee",
    "right_item": "cigarette",
}


def load_settings() -> dict:
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        return {**DEFAULTS, **data} if isinstance(data, dict) else DEFAULTS.copy()
    except (OSError, ValueError):
        return DEFAULTS.copy()


def save_settings(values: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    merged = {**load_settings(), **values}
    temporary = CONFIG_FILE.with_suffix(".tmp")
    temporary.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(CONFIG_FILE)
