import shutil

from fastapi import APIRouter, Depends, HTTPException, Response, status, File, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.justification import FormOverlayPayload, PacketTrimPayload
from app.services import crm as crm_service
from app.services import justification_advice as justification_advice_service
from app.services import justification_b1 as justification_b1_service
from app.services import justification_kits as justification_kits_service
from app.services import justification_forms as justification_forms_service
from app.services import justification_packet as justification_packet_service
from app.utils.filepaths import get_client_justification_filename
from app.utils.filepaths import get_ascii_id_part as _get_ascii_id_part
from app.utils.filepaths import build_packet_ascii_filename as _build_packet_ascii_filename
from app.utils.http_headers import build_pdf_headers as _build_pdf_headers
from app.utils.http_exceptions import raise_new_product_not_found as _raise_new_product_not_found
from app.utils.http_exceptions import client_packet_pdf_not_found_exc as _client_packet_pdf_not_found_exc
from app.utils.http_exceptions import raise_client_not_found as _raise_client_not_found
from app.utils.http_exceptions import raise_client_packet_generation_error as _raise_client_packet_generation_error
from app.utils.http_exceptions import raise_client_packet_generation_failed as _raise_client_packet_generation_failed
from app.utils.http_exceptions import raise_internal_server_error as _raise_internal_server_error
from app.utils.http_exceptions import raise_not_found as _raise_not_found
from app.utils.http_exceptions import FAILED_TO_SAVE_UPLOADED_PDF_DETAIL as _FAILED_TO_SAVE_UPLOADED_PDF_DETAIL
from app.utils.http_exceptions import raise_uploaded_file_must_be_pdf as _raise_uploaded_file_must_be_pdf
from app.utils.http_exceptions import raise_no_pages_specified_for_removal as _raise_no_pages_specified_for_removal
from app.utils.uploads import read_upload_bytes as _read_upload_bytes
from app.utils.fs import try_write_bytes as _try_write_bytes
from app.routes.client_helpers import get_client_or_404 as _get_client_or_404


router = APIRouter(tags=["justification"])


def _get_export_dir(client):
    return justification_b1_service._get_client_export_dir(client)


def _pdf_response(pdf_bytes: bytes, filename: str, *, inline: bool) -> Response:
    headers = _build_pdf_headers(filename, inline=inline)
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


def _build_kit_ascii_filename(client_id: int, new_product_id: int, *, overlay: bool = False) -> str:
    suffix = "_overlay" if overlay else ""
    return f"kit_{client_id}_{new_product_id}{suffix}.pdf"


def _build_b1_ascii_filename(client, client_id: int, *, overlay: bool = False) -> str:
    ascii_id_part = _get_ascii_id_part(client, str(client_id))
    prefix = "b1_overlay" if overlay else "b1"
    return f"{prefix}_{ascii_id_part}.pdf"


def _read_pdf_bytes_from_paths(
    paths,
    *,
    not_found_exc: HTTPException,
    read_error_exc: HTTPException,
) -> bytes:
    try:
        for path in paths:
            if path.is_file():
                return path.read_bytes()
        raise not_found_exc
    except HTTPException:
        raise
    except Exception:
        raise read_error_exc


def _validate_pdf_upload_or_400(file: UploadFile) -> None:
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        _raise_uploaded_file_must_be_pdf()


async def _save_upload_file_or_500(
    file: UploadFile,
    *,
    target_path,
    error_detail: str,
) -> None:
    try:
        contents = await _read_upload_bytes(file)
        with target_path.open("wb") as f:
            f.write(contents)
    except Exception:
        _raise_internal_server_error(error_detail)


def _raise_kit_generation_error(message: str) -> None:
    if message == "CLIENT_NOT_FOUND":
        _raise_client_not_found()
    if message == "NEW_PRODUCT_NOT_FOUND":
        _raise_new_product_not_found()
    if message == "PRODUCT_DOES_NOT_BELONG_TO_CLIENT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Product does not belong to this client",
        )
    if message == "UNSUPPORTED_FUND_TYPE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Automatic form generation is supported only for גמל, גמל להשקעה, השתלמות",
        )
    if message.startswith("NO_TEMPLATE_FOUND"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No matching PDF template found for this fund type and company",
        )
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Kit generation failed")


