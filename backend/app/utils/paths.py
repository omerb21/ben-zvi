from __future__ import annotations

from pathlib import Path


def get_app_base_dir() -> Path:
    return Path(__file__).resolve().parent.parent


def get_backend_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent
