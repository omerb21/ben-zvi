from app.models import ExistingProduct, NewProduct
from app.services import justification_kits_payloads


def _new_fund(fund_type: str) -> NewProduct:
    return NewProduct(
        client_id=1,
        existing_product_id=10,
        fund_type=fund_type,
        company_name="הפניקס",
        fund_name="קופה חלופית",
        fund_code="9876",
    )


def _old_fund() -> ExistingProduct:
    return ExistingProduct(
        client_id=1,
        fund_type="גמל",
        company_name="מור",
        fund_name="קופה קיימת",
        fund_code="1234",
        personal_number="old-1",
    )


def test_gemel_replacement_fields_use_replacement_fund_values():
    payload = justification_kits_payloads.build_fund_fields(_new_fund("גמל"), _old_fund())

    assert payload["mekabeletg_name"] == "קופה חלופית"
    assert payload["mekabeletg_number"] == "9876"
    assert "mekabelet_name" not in payload
    assert "mekabelet_number" not in payload


def test_investment_gemel_replacement_fields_use_replacement_fund_values():
    payload = justification_kits_payloads.build_fund_fields(_new_fund("גמל להשקעה"), _old_fund())

    assert payload["mekabeletgh_name"] == "קופה חלופית"
    assert payload["mekabeletgh_number"] == "9876"
    assert "mekabeletg_name" not in payload
    assert "mekabeleth_name" not in payload


def test_hishtalmut_replacement_fields_use_replacement_fund_values():
    payload = justification_kits_payloads.build_fund_fields(_new_fund("השתלמות"), _old_fund())

    assert payload["mekabeleth_name"] == "קופה חלופית"
    assert payload["mekabeleth_number"] == "9876"
    assert "mekabeletg_name" not in payload
    assert "mekabeletgh_name" not in payload


def test_unknown_fund_type_does_not_emit_replacement_fields():
    new_fund = NewProduct(
        client_id=1,
        existing_product_id=10,
        fund_type="פנסיה",
        company_name="הפניקס",
        fund_name="קופה חלופית",
        fund_code="9876",
    )
    payload = justification_kits_payloads.build_fund_fields(new_fund, _old_fund())

    assert "mekabeletg_name" not in payload
    assert "mekabeletgh_name" not in payload
    assert "mekabeleth_name" not in payload
