from __future__ import annotations

from fastapi import HTTPException, status


FAILED_TO_SAVE_UPLOADED_PDF_DETAIL = "Failed to save uploaded PDF"


def raise_client_not_found() -> None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")


def raise_new_product_not_found() -> None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="New product not found")


def client_packet_pdf_not_found_exc() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client packet PDF not found")


def raise_client_packet_pdf_not_found() -> None:
    raise client_packet_pdf_not_found_exc()


def raise_no_pdfs_available_to_build_client_packet() -> None:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="No PDFs available to build client packet",
    )


def raise_client_packet_pdf_contains_no_pages() -> None:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Client packet PDF contains no pages",
    )


def raise_client_packet_generation_failed() -> None:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Client packet generation failed",
    )


def raise_client_packet_generation_error(message: str) -> None:
    if message == "NO_PDFS_FOR_CLIENT_PACKET":
        raise_no_pdfs_available_to_build_client_packet()
    if message == "NO_PAGES_IN_CLIENT_PACKET":
        raise_client_packet_pdf_contains_no_pages()
    raise_client_packet_generation_failed()


def raise_internal_server_error(detail: str) -> None:
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)


def raise_not_found(detail: str) -> None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def raise_uploaded_file_must_be_pdf() -> None:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file must be a PDF")


def raise_no_pages_specified_for_removal() -> None:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No pages specified for removal")


def raise_invalid_access_code() -> None:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access code")
