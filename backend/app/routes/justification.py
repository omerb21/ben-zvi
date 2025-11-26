from typing import List
import os

from fastapi import APIRouter, Depends, HTTPException, Response, status, File, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.justification import (
    FormInstanceCreate,
    FormInstanceRead,
    NewProductCreate,
    NewProductRead,
    SavingProductRead,
    ExistingProductRead,
    ExistingProductCreate,
    ExistingProductUpdate,
    FormOverlayPayload,
    ClientSignatureSubmitPayload,
    PacketTrimPayload,
)
from app.services import justification as justification_service
from app.services import crm as crm_service
from app.services import justification_advice as justification_advice_service
from app.services import justification_b1 as justification_b1_service
from app.services import justification_kits as justification_kits_service
from app.services import justification_forms as justification_forms_service
from app.services import justification_packet as justification_packet_service
from app.services import justification_signing as justification_signing_service


router = APIRouter(prefix="/api/v1/justification", tags=["justification"])


@router.get("/saving-products", response_model=List[SavingProductRead])
def list_saving_products(db: Session = Depends(get_db)):
    products = justification_service.list_saving_products(db)
    return [
        SavingProductRead(
            id=product.id,
            fundType=product.fund_type,
            companyName=product.company_name,
            fundName=product.fund_name,
            fundCode=product.fund_code,
            yield1yr=product.yield_1yr,
            yield3yr=product.yield_3yr,
            riskLevel=product.risk_level,
            guaranteedReturn=product.guaranteed_return,
        )
        for product in products
    ]


@router.post(
    "/clients/{client_id}/existing-products",
    response_model=ExistingProductRead,
    status_code=status.HTTP_201_CREATED,
)
def create_existing_product_for_client(
    client_id: int,
    existing_in: ExistingProductCreate,
    db: Session = Depends(get_db),
):
    client = crm_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    product = justification_service.create_existing_product_for_client(db, client_id, existing_in)
    return ExistingProductRead(
        id=product.id,
        clientId=product.client_id,
        fundType=product.fund_type,
        companyName=product.company_name,
        fundName=product.fund_name,
        fundCode=product.fund_code,
        yield1yr=product.yield_1yr,
        yield3yr=product.yield_3yr,
        personalNumber=product.personal_number,
        managementFeeBalance=product.management_fee_balance,
        managementFeeContributions=product.management_fee_contributions,
        accumulatedAmount=product.accumulated_amount,
        employmentStatus=product.employment_status,
        hasRegularContributions=product.has_regular_contributions,
        isVirtual=False,
    )


@router.get(
    "/clients/{client_id}/existing-products",
    response_model=List[ExistingProductRead],
)
def list_existing_products_for_client(client_id: int, db: Session = Depends(get_db)):
    client = crm_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    products = justification_service.list_existing_products_view_for_client(db, client_id)
    return [
        ExistingProductRead(
            id=product["id"],
            clientId=product["client_id"],
            fundType=product["fund_type"],
            companyName=product["company_name"],
            fundName=product["fund_name"],
            fundCode=product["fund_code"],
            yield1yr=product["yield_1yr"],
            yield3yr=product["yield_3yr"],
            personalNumber=product["personal_number"],
            managementFeeBalance=product["management_fee_balance"],
            managementFeeContributions=product["management_fee_contributions"],
            accumulatedAmount=product["accumulated_amount"],
            employmentStatus=product["employment_status"],
            hasRegularContributions=product["has_regular_contributions"],
            isVirtual=product["is_virtual"],
        )
        for product in products
    ]


@router.patch(
    "/existing-products/{existing_product_id}",
    response_model=ExistingProductRead,
)
def update_existing_product(
    existing_product_id: int,
    existing_in: ExistingProductUpdate,
    db: Session = Depends(get_db),
):
    product = justification_service.update_existing_product(db, existing_product_id, existing_in)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Existing product not found",
        )

    return ExistingProductRead(
        id=product.id,
        clientId=product.client_id,
        fundType=product.fund_type,
        companyName=product.company_name,
        fundName=product.fund_name,
        fundCode=product.fund_code,
        yield1yr=product.yield_1yr,
        yield3yr=product.yield_3yr,
        personalNumber=product.personal_number,
        managementFeeBalance=product.management_fee_balance,
        managementFeeContributions=product.management_fee_contributions,
        accumulatedAmount=product.accumulated_amount,
        employmentStatus=product.employment_status,
        hasRegularContributions=product.has_regular_contributions,
        isVirtual=False,
    )


