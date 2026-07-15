from __future__ import annotations

import io
import logging
import time

from pypdf import PdfReader as PyPdfReader
from sqlalchemy.orm import Session

from app.models import Client, ClientSignatureRequest
from app.services import crm_notes
from app.services import justification_advice as justification_advice_service
from app.services import justification_forms as justification_forms_service
from app.services import justification_packet as justification_packet_service
from app.services import justification_signing_overlay as _signing_overlay
from app.services import justification_signing_requests as _signing_requests
from app.utils.db import commit_and_refresh as _commit_and_refresh
from app.utils.fs import try_read_bytes as _try_read_bytes
from app.utils.fs import try_write_bytes as _try_write_bytes


logger = logging.getLogger(__name__)


def _try_generate_base_packet(db: Session, client: Client) -> None:
    try:
        justification_packet_service.generate_client_packet_pdf(db, client, generate_missing=False)
    except Exception:
        pass


def _try_persist_client_signature_png(export_dir, signature_data_url: str) -> None:
    try:
        sig_bytes = justification_forms_service._decode_data_url(signature_data_url)
        if sig_bytes:
            client_sig_path = export_dir / "client_signature.png"
            _try_write_bytes(client_sig_path, sig_bytes)
    except Exception:
        pass


def _try_regenerate_advice_pdf(db: Session, client: Client) -> None:
    try:
        justification_advice_service.save_advice_pdf_for_client(db, client)
    except Exception:
        pass


def _select_packet_path_for_signature(
    export_dir,
    base_packet_path,
    edited_packet_path,
    request: ClientSignatureRequest,
    use_db_packet_bytes: bool,
):
    if request.packet_filename:
        return export_dir / request.packet_filename
    if edited_packet_path.is_file():
        return edited_packet_path
    return base_packet_path


def _try_regenerate_base_packet_if_needed(
    db: Session,
    client: Client,
    use_db_packet_bytes: bool,
    packet_path,
    base_packet_path,
) -> None:
    if use_db_packet_bytes or packet_path != base_packet_path or packet_path.is_file():
        return

    _try_generate_base_packet(db, client)


def _read_packet_bytes_or_raise(
    request: ClientSignatureRequest,
    use_db_packet_bytes: bool,
    packet_path,
) -> bytes:
    if use_db_packet_bytes:
        return request.packet_pdf_data
    if packet_path.is_file():
        return packet_path.read_bytes()
    raise ValueError("CLIENT_PACKET_PDF_NOT_FOUND")


def _try_get_reference_pdf_bytes(
    db: Session,
    client: Client,
    request: ClientSignatureRequest,
    base_packet_path,
    is_edited_packet: bool,
) -> bytes | None:
    if not is_edited_packet:
        return None

    if getattr(request, "reference_pdf_data", None):
        return request.reference_pdf_data

    if not base_packet_path.is_file():
        _try_generate_base_packet(db, client)

    data = _try_read_bytes(base_packet_path)
    if data is not None:
        return data

    return None


def _packet_starts_with_advice(source_bytes: bytes, advice_bytes: bytes) -> bool:
    try:
        source_reader = PyPdfReader(io.BytesIO(source_bytes))
        advice_reader = PyPdfReader(io.BytesIO(advice_bytes))
        if not advice_reader.pages or len(source_reader.pages) < len(advice_reader.pages):
            return False

        for page_index, advice_page in enumerate(advice_reader.pages):
            source_text = "".join((source_reader.pages[page_index].extract_text() or "").split())
            advice_text = "".join((advice_page.extract_text() or "").split())
            if source_text != advice_text:
                return False
        return True
    except Exception:
        return False