def _raise_packet_generation_error(message: str) -> None:
    _raise_client_packet_generation_error(message)


def _raise_packet_trim_error(message: str) -> None:
    if message == "CLIENT_PACKET_PDF_NOT_FOUND":
        raise _client_packet_pdf_not_found_exc()
    if message == "NO_PAGES_LEFT_AFTER_TRIM":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pages left in packet after removal",
        )
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to trim client packet PDF",
    )


def _generate_kit_pdf_bytes_or_raise(generate_fn) -> bytes:
    try:
        pdf_bytes, _filename = generate_fn()
    except ValueError as exc:
        _raise_kit_generation_error(str(exc))
    return pdf_bytes


@router.get("/clients/{client_id}/advice.html")
def get_client_advice_html(
    client_id: int,
    db: Session = Depends(get_db),
):
    client = _get_client_or_404(db, client_id)

    html = justification_advice_service.build_advice_html(db, client)
    return Response(content=html, media_type="text/html; charset=utf-8")


@router.get("/clients/{client_id}/advice.pdf")
def download_client_advice_pdf(
    client_id: int,
    generate: bool = False,
    db: Session = Depends(get_db),
):
    client = _get_client_or_404(db, client_id)

    filename = get_client_justification_filename(client)

    export_dir = _get_export_dir(client)
    save_path = export_dir / filename

    if not generate and save_path.is_file():
        pdf_bytes = save_path.read_bytes()
        return _pdf_response(pdf_bytes, filename, inline=True)

    if not generate and not save_path.is_file():
        _raise_not_found("Advice PDF not found for client")

    html = justification_advice_service.build_advice_html(db, client)
    pdf_bytes = justification_advice_service.generate_advice_pdf(html)
    if pdf_bytes is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Advice PDF generation failed",
        )

    _try_write_bytes(save_path, pdf_bytes)

    return _pdf_response(pdf_bytes, filename, inline=True)


@router.post("/clients/{client_id}/advice-overlay.pdf")
def generate_client_advice_overlay_pdf(
    client_id: int,
    payload: FormOverlayPayload,
    db: Session = Depends(get_db),
):
    client = _get_client_or_404(db, client_id)

    html = justification_advice_service.build_advice_html(db, client)
    pdf_bytes = justification_advice_service.generate_advice_pdf(html)
    if pdf_bytes is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Advice PDF generation failed")

    overlaid = justification_forms_service.apply_overlay_to_pdf(
        pdf_bytes,
        free_text=payload.freeText or None,
        signature_image_data=None,
        signature_position=payload.signaturePosition or None,
    )

    ascii_filename = f"justification_overlay_{client_id}.pdf"
    return _pdf_response(overlaid, ascii_filename, inline=True)


@router.get("/clients/{client_id}/new-products/{new_product_id}/kit.pdf")
def download_client_new_product_kit_pdf(
    client_id: int,
    new_product_id: int,
    generate: bool = False,
    db: Session = Depends(get_db),
):
    client = _get_client_or_404(db, client_id)

    export_dir = _get_export_dir(client)
    edited_path = export_dir / f"kit_{new_product_id}_edited.pdf"
    auto_path = export_dir / f"kit_{client_id}_{new_product_id}.pdf"

    # View-only mode: prefer edited or pre-generated kit, do not generate new files.
    if not generate:
        pdf_bytes = _read_pdf_bytes_from_paths(
            [edited_path, auto_path],
            not_found_exc=HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Kit PDF not found for client and product",
            ),
            read_error_exc=HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to read existing kit PDF",
            ),
        )

        ascii_filename = _build_kit_ascii_filename(client_id, new_product_id)
        return _pdf_response(pdf_bytes, ascii_filename, inline=False)

    # Generate (or regenerate) kit PDF and save a stable copy for view-only access.
    pdf_bytes = _generate_kit_pdf_bytes_or_raise(
        lambda: justification_kits_service.generate_kit_pdf_for_new_product(
            db, client_id, new_product_id
        )
    )

    # Persist a stable copy that view-only mode can use later.
    _try_write_bytes(auto_path, pdf_bytes)

    # Use ASCII-only filename in header to avoid UnicodeEncodeError from non-ASCII characters
    ascii_filename = _build_kit_ascii_filename(client_id, new_product_id)

    return _pdf_response(pdf_bytes, ascii_filename, inline=False)


