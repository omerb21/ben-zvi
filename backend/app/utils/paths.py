from __future__ import annotations

import os
from pathlib import Path


def get_app_base_dir() -> Path:
    env_base_dir = os.getenv("APP_BASE_DIR")
    if env_base_dir:
        return Path(env_base_dir).resolve()
    return Path(__file__).resolve().parent.parent


def get_backend_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent
