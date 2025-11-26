from datetime import date, datetime, timezone
import math

from sqlalchemy import Boolean, Column, Date, DateTime, Float, Index, Integer, String, Text, event
from sqlalchemy.orm import relationship

from app.database import Base


def utcnow():
    """Return current UTC datetime for ORM defaults"""
    return datetime.now(timezone.utc)


class Client(Base):
    """Client entity model for unified CRM + justification system"""

    __tablename__ = "client"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # ID number fields
    id_number_raw = Column(String(20), nullable=False)
    id_number = Column(String(9), nullable=False, unique=True, index=True)

    # Name fields
    full_name = Column(String(100), nullable=False, index=True)
    first_name = Column(String(50))
    last_name = Column(String(50))

    # Personal details
    birth_date = Column(Date, nullable=False)
    gender = Column(String(10))  # male, female, other
    marital_status = Column(String(20))  # single, married, divorced, widowed
    birth_country = Column(String(50))

    # Employment details
    self_employed = Column(Boolean, default=False)
    current_employer_exists = Column(Boolean, default=False)
    planned_termination_date = Column(Date)
    employer_name = Column(String(100))
    employer_hp = Column(String(20))
    employer_address = Column(String(200))
    employer_phone = Column(String(20))

    # Contact information
    email = Column(String(100))
    phone = Column(String(20))

    # Address
    address_street = Column(String(100))
    address_city = Column(String(50))
    address_house_number = Column(String(10))
    address_apartment = Column(String(10))
    address_postal_code = Column(String(10))

    # Retirement planning (already here to support future integration)
    retirement_target_date = Column(Date)

    # Tax-related fields
    num_children = Column(Integer, default=0)
    is_new_immigrant = Column(Boolean, default=False)
    is_veteran = Column(Boolean, default=False)
    is_disabled = Column(Boolean, default=False)
    disability_percentage = Column(Integer)
    is_student = Column(Boolean, default=False)
    reserve_duty_days = Column(Integer, default=0)

    # Income and deductions
    annual_salary = Column(Float)
    pension_contributions = Column(Float, default=0)
    study_fund_contributions = Column(Float, default=0)
    insurance_premiums = Column(Float, default=0)
    charitable_donations = Column(Float, default=0)

    # Tax credit points - נקודות זיכוי
    tax_credit_points = Column(Float, default=0)
    pension_start_date = Column(Date)
    spouse_income = Column(Float)
    immigration_date = Column(Date)
    military_discharge_date = Column(Date)

    # Record management
    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    # Indexes
    __table_args__ = (
        Index("ix_client_full_name_id_number", "full_name", "id_number"),
        Index("ix_client_is_active", "is_active"),
    )

    # Relationships used in CRM + justification
    snapshots = relationship("Snapshot", back_populates="client", cascade="all, delete-orphan")
    existing_products = relationship(
        "ExistingProduct", back_populates="client", cascade="all, delete-orphan"
    )
    new_products = relationship("NewProduct", back_populates="client", cascade="all, delete-orphan")
    client_notes = relationship("ClientNote", back_populates="client", cascade="all, delete-orphan")
    signature_requests = relationship(
        "ClientSignatureRequest",
        back_populates="client",
        cascade="all, delete-orphan",
    )

    def __init__(self, *args, **kwargs):
        # map older or alternate kwarg names to canonical field names
        alias_map = {
            "client_id": "id",  # client_id -> id
            "clientId": "id",  # clientId -> id
        }
        for alias, canonical in alias_map.items():
            if alias in kwargs and canonical not in kwargs:
                kwargs[canonical] = kwargs.pop(alias)
        cleaned_kwargs = {}
        for key, value in kwargs.items():
            v = value
            if isinstance(v, str):
                text = v.strip().lower()
                if text in {"nan", "none", ""}:
                    v = None
            else:
                try:
                    if math.isnan(v):
                        v = None
                except Exception:
                    pass
            cleaned_kwargs[key] = v

        super().__init__(*args, **cleaned_kwargs)

    def get_age(self, reference_date: date | None = None) -> int:
        """Calculate client age in years."""
        if not self.birth_date:
            return 0

        ref_date = reference_date or date.today()
        age = ref_date.year - self.birth_date.year

        # Adjust if birthday has not occurred yet this year
        if (ref_date.month, ref_date.day) < (self.birth_date.month, self.birth_date.day):
            age -= 1

        return age

    def __repr__(self) -> str:
        return f"<Client(id={self.id}, full_name='{self.full_name}', id_number='{self.id_number}')>"


def _normalize_client_nan_like_fields(target: "Client") -> None:
    numeric_fields = [
        "num_children",
        "reserve_duty_days",
        "disability_percentage",
    ]
    float_fields = [
        "annual_salary",
        "pension_contributions",
        "study_fund_contributions",
        "insurance_premiums",
        "charitable_donations",
        "tax_credit_points",
        "spouse_income",
    ]

    for attr in numeric_fields + float_fields:
        value = getattr(target, attr, None)
        if value is None:
            continue
        if isinstance(value, str):
            text = value.strip().lower()
            if text in {"nan", "none", ""}:
                setattr(target, attr, None)
                continue
        else:
            try:
                if math.isnan(value):
                    setattr(target, attr, None)
            except Exception:
                continue


@event.listens_for(Client, "before_insert")
def _client_fill_id_number_raw_before_insert(mapper, connection, target):
    """Fill id_number_raw from id_number if not provided during insert"""
    if not getattr(target, "id_number_raw", None) and getattr(target, "id_number", None):
        target.id_number_raw = target.id_number


@event.listens_for(Client, "before_update")
def _client_fill_id_number_raw_before_update(mapper, connection, target):
    """Fill id_number_raw from id_number if not provided during update"""
    if not getattr(target, "id_number_raw", None) and getattr(target, "id_number", None):
        target.id_number_raw = target.id_number


@event.listens_for(Client, "before_insert")
def _client_fill_full_name_before_insert(mapper, connection, target):
    """Fill full_name from first_name and last_name if not provided during insert"""
    if not getattr(target, "full_name", None):
        first_name = getattr(target, "first_name", "")
        last_name = getattr(target, "last_name", "")
        if first_name or last_name:
            target.full_name = f"{first_name} {last_name}".strip()

    # Set default birth_date if not provided (for testing / imported data)
    if not getattr(target, "birth_date", None):
        target.birth_date = date(1970, 1, 1)

    _normalize_client_nan_like_fields(target)


@event.listens_for(Client, "before_update")
def _client_fill_full_name_before_update(mapper, connection, target):
    """Fill full_name from first_name and last_name if not provided during update"""
    if not getattr(target, "full_name", None):
        first_name = getattr(target, "first_name", "")
        last_name = getattr(target, "last_name", "")
        if first_name or last_name:
            target.full_name = f"{first_name} {last_name}".strip()

    # Set default birth_date if not provided (for testing / imported data)
    if not getattr(target, "birth_date", None):
        target.birth_date = date(1970, 1, 1)

    _normalize_client_nan_like_fields(target)
