from __future__ import annotations

from typing import Any

from app.models import Client


def build_fs_safe_name(base: str, fallback: str) -> str:
    text = (base or "").strip()
    if not text:
        text = fallback

    safe_chars: list[str] = []
    for ch in text:
        if ch.isalnum() or "\u0590" <= ch <= "\u05FF":
            safe_chars.append(ch)
        else:
            safe_chars.append("_")
    return "".join(safe_chars) or fallback


def _build_safe_name(base: str, fallback: str) -> str:
    """Create a filesystem- and header-safe name based on a display string.

    Rules (mirrors existing justification logic):
    - Keep only alphanumerics and Hebrew letters in the first pass; replace others with '_'.
    - Then, for HTTP headers (latin-1 / ASCII only), keep only ASCII alphanumerics and '-_';
      replace all other characters (including Hebrew) with '_'.
    - If everything is filtered out, fall back to the provided fallback.
    """

    text = (base or '').strip()
    if not text:
        text = fallback

    safe_name = build_fs_safe_name(text, fallback)

    # Second pass: HTTP header safe (ASCII only, alnum or -_).
    ascii_chars: list[str] = []
    for ch in safe_name:
        if ch.isascii() and (ch.isalnum() or ch in "-_"):
            ascii_chars.append(ch)
        else:
            ascii_chars.append("_")

    ascii_name = "".join(ascii_chars) or fallback
    return ascii_name


def get_client_ascii_safe_name(client: Client) -> str:
    """Return an ASCII-safe identifier for a client, suitable for filenames/headers.

    Preference order for the source text:
    - full_name
    - id_number
    - fallback "client_<id>".
    """

    display_name = client.full_name or client.id_number or f"client_{client.id}"
    fallback = f"client_{client.id}"
    return _build_safe_name(display_name, fallback)


def get_client_justification_filename(client: Client) -> str:
    """Standard filename for justification (advice) PDFs for a client."""

    safe_name = get_client_ascii_safe_name(client)
    return f"justification_{safe_name}.pdf"


def get_ascii_id_part(client: Any, fallback: str | None = None) -> str:
    fallback_value = fallback or str(getattr(client, "id", ""))
    id_part = getattr(client, "id_number", None) or fallback_value
    ascii_id_part = "".join(ch for ch in str(id_part) if ch.isascii() and ch.isalnum()) or fallback_value
    return ascii_id_part


def build_packet_ascii_filename(
    client: Any,
    fallback: str | None = None,
    *,
    signed: bool = False,
) -> str:
    ascii_id_part = get_ascii_id_part(client, fallback)
    suffix = "_signed_client" if signed else ""
    return f"packet_{ascii_id_part}{suffix}.pdf"