@router.get(
    "/clients/{client_id}/new-products",
    response_model=List[NewProductRead],
)
def list_new_products_for_client(client_id: int, db: Session = Depends(get_db)):
    client = crm_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    products = justification_service.list_new_products_for_client(db, client_id)
    return [
        NewProductRead(
            id=product.id,
            clientId=product.client_id,
            existingProductId=getattr(product, "existing_product_id", None),
            fundType=product.fund_type,
            companyName=product.company_name,
            fundName=product.fund_name,
            fundCode=product.fund_code,
            yield1yr=product.yield_1yr,
            yield3yr=product.yield_3yr,
            personalNumber=product.personal_number,
            managementFeeBalance=product.management_fee_balance,
            managementFeeContributions=product.management_fee_contributions,
            accumulatedAmount=product.accumulated_amount,
            employmentStatus=product.employment_status,
            hasRegularContributions=product.has_regular_contributions,
        )
        for product in products
    ]


@router.post(
    "/clients/{client_id}/new-products",
    response_model=NewProductRead,
    status_code=status.HTTP_201_CREATED,
)
def create_new_product_for_client(
    client_id: int,
    new_product_in: NewProductCreate,
    db: Session = Depends(get_db),
):
    client = crm_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    product = justification_service.create_new_product_for_client(db, client_id, new_product_in)
    return NewProductRead(
        id=product.id,
        clientId=product.client_id,
        existingProductId=getattr(product, "existing_product_id", None),
        fundType=product.fund_type,
        companyName=product.company_name,
        fundName=product.fund_name,
        fundCode=product.fund_code,
        yield1yr=product.yield_1yr,
        yield3yr=product.yield_3yr,
        personalNumber=product.personal_number,
        managementFeeBalance=product.management_fee_balance,
        managementFeeContributions=product.management_fee_contributions,
        accumulatedAmount=product.accumulated_amount,
        employmentStatus=product.employment_status,
        hasRegularContributions=product.has_regular_contributions,
    )


@router.get(
    "/new-products/{new_product_id}/form-instances",
    response_model=List[FormInstanceRead],
)
def list_form_instances_for_new_product(new_product_id: int, db: Session = Depends(get_db)):
    forms = justification_service.list_form_instances_for_new_product(db, new_product_id)
    return [
        FormInstanceRead(
            id=form.id,
            newProductId=form.new_product_id,
            templateFilename=form.template_filename,
            status=form.status,
            filledData=form.filled_data,
            fileOutputPath=form.file_output_path,
        )
        for form in forms
    ]


@router.post(
    "/new-products/{new_product_id}/form-instances",
    response_model=FormInstanceRead,
    status_code=status.HTTP_201_CREATED,
)
def create_form_instance_for_new_product(
    new_product_id: int,
    form_in: FormInstanceCreate,
    db: Session = Depends(get_db),
):
    # Could validate that new_product_id exists here if needed
    form = justification_service.create_form_instance_for_new_product(db, new_product_id, form_in)
    return FormInstanceRead(
        id=form.id,
        newProductId=form.new_product_id,
        templateFilename=form.template_filename,
        status=form.status,
        filledData=form.filled_data,
        fileOutputPath=form.file_output_path,
    )


