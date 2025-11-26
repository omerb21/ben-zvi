import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Database URL: can be overridden by environment variable, defaults to local SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./unified_crm_justification.db")

Base = declarative_base()


def get_engine(url: str | None = None):
    url = url or DATABASE_URL
    is_sqlite = url.startswith("sqlite")

    connect_args = {"check_same_thread": False} if is_sqlite else {}
    engine_kwargs: dict = {}

    if not is_sqlite:
        engine_kwargs.update(
            pool_pre_ping=True,
            pool_recycle=600,
            pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
        )

    return create_engine(url, connect_args=connect_args, **engine_kwargs)


engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