@router.post("/clients/{client_id}/b1-overlay.pdf")
def generate_client_b1_overlay_pdf(
    client_id: int,
    payload: FormOverlayPayload,
    db: Session = Depends(get_db),
):
    client = _get_client_or_404(db, client_id)

    pdf_bytes, _filename = justification_b1_service.generate_b1_pdf_for_client_overlay(
        client
    )

    overlaid = justification_forms_service.apply_overlay_to_pdf(
        pdf_bytes,
        free_text=payload.freeText or None,
        signature_image_data=payload.signatureDataUrl or None,
    )

    ascii_filename = _build_b1_ascii_filename(client, client_id, overlay=True)

    return _pdf_response(overlaid, ascii_filename, inline=True)


@router.post("/clients/{client_id}/new-products/{new_product_id}/kit-overlay.pdf")
def generate_client_new_product_kit_overlay_pdf(
    client_id: int,
    new_product_id: int,
    payload: FormOverlayPayload,
    db: Session = Depends(get_db),
):
    client = _get_client_or_404(db, client_id)

    pdf_bytes = _generate_kit_pdf_bytes_or_raise(
        lambda: justification_kits_service.generate_kit_pdf_for_new_product_overlay(
            db, client_id, new_product_id
        )
    )

    overlaid = justification_forms_service.apply_overlay_to_pdf(
        pdf_bytes,
        free_text=payload.freeText or None,
        signature_image_data=payload.signatureDataUrl or None,
    )

    ascii_filename = _build_kit_ascii_filename(client_id, new_product_id, overlay=True)
    return _pdf_response(overlaid, ascii_filename, inline=True)


@router.get("/clients/{client_id}/b1.pdf")
def download_client_b1_pdf(
    client_id: int,
    generate: bool = False,
    db: Session = Depends(get_db),
):
    client = _get_client_or_404(db, client_id)

    # Use ASCII-only filename in header to avoid UnicodeEncodeError
    ascii_filename = _build_b1_ascii_filename(client, client_id)

    export_dir = _get_export_dir(client)
    edited_path = export_dir / "b1_edited.pdf"
    auto_filename = f"יפוי כח עבור {client.first_name or ''} {client.last_name or ''}.pdf".strip()
    auto_path = export_dir / auto_filename

    if not generate:
        pdf_bytes = _read_pdf_bytes_from_paths(
            [edited_path, auto_path],
            not_found_exc=HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="B1 PDF not found for client",
            ),
            read_error_exc=HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to read existing B1 PDF",
            ),
        )

        return _pdf_response(pdf_bytes, ascii_filename, inline=True)

    pdf_bytes, _filename = justification_b1_service.generate_b1_pdf_for_client(client)

    return _pdf_response(pdf_bytes, ascii_filename, inline=False)


