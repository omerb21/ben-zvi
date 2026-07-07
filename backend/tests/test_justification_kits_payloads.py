from app.models import ExistingProduct, NewProduct
from app.services import justification_kits_payloads


def test_mekabelet_fields_use_replacement_fund_values():
    new_fund = NewProduct(
        client_id=1,
        existing_product_id=10,
        fund_type="גמל",
        company_name="הפניקס",
        fund_name="קופה חלופית",
        fund_code="9876",
    )
    old_fund = ExistingProduct(
        client_id=1,
        fund_type="גמל",
        company_name="מור",
        fund_name="קופה קיימת",
        fund_code="1234",
        personal_number="old-1",
    )

    payload = justification_kits_payloads.build_fund_fields(new_fund, old_fund)

    assert payload["mekabelet_name"] == "קופה חלופית"
    assert payload["mekabelet_number"] == "9876"