@router.delete(
    "/new-products/{new_product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_new_product(new_product_id: int, db: Session = Depends(get_db)):
    deleted = justification_service.delete_new_product(db, new_product_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="New product not found",
        )


@router.delete(
    "/existing-products/{existing_product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_existing_product(existing_product_id: int, db: Session = Depends(get_db)):
    deleted = justification_service.delete_existing_product(db, existing_product_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Existing product not found",
        )


@router.delete(
    "/form-instances/{form_instance_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_form_instance(form_instance_id: int, db: Session = Depends(get_db)):
    deleted = justification_service.delete_form_instance(db, form_instance_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Form instance not found",
        )


@router.get("/clients/{client_id}/advice.html")
def get_client_advice_html(
    client_id: int,
    db: Session = Depends(get_db),
):
    client = crm_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    html = justification_advice_service.build_advice_html(db, client)
    return Response(content=html, media_type="text/html; charset=utf-8")


@router.get("/clients/{client_id}/advice.pdf")
def download_client_advice_pdf(
    client_id: int,
    generate: bool = False,
    db: Session = Depends(get_db),
):
    client = crm_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    display_name = client.full_name or client.id_number or f"client_{client_id}"
    safe_name_chars = []
    for ch in display_name:
        if ch.isalnum() or "\u0590" <= ch <= "\u05FF":
            safe_name_chars.append(ch)
        else:
            safe_name_chars.append("_")
    safe_name = "".join(safe_name_chars)

    # HTTP headers must be latin-1/ASCII encodable; replace non-ASCII with '_'
    ascii_safe_name_chars = []
    for ch in safe_name:
        if ch.isascii() and (ch.isalnum() or ch in "-_"):
            ascii_safe_name_chars.append(ch)
        else:
            ascii_safe_name_chars.append("_")
    ascii_safe_name = "".join(ascii_safe_name_chars) or f"client_{client_id}"

    filename = f"justification_{ascii_safe_name}.pdf"

    export_dir = justification_b1_service._get_client_export_dir(client)
    save_path = export_dir / filename

    if not generate and save_path.is_file():
        pdf_bytes = save_path.read_bytes()
        headers = {
            "Content-Disposition": f'inline; filename="{filename}"',
        }
        return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)

    if not generate and not save_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Advice PDF not found for client",
        )

    html = justification_advice_service.build_advice_html(db, client)
    pdf_bytes = justification_advice_service.generate_advice_pdf(html)
    if pdf_bytes is None:
        return Response(content=html, media_type="text/html; charset=utf-8")

    try:
        save_path.write_bytes(pdf_bytes)
    except Exception:
        pass

    headers = {
        "Content-Disposition": f'inline; filename="{filename}"',
    }
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


@router.post("/clients/{client_id}/advice-overlay.pdf")
def generate_client_advice_overlay_pdf(
    client_id: int,
    payload: FormOverlayPayload,
    db: Session = Depends(get_db),
):
    client = crm_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

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
    headers = {
        "Content-Disposition": f'inline; filename="{ascii_filename}"',
    }
    return Response(content=overlaid, media_type="application/pdf", headers=headers)


@router.get("/clients/{client_id}/new-products/{new_product_id}/kit.pdf")
def download_client_new_product_kit_pdf(
    client_id: int,
    new_product_id: int,
    generate: bool = False,
    db: Session = Depends(get_db),
):
    client = crm_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    export_dir = justification_b1_service._get_client_export_dir(client)
    edited_path = export_dir / f"kit_{new_product_id}_edited.pdf"
    auto_path = export_dir / f"kit_{client_id}_{new_product_id}.pdf"

    # View-only mode: prefer edited or pre-generated kit, do not generate new files.
    if not generate:
        try:
            if edited_path.is_file():
                pdf_bytes = edited_path.read_bytes()
            elif auto_path.is_file():
                pdf_bytes = auto_path.read_bytes()
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Kit PDF not found for client and product",
                )
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to read existing kit PDF",
            )

        ascii_client_id = str(client_id)
        ascii_product_id = str(new_product_id)
        ascii_filename = f"kit_{ascii_client_id}_{ascii_product_id}.pdf"
        headers = {
            "Content-Disposition": f'inline; filename="{ascii_filename}"',
        }
        return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)

    # Generate (or regenerate) kit PDF and save a stable copy for view-only access.
    try:
        pdf_bytes, filename = (
            justification_kits_service.generate_kit_pdf_for_new_product(
                db, client_id, new_product_id
            )
        )
    except ValueError as exc:
        message = str(exc)
        if message == "CLIENT_NOT_FOUND":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
        if message == "NEW_PRODUCT_NOT_FOUND":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="New product not found")
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

    # Persist a stable copy that view-only mode can use later.
    try:
        auto_path.write_bytes(pdf_bytes)
    except Exception:
        pass

    # Use ASCII-only filename in header to avoid UnicodeEncodeError from non-ASCII characters
    ascii_client_id = str(client_id)
    ascii_product_id = str(new_product_id)
    ascii_filename = f"kit_{ascii_client_id}_{ascii_product_id}.pdf"

    headers = {
        "Content-Disposition": f'inline; filename="{ascii_filename}"',
    }
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


