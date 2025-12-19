import os

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.justification import ClientSignatureSubmitPayload
from app.services import crm as crm_service
from app.services import justification_advice as justification_advice_service
from app.services import justification_b1 as justification_b1_service
from app.services import justification_packet as justification_packet_service
from app.services import justification_signing as justification_signing_service
from app.utils.db import commit_and_refresh as _commit_and_refresh
from app.utils.filepaths import get_ascii_id_part as _get_ascii_id_part
from app.utils.filepaths import build_packet_ascii_filename as _build_packet_ascii_filename
from app.utils.http_headers import build_inline_pdf_headers as _build_inline_pdf_headers
from app.utils.http_exceptions import raise_client_packet_pdf_not_found as _raise_client_packet_pdf_not_found
from app.utils.http_exceptions import raise_client_not_found as _raise_client_not_found
from app.utils.http_exceptions import raise_client_packet_generation_error as _raise_client_packet_generation_error
from app.utils.http_exceptions import raise_client_packet_generation_failed as _raise_client_packet_generation_failed
from app.utils.http_exceptions import raise_internal_server_error as _raise_internal_server_error
from app.utils.http_exceptions import raise_not_found as _raise_not_found
from app.routes.client_helpers import get_client_or_404 as _get_client_or_404


router = APIRouter(tags=["justification"])


def _raise_signing_link_not_found() -> None:
    _raise_not_found("Signing link not found")


def _build_signed_packet_url(client_id: int) -> str:
    return f"/api/v1/justification/clients/{client_id}/packet-signed-client.pdf"


def _inline_pdf_response(pdf_bytes: bytes, filename: str) -> Response:
    headers = _build_inline_pdf_headers(filename)
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


def _get_no_cache_headers() -> dict[str, str]:
    return {
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
    }


def _get_request_and_client_or_http_exc(db: Session, token: str, *, error_detail: str):
    try:
        return justification_signing_service.get_request_and_client_for_token(db, token)
    except ValueError as exc:
        message = str(exc)
        if message in {"SIGNATURE_REQUEST_NOT_FOUND", "CLIENT_NOT_FOUND"}:
            _raise_signing_link_not_found()
        _raise_internal_server_error(error_detail)


def _redirect_to_signed_packet_if_not_pending(request_obj, client):
    if request_obj.status == "pending":
        return None
    signed_packet_url = _build_signed_packet_url(client.id)
    return RedirectResponse(url=signed_packet_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


def _resolve_packet_path_for_request(client, packet_filename: str | None):
    export_dir = justification_b1_service._get_client_export_dir(client)
    resolved_filename = packet_filename or f"packet_{client.id}.pdf"
    resolved_path = export_dir / resolved_filename
    is_edited_packet = resolved_filename.endswith("_edited.pdf")
    return export_dir, resolved_filename, resolved_path, is_edited_packet


@router.post("/clients/{client_id}/packet-sign-request")
def create_client_packet_sign_request(
    client_id: int,
    db: Session = Depends(get_db),
):
    _get_client_or_404(db, client_id)

    try:
        request_obj = justification_signing_service.create_packet_signature_request(db, client_id)
    except ValueError as exc:
        message = str(exc)
        if message == "CLIENT_NOT_FOUND":
            _raise_client_not_found()
        if message == "CLIENT_PACKET_PDF_NOT_FOUND":
            # PDF missing (probably due to migration). Regenerate it and retry.
            try:
                justification_packet_service.generate_client_packet_pdf(
                    db, db.get(crm_service.Client, client_id), generate_missing=True
                )
                # Retry creating the request
                request_obj = justification_signing_service.create_packet_signature_request(db, client_id)
            except Exception:
                # If regeneration fails or second attempt fails, raise original error
                _raise_client_packet_pdf_not_found()
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create client packet signature request",
            )

    url_path = f"/api/v1/justification/client-sign/{request_obj.token}"

    external_base = os.environ.get("PUBLIC_BASE_URL") or ""
    external_base = external_base.rstrip("/")
    full_url = f"{external_base}{url_path}" if external_base else ""

    return {"token": request_obj.token, "url": url_path, "fullUrl": full_url}


