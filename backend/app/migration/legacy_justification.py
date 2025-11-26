from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, JSON, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker


DEFAULT_JUSTIFICATION_URL = "sqlite:///../../מערכת הנמקה/app.db"

JustificationBase = declarative_base()


class JustClient(JustificationBase):
    __tablename__ = "client"

    id = Column(Integer, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    national_id = Column(String, unique=True, nullable=False)
    gender = Column(String, nullable=False)
    marital_status = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    city = Column(String, nullable=False)
    street = Column(String, nullable=False)
    house_number = Column(String, nullable=True)
    apartment_number = Column(String, nullable=True)
    zip_code = Column(String, nullable=True)
    employer_name = Column(String, nullable=True)
    employer_company_id = Column(String, nullable=True)
    employer_address = Column(String, nullable=True)
    employer_phone = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class JustExistingProduct(JustificationBase):
    __tablename__ = "existing_product"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("client.id"), nullable=False)
    fund_type = Column(String, nullable=False)
    company_name = Column(String, nullable=False)
    fund_name = Column(String, nullable=False)
    fund_code = Column(String, nullable=False)
    yield_1yr = Column(Float, nullable=True)
    yield_3yr = Column(Float, nullable=True)
    personal_number = Column(String, nullable=False, unique=True)
    management_fee_balance = Column(Float, nullable=True)
    management_fee_contributions = Column(Float, nullable=True)
    accumulated_amount = Column(Float, nullable=True)
    employment_status = Column(String, nullable=True)
    has_regular_contributions = Column(Boolean, nullable=True)


class JustNewProduct(JustificationBase):
    __tablename__ = "new_product"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("client.id"), nullable=False)
    existing_product_id = Column(Integer, ForeignKey("existing_product.id"), nullable=True)
    fund_type = Column(String, nullable=False)
    company_name = Column(String, nullable=False)
    fund_name = Column(String, nullable=False)
    fund_code = Column(String, nullable=False)
    yield_1yr = Column(Float, nullable=True)
    yield_3yr = Column(Float, nullable=True)
    personal_number = Column(String, nullable=True, unique=True)
    management_fee_balance = Column(Float, nullable=True)
    management_fee_contributions = Column(Float, nullable=True)
    accumulated_amount = Column(Float, nullable=True)
    employment_status = Column(String, nullable=True)
    has_regular_contributions = Column(Boolean, nullable=True)
    created_at = Column(DateTime, nullable=False)


class JustSavingProduct(JustificationBase):
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


class JustFormInstance(JustificationBase):
    __tablename__ = "form_instance"

    id = Column(Integer, primary_key=True)
    new_product_id = Column(Integer, ForeignKey("new_product.id"), nullable=False)
    template_filename = Column(String(255), nullable=False)
    generated_at = Column(DateTime, nullable=False)
    status = Column(String(255), nullable=False)
    filled_data = Column(JSON, nullable=True)
    file_output_path = Column(String(512), nullable=True)


def get_justification_engine(url: str | None = None):
    db_url = url or DEFAULT_JUSTIFICATION_URL
    connect_args = {"check_same_thread": False}
    return create_engine(db_url, connect_args=connect_args)


def get_justification_session(url: str | None = None) -> Session:
    engine = get_justification_engine(url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()