@router.post("/clients/{client_id}/b1-overlay.pdf")
def generate_client_b1_overlay_pdf(
    client_id: int,
    payload: FormOverlayPayload,
    db: Session = Depends(get_db),
):
    client = crm_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    pdf_bytes, _filename = justification_b1_service.generate_b1_pdf_for_client_overlay(
        client
    )

    overlaid = justification_forms_service.apply_overlay_to_pdf(
        pdf_bytes,
        free_text=payload.freeText or None,
        signature_image_data=payload.signatureDataUrl or None,
    )

    id_part = client.id_number or str(client_id)
    ascii_id_part = "".join(ch for ch in id_part if ch.isascii() and ch.isalnum()) or str(client_id)
    ascii_filename = f"b1_overlay_{ascii_id_part}.pdf"

    headers = {
        "Content-Disposition": f'inline; filename="{ascii_filename}"',
    }
    return Response(content=overlaid, media_type="application/pdf", headers=headers)


@router.post("/clients/{client_id}/new-products/{new_product_id}/kit-overlay.pdf")
def generate_client_new_product_kit_overlay_pdf(
    client_id: int,
    new_product_id: int,
    payload: FormOverlayPayload,
    db: Session = Depends(get_db),
):
    client = crm_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    try:
        pdf_bytes, _filename = (
            justification_kits_service.generate_kit_pdf_for_new_product_overlay(
                db, client_id, new_product_id
            )
        )
    except ValueError as exc:
        message = str(exc)
        if message == "CLIENT_NOT_FOUND":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
        if message == "NEW_PRODUCT_NOT_FOUND":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="New product not found")
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

    overlaid = justification_forms_service.apply_overlay_to_pdf(
        pdf_bytes,
        free_text=payload.freeText or None,
        signature_image_data=payload.signatureDataUrl or None,
    )

    ascii_client_id = str(client_id)
    ascii_product_id = str(new_product_id)
    ascii_filename = f"kit_overlay_{ascii_client_id}_{ascii_product_id}.pdf"
    headers = {
        "Content-Disposition": f'inline; filename="{ascii_filename}"',
    }
    return Response(content=overlaid, media_type="application/pdf", headers=headers)


@router.get("/clients/{client_id}/b1.pdf")
def download_client_b1_pdf(
    client_id: int,
    generate: bool = False,
    db: Session = Depends(get_db),
):
    client = crm_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    # Use ASCII-only filename in header to avoid UnicodeEncodeError
    id_part = client.id_number or str(client_id)
    ascii_id_part = "".join(ch for ch in id_part if ch.isascii() and ch.isalnum()) or str(client_id)
    ascii_filename = f"b1_{ascii_id_part}.pdf"

    export_dir = justification_b1_service._get_client_export_dir(client)
    edited_path = export_dir / "b1_edited.pdf"
    auto_filename = f"יפוי כח עבור {client.first_name or ''} {client.last_name or ''}.pdf".strip()
    auto_path = export_dir / auto_filename

    if not generate:
        try:
            if edited_path.is_file():
                pdf_bytes = edited_path.read_bytes()
            elif auto_path.is_file():
                pdf_bytes = auto_path.read_bytes()
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="B1 PDF not found for client",
                )
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to read existing B1 PDF",
            )

        headers = {
            "Content-Disposition": f'inline; filename="{ascii_filename}"',
        }
        return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)

    pdf_bytes, _filename = justification_b1_service.generate_b1_pdf_for_client(client)

    headers = {
        "Content-Disposition": f'inline; filename="{ascii_filename}"',
    }
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


