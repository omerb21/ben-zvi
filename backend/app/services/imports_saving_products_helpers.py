from __future__ import annotations

from app.models import SavingProduct
from app.schemas.justification import SavingProductCreate


def _to_float_percent(value: str | None) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace("%", "")
    if not text:
        return None
    try:
        return float(text)
    except Exception:
        return None


def _fallback_float_percent(primary: str | None, fallback: str | None) -> float | None:
    value = _to_float_percent(primary)
    if not value:
        return _to_float_percent(fallback)
    return value


def _update_saving_product_from_schema(sp: SavingProduct, p: SavingProductCreate) -> bool:
    changed = False
    if sp.fund_type != p.fundType:
        sp.fund_type = p.fundType
        changed = True
    if sp.company_name != p.companyName:
        sp.company_name = p.companyName
        changed = True
    if sp.fund_name != p.fundName:
        sp.fund_name = p.fundName
        changed = True

    if p.yield1yr is not None and sp.yield_1yr != p.yield1yr:
        sp.yield_1yr = p.yield1yr
        changed = True
    if p.yield3yr is not None and sp.yield_3yr != p.yield3yr:
        sp.yield_3yr = p.yield3yr
        changed = True
    if p.riskLevel is not None and sp.risk_level != p.riskLevel:
        sp.risk_level = p.riskLevel
        changed = True
    if p.guaranteedReturn is not None and sp.guaranteed_return != p.guaranteedReturn:
        sp.guaranteed_return = p.guaranteedReturn
        changed = True

    return changed


def _create_saving_product(
    *,
    fund_type: str,
    company_name: str,
    fund_name: str,
    fund_code: str,
    yield_1yr: float | None,
    yield_3yr: float | None,
    risk_level: float | None,
    guaranteed_return: str | None,
) -> SavingProduct:
    return SavingProduct(
        fund_type=fund_type,
        company_name=company_name,
        fund_name=fund_name,
        fund_code=fund_code,
        yield_1yr=yield_1yr,
        yield_3yr=yield_3yr,
        risk_level=risk_level,
        guaranteed_return=guaranteed_return,
    )


def _saving_product_compound_key(
    fund_type: str | None,
    company_name: str | None,
    fund_name: str | None,
    fund_code: str | None,
) -> tuple[str, str, str, str]:
    return (
        fund_type or "",
        company_name or "",
        fund_name or "",
        fund_code or "",
    )
