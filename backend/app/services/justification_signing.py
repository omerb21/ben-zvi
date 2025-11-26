from __future__ import annotations

import secrets
from typing import Tuple

from sqlalchemy.orm import Session

from app.models import Client, ClientSignatureRequest
from app.services import justification_b1 as justification_b1_service
from app.services import justification_forms as justification_forms_service
from app.services import justification_packet as justification_packet_service
from app.services import justification_advice as justification_advice_service


def _get_packet_paths_for_client(client: Client):
    export_dir = justification_b1_service._get_client_export_dir(client)
    base_packet_path = export_dir / f"packet_{client.id}.pdf"
    edited_packet_path = export_dir / f"packet_{client.id}_edited.pdf"
    signed_packet_path = export_dir / f"packet_{client.id}_signed_client.pdf"
    return export_dir, base_packet_path, edited_packet_path, signed_packet_path


def create_packet_signature_request(db: Session, client_id: int) -> ClientSignatureRequest:
    client = db.get(Client, client_id)
    if not client:
        raise ValueError("CLIENT_NOT_FOUND")

    export_dir, base_packet_path, edited_packet_path, _ = _get_packet_paths_for_client(client)

    if edited_packet_path.is_file():
        packet_path = edited_packet_path
    elif base_packet_path.is_file():
        packet_path = base_packet_path
    else:
        raise ValueError("CLIENT_PACKET_PDF_NOT_FOUND")

    token = secrets.token_urlsafe(32)

    request = ClientSignatureRequest(
        client_id=client.id,
        token=token,
        packet_filename=packet_path.name,
        status="pending",
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


def get_active_request_for_token(db: Session, token: str) -> Tuple[ClientSignatureRequest, Client]:
    request = db.query(ClientSignatureRequest).filter(ClientSignatureRequest.token == token).first()
    if not request:
        raise ValueError("SIGNATURE_REQUEST_NOT_FOUND")
    if request.status != "pending":
        raise ValueError("SIGNATURE_REQUEST_ALREADY_COMPLETED")

    client = db.get(Client, request.client_id)
    if not client:
        raise ValueError("CLIENT_NOT_FOUND")

    return request, client


def complete_packet_signature(db: Session, token: str, signature_data_url: str) -> ClientSignatureRequest:
    request = db.query(ClientSignatureRequest).filter(ClientSignatureRequest.token == token).first()
    if not request:
        raise ValueError("SIGNATURE_REQUEST_NOT_FOUND")
    if request.status != "pending" or request.signed_at is not None:
        raise ValueError("SIGNATURE_REQUEST_ALREADY_COMPLETED")

    client = db.get(Client, request.client_id)
    if not client:
        raise ValueError("CLIENT_NOT_FOUND")

    export_dir, base_packet_path, edited_packet_path, signed_packet_path = _get_packet_paths_for_client(client)

    # First, persist the client's drawn signature as a PNG in the
    # export directory so that other documents (e.g. the advice PDF)
    # can embed it visually.
    try:
        sig_bytes = justification_forms_service._decode_data_url(signature_data_url)
        if sig_bytes:
            client_sig_path = export_dir / "client_signature.png"
            client_sig_path.write_bytes(sig_bytes)
    except Exception:
        pass

    # Next, (re)generate the advice PDF so that it can include the
    # client's signature image at the designated locations. Failures
    # here do not affect the main signing flow.
    try:
        justification_advice_service.save_advice_pdf_for_client(db, client)
    except Exception:
        pass

    # Determine which packet file we are signing.
    if request.packet_filename:
        packet_path = export_dir / request.packet_filename
    elif edited_packet_path.is_file():
        packet_path = edited_packet_path
    else:
        packet_path = base_packet_path

    # If we are signing the auto-generated base packet, rebuild it now
    # so that it reflects the latest advice/B1/kits, including the
    # newly signed advice PDF.
    if packet_path == base_packet_path:
        try:
            justification_packet_service.generate_client_packet_pdf(db, client, generate_missing=True)
        except Exception:
            # If packet generation fails, we fall back to the existing
            # packet file (if any). A missing/invalid packet will still
            # be caught by the check below.
            pass

    if not packet_path.is_file():
        raise ValueError("CLIENT_PACKET_PDF_NOT_FOUND")

    source_bytes = packet_path.read_bytes()

    signed_bytes = justification_forms_service.apply_signature_to_sig_fields(
        source_bytes,
        signature_image_data=signature_data_url,
    )

    if not signed_packet_path.parent.exists():
        signed_packet_path.parent.mkdir(parents=True, exist_ok=True)

    signed_packet_path.write_bytes(signed_bytes)

    from datetime import datetime, timezone

    request.signed_packet_filename = signed_packet_path.name
    request.status = "signed"
    request.signed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(request)
    return request