@router.post("/clients/{client_id}/b1-upload")
async def upload_client_b1_pdf(
    client_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    client = crm_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be a PDF",
        )

    export_dir = justification_b1_service._get_client_export_dir(client)
    edited_path = export_dir / "b1_edited.pdf"

    try:
        contents = await file.read()
        with edited_path.open("wb") as f:
            f.write(contents)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save uploaded PDF",
        )

    return {"detail": "B1 PDF uploaded"}


@router.post("/clients/{client_id}/new-products/{new_product_id}/kit-upload")
async def upload_client_new_product_kit_pdf(
    client_id: int,
    new_product_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    client = crm_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be a PDF",
        )

    export_dir = justification_b1_service._get_client_export_dir(client)
    edited_path = export_dir / f"kit_{new_product_id}_edited.pdf"

    try:
        contents = await file.read()
        with edited_path.open("wb") as f:
            f.write(contents)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save uploaded PDF",
        )

    return {"detail": "Kit PDF uploaded"}


@router.get("/clients/{client_id}/packet.pdf")
def download_client_packet_pdf(
    client_id: int,
    generate: bool = False,
    db: Session = Depends(get_db),
):
    client = crm_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    export_dir = justification_b1_service._get_client_export_dir(client)
    base_packet_path = export_dir / f"packet_{client.id}.pdf"
    edited_packet_path = export_dir / f"packet_{client.id}_edited.pdf"

    # ASCII-only filename for HTTP header
    id_part = client.id_number or str(client_id)
    ascii_id_part = "".join(ch for ch in id_part if ch.isascii() and ch.isalnum()) or str(client_id)
    ascii_filename = f"packet_{ascii_id_part}.pdf"

    if not generate:
        try:
            if edited_packet_path.is_file():
                pdf_bytes = edited_packet_path.read_bytes()
            elif base_packet_path.is_file():
                pdf_bytes = base_packet_path.read_bytes()
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Client packet PDF not found",
                )
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to read existing client packet PDF",
            )

        headers = {
            "Content-Disposition": f'inline; filename="{ascii_filename}"',
        }
        return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)

    try:
        pdf_bytes, _filename = justification_packet_service.generate_client_packet_pdf(
            db, client, generate_missing=True
        )
    except ValueError as exc:
        message = str(exc)
        if message == "NO_PDFS_FOR_CLIENT_PACKET":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No PDFs available to build client packet",
            )
        if message == "NO_PAGES_IN_CLIENT_PACKET":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Client packet PDF contains no pages",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Client packet generation failed",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Client packet generation failed",
        )

    headers = {
        "Content-Disposition": f'inline; filename="{ascii_filename}"',
    }
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


@router.post("/clients/{client_id}/packet-upload")
async def upload_client_packet_pdf(
    client_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    client = crm_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be a PDF",
        )

    export_dir = justification_b1_service._get_client_export_dir(client)
    edited_path = export_dir / f"packet_{client.id}_edited.pdf"

    try:
        contents = await file.read()
        with edited_path.open("wb") as f:
            f.write(contents)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save uploaded client packet PDF",
        )

    return {"detail": "Client packet PDF uploaded"}


@router.post("/clients/{client_id}/packet-trim")
def trim_client_packet_pdf(
    client_id: int,
    payload: PacketTrimPayload,
    db: Session = Depends(get_db),
):
    client = crm_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    pages_to_remove = payload.pagesToRemove or []
    if not pages_to_remove:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pages specified for removal",
        )

    try:
        edited_path = justification_packet_service.trim_client_packet_pdf(
            client,
            pages_to_remove,
        )
    except ValueError as exc:
        message = str(exc)
        if message == "CLIENT_PACKET_PDF_NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client packet PDF not found",
            )
        if message == "NO_PAGES_LEFT_AFTER_TRIM":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No pages left in packet after removal",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trim client packet PDF",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trim client packet PDF",
        )

    return {"detail": "Client packet PDF trimmed", "editedFilename": edited_path.name}


