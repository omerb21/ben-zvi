from __future__ import annotations

from pathlib import Path


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def try_read_bytes(path: Path) -> bytes | None:
    try:
        if path.is_file():
            return path.read_bytes()
    except Exception:
        return None
    return None


def try_write_bytes(path: Path, data: bytes) -> None:
    try:
        path.write_bytes(data)
    except Exception:
        pass
