from datetime import date

from app.models import Client, NewProduct
from app.services import justification_kits_templates as templates


def _client(birth_date: date) -> Client:
    return Client(
        id_number_raw="123456789",
        id_number="123456789",
        full_name="לקוח בדיקה",
        birth_date=birth_date,
    )


def _mor_investment_product(company_name: str = "MOR") -> NewProduct:
    return NewProduct(
        client_id=1,
        fund_type="גמל להשקעה",
        company_name=company_name,
        fund_name="מור גמל להשקעה",
        fund_code="1234",
    )


def test_minor_age_boundary():
    today = date(2026, 6, 14)

    assert templates._is_minor(_client(date(2008, 6, 15)), today=today)
    assert not templates._is_minor(_client(date(2008, 6, 14)), today=today)


def test_minor_mor_investment_uses_minor_template(monkeypatch):
    monkeypatch.setattr(templates, "_is_minor", lambda client: True)

    template_name = templates._template_name_for_product(
        _mor_investment_product(),
        _client(date(2015, 1, 1)),
    )

    assert template_name == templates.MOR_MINOR_INVESTMENT_TEMPLATE


def test_adult_or_other_company_uses_regular_investment_template(monkeypatch):
    monkeypatch.setattr(templates, "_is_minor", lambda client: False)
    regular_template = templates.FUND_TYPE_TEMPLATES["גמל להשקעה"]

    adult_mor_template = templates._template_name_for_product(
        _mor_investment_product(),
        _client(date(1990, 1, 1)),
    )
    minor_other_company_template = templates._template_name_for_product(
        _mor_investment_product("הפניקס"),
        _client(date(2015, 1, 1)),
    )

    assert adult_mor_template == regular_template
    assert minor_other_company_template == regular_template