@router.get("/clients/{client_id}/packet-signed-client.pdf")
def download_client_signed_packet_pdf(
    client_id: int,
    db: Session = Depends(get_db),
):
    client = crm_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    export_dir = justification_b1_service._get_client_export_dir(client)
    signed_packet_path = export_dir / f"packet_{client.id}_signed_client.pdf"

    if not signed_packet_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Signed client packet PDF not found",
        )

    id_part = client.id_number or str(client_id)
    ascii_id_part = "".join(ch for ch in id_part if ch.isascii() and ch.isalnum()) or str(client_id)
    ascii_filename = f"packet_{ascii_id_part}_signed_client.pdf"

    try:
        pdf_bytes = signed_packet_path.read_bytes()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to read signed client packet PDF",
        )

    headers = {
        "Content-Disposition": f'inline; filename="{ascii_filename}"',
    }
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


@router.post("/clients/{client_id}/packet-sign-request")
def create_client_packet_sign_request(
    client_id: int,
    db: Session = Depends(get_db),
):
    client = crm_service.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    try:
        request_obj = justification_signing_service.create_packet_signature_request(db, client_id)
    except ValueError as exc:
        message = str(exc)
        if message == "CLIENT_NOT_FOUND":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
        if message == "CLIENT_PACKET_PDF_NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client packet PDF not found",
            )
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
    try:
        request_obj, client = justification_signing_service.get_active_request_for_token(db, token)
    except ValueError as exc:
        message = str(exc)
        if message in {"SIGNATURE_REQUEST_NOT_FOUND", "CLIENT_NOT_FOUND"}:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Signing link not found",
            )
        if message == "SIGNATURE_REQUEST_ALREADY_COMPLETED":
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Signing link already used",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load signing page",
        )

    client_name_parts = [client.first_name or "", client.last_name or ""]
    client_name = " ".join(part for part in client_name_parts if part).strip()
    if not client_name:
        client_name = client.full_name or client.id_number or "לקוח"

    env = justification_advice_service._get_templates_env()
    template = env.get_template("client_sign.html")

    packet_url = f"/api/v1/justification/client-sign/{token}/packet.pdf"
    submit_url = f"/api/v1/justification/client-sign/{token}/submit"

    html = template.render(
        client_name=client_name,
        packet_url=packet_url,
        submit_url=submit_url,
    )
    return Response(content=html, media_type="text/html; charset=utf-8")


@router.get("/client-sign/{token}/packet.pdf")
def download_client_packet_for_sign(
    token: str,
    db: Session = Depends(get_db),
):
    print("[sign] download_client_packet_for_sign called, token=", token)
    try:
        request_obj, client = justification_signing_service.get_active_request_for_token(db, token)
    except ValueError as exc:
        message = str(exc)
        if message in {"SIGNATURE_REQUEST_NOT_FOUND", "CLIENT_NOT_FOUND"}:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Signing link not found",
            )
        if message == "SIGNATURE_REQUEST_ALREADY_COMPLETED":
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Signing link already used",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load client packet for sign",
        )

    export_dir = justification_b1_service._get_client_export_dir(client)
    packet_path = export_dir / request_obj.packet_filename

    if not packet_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client packet PDF not found",
        )

    id_part = client.id_number or str(client.id)
    ascii_id_part = "".join(ch for ch in id_part if ch.isascii() and ch.isalnum()) or str(client.id)
    ascii_filename = f"packet_{ascii_id_part}.pdf"

    try:
        pdf_bytes = packet_path.read_bytes()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to read client packet PDF",
        )

    headers = {
        "Content-Disposition": f'inline; filename="{ascii_filename}"',
    }
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


@router.post("/client-sign/{token}/submit")
def submit_client_signature(
    token: str,
    payload: ClientSignatureSubmitPayload,
    db: Session = Depends(get_db),
):
    print("[sign] submit_client_signature called, token=", token)
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Signing link not found",
            )
        if message == "SIGNATURE_REQUEST_ALREADY_COMPLETED":
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Signing link already used",
            )
        if message == "CLIENT_PACKET_PDF_NOT_FOUND":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client packet PDF not found",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save client signature",
        )

    return {"detail": "Signature saved", "status": request_obj.status}
