from __future__ import annotations

import logging
from typing import Tuple

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session

from app.models import Client, ClientSignatureRequest
from app.services import justification_signing_complete as _signing_complete
from app.services import justification_signing_overlay as _signing_overlay
from app.services import justification_signing_requests as _signing_requests
from app.utils.fs import try_read_bytes as _try_read_bytes


def _try_generate_base_packet(db: Session, client: Client) -> None:
    return _signing_complete._try_generate_base_packet(db, client)


def _try_persist_client_signature_png(export_dir, signature_data_url: str) -> None:
    return _signing_complete._try_persist_client_signature_png(export_dir, signature_data_url)


def _try_regenerate_advice_pdf(db: Session, client: Client) -> None:
    return _signing_complete._try_regenerate_advice_pdf(db, client)


def _select_packet_path_for_signature(
    export_dir,
    base_packet_path,
    edited_packet_path,
    request: ClientSignatureRequest,
    use_db_packet_bytes: bool,
):
    return _signing_complete._select_packet_path_for_signature(
        export_dir,
        base_packet_path,
        edited_packet_path,
        request,
        use_db_packet_bytes,
    )


def _try_regenerate_base_packet_if_needed(
    db: Session,
    client: Client,
    use_db_packet_bytes: bool,
    packet_path,
    base_packet_path,
) -> None:
    return _signing_complete._try_regenerate_base_packet_if_needed(
        db,
        client,
        use_db_packet_bytes,
        packet_path,
        base_packet_path,
    )


def _read_packet_bytes_or_raise(
    request: ClientSignatureRequest,
    use_db_packet_bytes: bool,
    packet_path,
) -> bytes:
    return _signing_complete._read_packet_bytes_or_raise(
        request,
        use_db_packet_bytes,
        packet_path,
    )


def _try_get_reference_pdf_bytes(
    db: Session,
    client: Client,
    base_packet_path,
    is_edited_packet: bool,
) -> bytes | None:
    return _signing_complete._try_get_reference_pdf_bytes(
        db,
        client,
        base_packet_path,
        is_edited_packet,
    )


def _get_fallback_signature_positions(advice_page_count: int):
    """
    מחזיר מיקומי חתימה קבועים לדפי ההנמקה.
    גישה מהירה במקום pdfplumber - חוסכת זמן עיבוד משמעותי.
    """
    return _signing_overlay._get_fallback_signature_positions(advice_page_count)


def _add_signature_overlay_to_advice_pages(
    packet_bytes: bytes,
    signature_data_url: str,
    advice_page_count: int,
) -> bytes:
    """
    מוסיף overlay של חתימת לקוח לדפי ההנמקה בחבילה הערוכה.
    מחפש את המיקום של "חתימת הלקוח" בטקסט של כל עמוד ומציב את החתימה מתחת.
    """
    return _signing_overlay._add_signature_overlay_to_advice_pages(
        packet_bytes,
        signature_data_url,
        advice_page_count,
    )


def _get_packet_paths_for_client(client: Client):
    return _signing_requests._get_packet_paths_for_client(client)


def _get_signature_request_or_raise(db: Session, token: str) -> ClientSignatureRequest:
    return _signing_requests._get_signature_request_or_raise(db, token)


def _get_request_client_or_raise(db: Session, request: ClientSignatureRequest) -> Client:
    return _signing_requests._get_request_client_or_raise(db, request)


def create_packet_signature_request(db: Session, client_id: int) -> ClientSignatureRequest:
    return _signing_requests.create_packet_signature_request(db, client_id)


def get_active_request_for_token(db: Session, token: str) -> Tuple[ClientSignatureRequest, Client]:
    return _signing_requests.get_active_request_for_token(db, token)


def get_request_and_client_for_token(db: Session, token: str) -> Tuple[ClientSignatureRequest, Client]:
    """Fetch a signature request and its client by token without enforcing status.

    Used when we want to access resources (כמו המסמך החתום) גם אחרי שהקישור
    החד-פעמי כבר נוצל והסטטוס של הבקשה איננו "pending".
    """

    return _signing_requests.get_request_and_client_for_token(db, token)


def get_latest_request_for_client(db: Session, client_id: int) -> ClientSignatureRequest | None:
    return _signing_requests.get_latest_request_for_client(db, client_id)


def complete_packet_signature(db: Session, token: str, signature_data_url: str) -> ClientSignatureRequest:
    return _signing_complete.complete_packet_signature(db, token, signature_data_url)
