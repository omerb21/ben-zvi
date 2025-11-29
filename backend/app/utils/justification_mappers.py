from typing import Any, Dict

from app.models import ExistingProduct, FormInstance, NewProduct, SavingProduct
from app.schemas.justification import (
    ExistingProductRead,
    FormInstanceRead,
    NewProductRead,
    SavingProductRead,
)


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
        isVirtual=is_virtual,
    )


def to_existing_product_read_from_dict(data: Dict[str, Any]) -> ExistingProductRead:
    return ExistingProductRead(
        id=data["id"],
        clientId=data["client_id"],
        fundType=data["fund_type"],
        companyName=data["company_name"],
        fundName=data["fund_name"],
        fundCode=data["fund_code"],
        yield1yr=data["yield_1yr"],
        yield3yr=data["yield_3yr"],
        personalNumber=data["personal_number"],
        managementFeeBalance=data["management_fee_balance"],
        managementFeeContributions=data["management_fee_contributions"],
        accumulatedAmount=data["accumulated_amount"],
        employmentStatus=data["employment_status"],
        hasRegularContributions=data["has_regular_contributions"],
        isVirtual=data["is_virtual"],
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
