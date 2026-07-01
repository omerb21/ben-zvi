from __future__ import annotations

import secrets
from pathlib import Path
from typing import Tuple

from sqlalchemy.orm import Session

from app.models import Client, ClientSignatureRequest
from app.services import justification_b1 as justification_b1_service
from app.services import justification_packet_generate as justification_packet_generate_service
from app.services import justification_packet_trim as justification_packet_trim_service
from app.utils.db import commit_and_refresh as _commit_and_refresh
from app.utils.fs import try_read_bytes as _try_read_bytes


def _get_packet_paths_for_client(client: Client):
    export_dir = justification_b1_service._get_client_export_dir(client)
    base_packet_path = export_dir / f"packet_{client.id}.pdf"
    edited_packet_path = export_dir / f"packet_{client.id}_edited.pdf"
    signed_packet_path = export_dir / f"packet_{client.id}_signed_client.pdf"
    return export_dir, base_packet_path, edited_packet_path, signed_packet_path


def _get_signature_request_or_raise(db: Session, token: str) -> ClientSignatureRequest:
    request = db.query(ClientSignatureRequest).filter(ClientSignatureRequest.token == token).first()
    if not request:
        raise ValueError("SIGNATURE_REQUEST_NOT_FOUND")
    return request


def _get_request_client_or_raise(db: Session, request: ClientSignatureRequest) -> Client:
    client = db.get(Client, request.client_id)
    if not client:
        raise ValueError("CLIENT_NOT_FOUND")
    return client


def create_packet_signature_request(db: Session, client_id: int) -> ClientSignatureRequest:
    client = db.get(Client, client_id)
    if not client:
        raise ValueError("CLIENT_NOT_FOUND")

    export_dir, base_packet_path, edited_packet_path, _ = _get_packet_paths_for_client(client)

    packet_pdf_data = None

    if edited_packet_path.is_file():
        if not base_packet_path.is_file():
            try:
                justification_packet_generate_service.generate_client_packet_pdf(
                    db,
                    client,
                    generate_missing=False,
                )
            except Exception:
                pass
        justification_packet_trim_service.refresh_edited_packet_from_base_if_possible(
            base_packet_path,
            edited_packet_path,
        )
        packet_path = edited_packet_path
        packet_pdf_data = _try_read_bytes(edited_packet_path)
    elif base_packet_path.is_file():
        packet_path = base_packet_path
        packet_pdf_data = _try_read_bytes(base_packet_path)
    else:
        raise ValueError("CLIENT_PACKET_PDF_NOT_FOUND")

    db.query(ClientSignatureRequest).filter(
        ClientSignatureRequest.client_id == client_id,
        ClientSignatureRequest.status == "pending",
    ).delete()

    token = secrets.token_urlsafe(32)

    request = ClientSignatureRequest(
        client_id=client.id,
        token=token,
        packet_filename=packet_path.name,
        signed_packet_filename=None,
        status="pending",
        packet_pdf_data=packet_pdf_data,
    )
    db.add(request)
    _commit_and_refresh(db, request)
    return request


def create_external_document_signature_request(
    db: Session,
    client_id: int,
    pdf_bytes: bytes,
) -> ClientSignatureRequest:
    client = db.get(Client, client_id)
    if not client:
        raise ValueError("CLIENT_NOT_FOUND")

    db.query(ClientSignatureRequest).filter(
        ClientSignatureRequest.client_id == client_id,
        ClientSignatureRequest.status == "pending",
    ).delete()

    request = ClientSignatureRequest(
        client_id=client.id,
        token=secrets.token_urlsafe(32),
        packet_filename=f"external_document_{client.id}.pdf",
        signed_packet_filename=None,
        status="pending",
        packet_pdf_data=pdf_bytes,
    )
    db.add(request)
    _commit_and_refresh(db, request)
    return request


def get_active_request_for_token(db: Session, token: str) -> Tuple[ClientSignatureRequest, Client]:
    request = _get_signature_request_or_raise(db, token)
    if request.status != "pending":
        raise ValueError("SIGNATURE_REQUEST_ALREADY_COMPLETED")

    client = _get_request_client_or_raise(db, request)

    return request, client


def get_request_and_client_for_token(db: Session, token: str) -> Tuple[ClientSignatureRequest, Client]:
    request = _get_signature_request_or_raise(db, token)
    client = _get_request_client_or_raise(db, request)

    return request, client


def get_latest_request_for_client(
    db: Session,
    client_id: int,
) -> ClientSignatureRequest | None:
    return (
        db.query(ClientSignatureRequest)
        .filter(ClientSignatureRequest.client_id == client_id)
        .order_by(ClientSignatureRequest.created_at.desc(), ClientSignatureRequest.id.desc())
        .first()
    )
