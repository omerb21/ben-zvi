from typing import Any, Dict

from app.models import ExistingProduct, FormInstance, NewProduct, SavingProduct
from app.schemas.justification import (
    ExistingProductRead,
    FormInstanceRead,
    NewProductRead,
    SavingProductRead,
)


def _existing_product_read_kwargs(
    *,
    id: int,
    client_id: int,
    fund_type: str,
    company_name: str,
    fund_name: str,
    fund_code: str,
    yield_1yr,
    yield_3yr,
    personal_number,
    management_fee_balance,
    management_fee_contributions,
    accumulated_amount,
    employment_status,
    has_regular_contributions,
    is_virtual: bool,
) -> Dict[str, Any]:
    return {
        "id": id,
        "clientId": client_id,
        "fundType": fund_type,
        "companyName": company_name,
        "fundName": fund_name,
        "fundCode": fund_code,
        "yield1yr": yield_1yr,
        "yield3yr": yield_3yr,
        "personalNumber": personal_number,
        "managementFeeBalance": management_fee_balance,
        "managementFeeContributions": management_fee_contributions,
        "accumulatedAmount": accumulated_amount,
        "employmentStatus": employment_status,
        "hasRegularContributions": has_regular_contributions,
        "isVirtual": is_virtual,
    }


def to_saving_product_read(product: SavingProduct) -> SavingProductRead:
    return SavingProductRead(
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


def to_existing_product_read(product: ExistingProduct, is_virtual: bool = False) -> ExistingProductRead:
    return ExistingProductRead(
        **_existing_product_read_kwargs(
            id=product.id,
            client_id=product.client_id,
            fund_type=product.fund_type,
            company_name=product.company_name,
            fund_name=product.fund_name,
            fund_code=product.fund_code,
            yield_1yr=product.yield_1yr,
            yield_3yr=product.yield_3yr,
            personal_number=product.personal_number,
            management_fee_balance=product.management_fee_balance,
            management_fee_contributions=product.management_fee_contributions,
            accumulated_amount=product.accumulated_amount,
            employment_status=product.employment_status,
            has_regular_contributions=product.has_regular_contributions,
            is_virtual=is_virtual,
        )
    )


def to_existing_product_read_from_dict(data: Dict[str, Any]) -> ExistingProductRead:
    return ExistingProductRead(
        **_existing_product_read_kwargs(
            id=data["id"],
            client_id=data["client_id"],
            fund_type=data["fund_type"],
            company_name=data["company_name"],
            fund_name=data["fund_name"],
            fund_code=data["fund_code"],
            yield_1yr=data["yield_1yr"],
            yield_3yr=data["yield_3yr"],
            personal_number=data["personal_number"],
            management_fee_balance=data["management_fee_balance"],
            management_fee_contributions=data["management_fee_contributions"],
            accumulated_amount=data["accumulated_amount"],
            employment_status=data["employment_status"],
            has_regular_contributions=data["has_regular_contributions"],
            is_virtual=data["is_virtual"],
        )
    )


def to_new_product_read(product: NewProduct) -> NewProductRead:
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


def to_form_instance_read(form: FormInstance) -> FormInstanceRead:
    return FormInstanceRead(
        id=form.id,
        newProductId=form.new_product_id,
        templateFilename=form.template_filename,
        status=form.status,
        filledData=form.filled_data,
        fileOutputPath=form.file_output_path,
    )
