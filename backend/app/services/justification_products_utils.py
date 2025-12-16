from typing import Dict, Any, List


def _product_schema_to_model_kwargs(product_in) -> Dict[str, Any]:
    return {
        "fund_type": product_in.fundType,
        "company_name": product_in.companyName,
        "fund_name": product_in.fundName,
        "fund_code": product_in.fundCode,
        "yield_1yr": product_in.yield1yr,
        "yield_3yr": product_in.yield3yr,
        "personal_number": product_in.personalNumber,
        "management_fee_balance": product_in.managementFeeBalance,
        "management_fee_contributions": product_in.managementFeeContributions,
        "accumulated_amount": product_in.accumulatedAmount,
        "employment_status": product_in.employmentStatus,
        "has_regular_contributions": product_in.hasRegularContributions,
    }


def _find_existing_view_item_by_id(
    existing_view_items: List[Dict[str, Any]],
    target_id: int,
) -> Dict[str, Any] | None:
    for item in existing_view_items:
        if item.get("id") == target_id:
            return item
    return None
