from sqlalchemy import Column, Float, Integer, String

from app.database import Base


class SavingProduct(Base):
    """Reference table of saving products (from justification system)."""

    __tablename__ = "saving_product"

    id = Column(Integer, primary_key=True)
    fund_type = Column(String, nullable=False)
    company_name = Column(String, nullable=False)
    fund_name = Column(String, nullable=False)
    fund_code = Column(String, nullable=False)
    yield_1yr = Column(Float, nullable=True)
    yield_3yr = Column(Float, nullable=True)
    risk_level = Column(Integer, nullable=True)
    guaranteed_return = Column(String, nullable=True)
