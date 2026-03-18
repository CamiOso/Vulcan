from __future__ import annotations

import json
from pathlib import Path

from .module_catalog import MODULES


DEFAULT_CONFIG = {
    "setup_completed": False,
    "data_folder": "",
    "ui_resolution": "1280x800",
    "ui_style": "Claro",
    "units": "metros",
    "enabled_modules": [m["key"] for m in MODULES],
}

CONFIG_DIR = Path.home() / ".proyectovulcano"
CONFIG_PATH = CONFIG_DIR / "config.json"


def load_user_config() -> dict:
    """Load persisted app configuration from user home."""
    config = dict(DEFAULT_CONFIG)
    if not CONFIG_PATH.exists():
        return config

    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            config.update(data)
    except json.JSONDecodeError:
        return config

    return config


def save_user_config(config: dict) -> None:
    """Persist app configuration to user home."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