@router.post("/clients/{client_id}/b1-upload")
async def upload_client_b1_pdf(
    client_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    client = _get_client_or_404(db, client_id)

    _validate_pdf_upload_or_400(file)

    export_dir = _get_export_dir(client)
    edited_path = export_dir / "b1_edited.pdf"

    await _save_upload_file_or_500(file, target_path=edited_path, error_detail=_FAILED_TO_SAVE_UPLOADED_PDF_DETAIL)

    return {"detail": "B1 PDF uploaded"}


@router.post("/clients/{client_id}/new-products/{new_product_id}/kit-upload")
async def upload_client_new_product_kit_pdf(
    client_id: int,
    new_product_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    client = _get_client_or_404(db, client_id)

    _validate_pdf_upload_or_400(file)

    export_dir = _get_export_dir(client)
    edited_path = export_dir / f"kit_{new_product_id}_edited.pdf"

    await _save_upload_file_or_500(file, target_path=edited_path, error_detail=_FAILED_TO_SAVE_UPLOADED_PDF_DETAIL)

    return {"detail": "Kit PDF uploaded"}


@router.get("/clients/{client_id}/packet.pdf")
def download_client_packet_pdf(
    client_id: int,
    generate: bool = False,
    db: Session = Depends(get_db),
):
    client = _get_client_or_404(db, client_id)

    export_dir = _get_export_dir(client)
    base_packet_path = export_dir / f"packet_{client.id}.pdf"
    edited_packet_path = export_dir / f"packet_{client.id}_edited.pdf"

    # ASCII-only filename for HTTP header
    ascii_filename = _build_packet_ascii_filename(client, client_id)

    if not generate:
        pdf_bytes = _read_pdf_bytes_from_paths(
            [edited_packet_path, base_packet_path],
            not_found_exc=_client_packet_pdf_not_found_exc(),
            read_error_exc=HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to read existing client packet PDF",
            ),
        )

        return _pdf_response(pdf_bytes, ascii_filename, inline=False)

    try:
        pdf_bytes, _filename = justification_packet_service.generate_client_packet_pdf(
            db, client, generate_missing=True
        )
    except ValueError as exc:
        _raise_packet_generation_error(str(exc))
    except Exception:
        _raise_client_packet_generation_failed()

    return _pdf_response(pdf_bytes, ascii_filename, inline=False)


@router.post("/clients/{client_id}/packet-upload")
async def upload_client_packet_pdf(
    client_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    client = _get_client_or_404(db, client_id)

    _validate_pdf_upload_or_400(file)

    export_dir = _get_export_dir(client)
    edited_path = export_dir / f"packet_{client.id}_edited.pdf"

    await _save_upload_file_or_500(
        file,
        target_path=edited_path,
        error_detail="Failed to save uploaded client packet PDF",
    )

    return {"detail": "Client packet PDF uploaded"}


@router.post("/clients/{client_id}/packet-trim")
def trim_client_packet_pdf(
    client_id: int,
    payload: PacketTrimPayload,
    db: Session = Depends(get_db),
):
    client = _get_client_or_404(db, client_id)

    pages_to_remove = payload.pagesToRemove or []
    if not pages_to_remove:
        _raise_no_pages_specified_for_removal()

    try:
        edited_path = justification_packet_service.trim_client_packet_pdf(
            client,
            pages_to_remove,
        )
    except ValueError as exc:
        _raise_packet_trim_error(str(exc))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trim client packet PDF",
        )

    return {"detail": "Client packet PDF trimmed", "editedFilename": edited_path.name}


@router.delete("/clients/{client_id}/exports", status_code=status.HTTP_204_NO_CONTENT)
def delete_client_exports(
    client_id: int,
    db: Session = Depends(get_db),
):
    client = _get_client_or_404(db, client_id)

    export_dir = _get_export_dir(client)

    try:
        if export_dir.is_dir():
            shutil.rmtree(export_dir)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete client export directory",
        )


@router.get("/clients/{client_id}/packet-signed-client.pdf")
def download_client_signed_packet_pdf(
    client_id: int,
    db: Session = Depends(get_db),
):
    client = _get_client_or_404(db, client_id)

    export_dir = _get_export_dir(client)
    signed_packet_path = export_dir / f"packet_{client.id}_signed_client.pdf"

    ascii_filename = _build_packet_ascii_filename(client, client_id, signed=True)

    pdf_bytes = _read_pdf_bytes_from_paths(
        [signed_packet_path],
        not_found_exc=HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Signed client packet PDF not found",
        ),
        read_error_exc=HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to read signed client packet PDF",
        ),
    )

    return _pdf_response(pdf_bytes, ascii_filename, inline=True)
