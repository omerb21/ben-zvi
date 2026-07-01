from __future__ import annotations

import io
import logging
import time
from typing import Tuple

from pypdf import PdfReader as PyPdfReader
from sqlalchemy.orm import Session

from app.models import Client, ClientSignatureRequest
from app.services import justification_advice as justification_advice_service
from app.services import justification_forms as justification_forms_service
from app.services import justification_packet as justification_packet_service
from app.services import justification_signing_complete_helpers as _helpers
from app.services import justification_signing_overlay as _signing_overlay
from app.services import justification_signing_requests as _signing_requests
from app.utils.db import commit_and_refresh as _commit_and_refresh
from app.utils.fs import try_read_bytes as _try_read_bytes
from app.utils.fs import try_write_bytes as _try_write_bytes


logger = logging.getLogger(__name__)


def _try_generate_base_packet(db: Session, client: Client) -> None:
    return _helpers._try_generate_base_packet(db, client)


def _try_persist_client_signature_png(export_dir, signature_data_url: str) -> None:
    return _helpers._try_persist_client_signature_png(export_dir, signature_data_url)


def _try_regenerate_advice_pdf(db: Session, client: Client) -> None:
    return _helpers._try_regenerate_advice_pdf(db, client)


def _select_packet_path_for_signature(
    export_dir,
    base_packet_path,
    edited_packet_path,
    request: ClientSignatureRequest,
    use_db_packet_bytes: bool,
):
    return _helpers._select_packet_path_for_signature(
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
    return _helpers._try_regenerate_base_packet_if_needed(
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
    return _helpers._read_packet_bytes_or_raise(request, use_db_packet_bytes, packet_path)


def _try_get_reference_pdf_bytes(
    db: Session,
    client: Client,
    request: ClientSignatureRequest,
    base_packet_path,
    is_edited_packet: bool,
) -> bytes | None:
    return _helpers._try_get_reference_pdf_bytes(
        db,
        client,
        request,
        base_packet_path,
        is_edited_packet,
    )


def complete_packet_signature(db: Session, token: str, signature_data_url: str) -> ClientSignatureRequest:
    return _helpers.complete_packet_signature(db, token, signature_data_url)