@router.get("/client-sign/{token}")
def get_client_sign_page(
    token: str,
    db: Session = Depends(get_db),
):
    request_obj, client = _get_request_and_client_or_http_exc(
        db, token, error_detail="Failed to load signing page"
    )

    # אם הבקשה כבר לא במצב pending, נפנה ישירות למסמך החתום
    redirect = _redirect_to_signed_packet_if_not_pending(request_obj, client)
    if redirect is not None:
        return redirect

    client_name_parts = [client.first_name or "", client.last_name or ""]
    client_name = " ".join(part for part in client_name_parts if part).strip()
    if not client_name:
        client_name = client.full_name or client.id_number or "לקוח"

    env = justification_advice_service._get_templates_env()
    template = env.get_template("client_sign.html")

    packet_url = f"/api/v1/justification/client-sign/{token}/packet.pdf"
    submit_url = f"/api/v1/justification/client-sign/{token}/submit"
    signed_packet_url = _build_signed_packet_url(client.id)

    html = template.render(
        client_name=client_name,
        packet_url=packet_url,
        submit_url=submit_url,
        signed_packet_url=signed_packet_url,
    )
    # Prevent browser caching to ensure fresh content
    headers = _get_no_cache_headers()
    return Response(content=html, media_type="text/html; charset=utf-8", headers=headers)


@router.get("/client-sign/{token}/packet.pdf")
def download_client_packet_for_sign(
    token: str,
    db: Session = Depends(get_db),
):
    request_obj, client = _get_request_and_client_or_http_exc(
        db, token, error_detail="Failed to load client packet for sign"
    )

    # קישור ה-token ל-PDF ישמש רק לפני החתימה. לאחר החתימה נפנה למסמך החתום.
    redirect = _redirect_to_signed_packet_if_not_pending(request_obj, client)
    if redirect is not None:
        return redirect

    export_dir, packet_filename, packet_path, is_edited_packet = _resolve_packet_path_for_request(
        client,
        request_obj.packet_filename,
    )

    pdf_bytes: bytes | None = None

    if not packet_path.is_file():
        if request_obj.packet_pdf_data:
            pdf_bytes = request_obj.packet_pdf_data
        else:
            if is_edited_packet:
                raise HTTPException(
                    status_code=status.HTTP_410_GONE,
                    detail=(
                        "Edited client packet PDF not found for this signing request; "
                        "please regenerate the edited packet and create a new signing link"
                    ),
                )

            # The original packet file might have been lost (e.g. after a redeploy or filesystem reset).
            # In that case we try to regenerate a fresh base packet so that existing signing links remain usable.
            try:
                pdf_bytes, new_filename = justification_packet_service.generate_client_packet_pdf(
                    db, client, generate_missing=True
                )
            except ValueError as exc:
                _raise_client_packet_generation_error(str(exc))
            except Exception:
                _raise_client_packet_generation_failed()

            # Persist regenerated filename on the signature request so future calls use the new packet file.
            if new_filename and new_filename != request_obj.packet_filename:
                request_obj.packet_filename = new_filename
                _commit_and_refresh(db, request_obj)

            packet_path = export_dir / new_filename

            if not packet_path.is_file() and pdf_bytes is None:
                # Safeguard: if for some reason the regenerated file is not present, fall back to 404.
                _raise_client_packet_pdf_not_found()

    ascii_filename = _build_packet_ascii_filename(client)

    if pdf_bytes is None:
        pdf_bytes = justification_signing_service._try_read_bytes(packet_path)
    if pdf_bytes is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to read client packet PDF",
        )

    return _inline_pdf_response(pdf_bytes, ascii_filename)


@router.post("/client-sign/{token}/submit")
def submit_client_signature(
    token: str,
    payload: ClientSignatureSubmitPayload,
    db: Session = Depends(get_db),
):
    if not payload.signatureDataUrl:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing signature data",
        )

    try:
        request_obj = justification_signing_service.complete_packet_signature(
            db,
            token,
            payload.signatureDataUrl,
        )
    except ValueError as exc:
        message = str(exc)
        if message in {"SIGNATURE_REQUEST_NOT_FOUND", "CLIENT_NOT_FOUND"}:
            _raise_signing_link_not_found()
        if message == "SIGNATURE_REQUEST_ALREADY_COMPLETED":
            # אם הבקשה כבר הושלמה, נתייחס לזה כאל פעולה אידמפוטנטית
            # ונחזיר ללקוח את כתובת המסמך החתום במקום שגיאה.
            try:
                request_obj, _client = justification_signing_service.get_request_and_client_for_token(
                    db, token
                )
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_410_GONE,
                    detail="Signing link already used",
                )

            signed_packet_url = (
                _build_signed_packet_url(request_obj.client_id)
            )

            return {
                "detail": "Signature already saved",
                "status": request_obj.status,
                "signedPacketUrl": signed_packet_url,
            }
        if message == "CLIENT_PACKET_PDF_NOT_FOUND":
            _raise_client_packet_pdf_not_found()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save client signature",
        )

    signed_packet_url = _build_signed_packet_url(request_obj.client_id)

    return {
        "detail": "Signature saved",
        "status": request_obj.status,
        "signedPacketUrl": signed_packet_url,
    }
