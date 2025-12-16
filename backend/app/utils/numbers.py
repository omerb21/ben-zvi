from __future__ import annotations

from typing import Any


def coerce_amount(value: Any) -> float:
    return float(value or 0.0)
