from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker


DEFAULT_MINI_CRM_URL = "sqlite:///../../mini_crm/crm.db"

MiniCrmBase = declarative_base()


class MiniCrmClient(MiniCrmBase):
    __tablename__ = "client"

    id = Column(Integer, primary_key=True)
    id_canon = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)


class MiniCrmSnapshot(MiniCrmBase):
    __tablename__ = "snapshot"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("client.id"), nullable=False)
    fund_code = Column(String, nullable=False)
    fund_type = Column(String, nullable=True)
    fund_name = Column(String, nullable=True)
    fund_number = Column(String, nullable=True)
    source = Column(String, nullable=True)
    amount = Column(Float, nullable=False)
    snapshot_date = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)


def get_mini_crm_engine(url: str | None = None):
    db_url = url or DEFAULT_MINI_CRM_URL
    connect_args = {"check_same_thread": False}
    return create_engine(db_url, connect_args=connect_args)


def get_mini_crm_session(url: str | None = None) -> Session:
    engine = get_mini_crm_engine(url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()