def complete_packet_signature(db: Session, token: str, signature_data_url: str) -> ClientSignatureRequest:
    start_time = time.time()
    request = _signing_requests._get_signature_request_or_raise(db, token)
    if request.status != "pending" or request.signed_at is not None:
        raise ValueError("SIGNATURE_REQUEST_ALREADY_COMPLETED")

    client = _signing_requests._get_request_client_or_raise(db, request)

    export_dir, base_packet_path, edited_packet_path, signed_packet_path = _signing_requests._get_packet_paths_for_client(client)

    _try_persist_client_signature_png(export_dir, signature_data_url)

    use_db_packet_bytes = bool(getattr(request, "packet_pdf_data", None))

    packet_path = _select_packet_path_for_signature(
        export_dir,
        base_packet_path,
        edited_packet_path,
        request,
        use_db_packet_bytes,
    )

    _try_regenerate_base_packet_if_needed(
        db,
        client,
        use_db_packet_bytes,
        packet_path,
        base_packet_path,
    )

    source_bytes = _read_packet_bytes_or_raise(
        request,
        use_db_packet_bytes,
        packet_path,
    )

    is_edited_packet = packet_path.name.endswith("_edited.pdf")

    reference_pdf_bytes = _try_get_reference_pdf_bytes(
        db,
        client,
        request,
        base_packet_path,
        is_edited_packet,
    )

    advice_path = justification_packet_service._get_advice_pdf_path(client)
    if advice_path.is_file():
        try:
            advice_bytes = _try_read_bytes(advice_path)
            if advice_bytes is None:
                raise ValueError("ADVICE_PDF_READ_FAILED")
            advice_reader = PyPdfReader(io.BytesIO(advice_bytes))
            advice_page_count = 0

            if is_edited_packet:
                advice_page_count = len(advice_reader.pages)
                if reference_pdf_bytes:
                    source_reader = PyPdfReader(io.BytesIO(source_bytes))
                    ref_reader = PyPdfReader(io.BytesIO(reference_pdf_bytes))
                    ref_forms_count = len(ref_reader.pages) - len(advice_reader.pages)
                    # Forms are at the end, so edited advice pages = total pages - forms pages.
                    advice_page_count = max(0, len(source_reader.pages) - ref_forms_count)
            elif _packet_starts_with_advice(source_bytes, advice_bytes):
                advice_page_count = len(advice_reader.pages)

            if advice_page_count > 0:
                source_bytes = _signing_overlay._add_signature_overlay_to_advice_pages(
                    source_bytes,
                    signature_data_url,
                    advice_page_count,
                )
        except Exception as e:
            logger.error(f"Failed to add advice signature overlay: {e}")

    signed_bytes = justification_forms_service.apply_signature_to_sig_fields(
        source_bytes,
        signature_image_data=signature_data_url,
        reference_pdf_bytes=reference_pdf_bytes,
    )

    flattened_bytes = justification_forms_service.flatten_form_fields(signed_bytes)
    if (
        is_edited_packet
        and reference_pdf_bytes
        and justification_forms_service.has_missing_signature_draws(flattened_bytes, reference_pdf_bytes)
    ):
        completed_signed_bytes = justification_forms_service.apply_signature_to_sig_fields(
            flattened_bytes,
            signature_image_data=signature_data_url,
            reference_pdf_bytes=reference_pdf_bytes,
        )
        flattened_bytes = justification_forms_service.flatten_form_fields(completed_signed_bytes)

    # The signed PDF is persisted in the database below and is therefore not
    # allowed to depend on the instance's local filesystem.  Hosted instances
    # can have ephemeral or temporarily unwritable storage; a direct write here
    # used to abort the request before status/signed_at were committed, leaving
    # a successfully submitted signing link stuck in ``pending``.
    _try_write_bytes(signed_packet_path, flattened_bytes)

    from datetime import datetime, timezone

    request.signed_packet_filename = signed_packet_path.name
    request.status = "signed"
    request.signed_at = datetime.now(timezone.utc)
    # Also save the signed PDF to database to prevent loss in ephemeral storage
    request.packet_pdf_data = flattened_bytes

    _commit_and_refresh(db, request)
    try:
        _create_signature_notification(db, client, request)
    except Exception:
        logger.exception("Failed to create CRM signature notification for client_id=%s", client.id)
    elapsed = time.time() - start_time
    logger.info(f"[PDF-TIMING] Signing completed in {elapsed:.2f}s for client_id={client.id}")
    return request


def _create_signature_notification(
    db: Session,
    client: Client,
    request: ClientSignatureRequest,
) -> None:
    signed_date = request.signed_at.date().isoformat() if request.signed_at else None
    crm_notes.create_client_note(
        db,
        client.id,
        "הלקוח חתם על חבילת המסמכים",
        signed_date,
    )
