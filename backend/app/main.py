from contextlib import asynccontextmanager

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import app.models  # noqa: F401
from app.database import Base, engine
from app.migration.schema_upgrade import ensure_schema_up_to_date
from app.routes import crm as crm_routes
from app.routes import justification as justification_routes
from app.routes import admin as admin_routes
from app.services import justification_forms


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler: ensure DB tables exist on startup."""
    Base.metadata.create_all(bind=engine)
    # Apply lightweight, non-destructive schema upgrades (e.g. new Client columns)
    ensure_schema_up_to_date(engine)
    yield


app = FastAPI(
    title="Unified CRM & Justification API",
    description="API for unified CRM and justification system",
    version="0.1.0",
    lifespan=lifespan,
)


app.mount("/static", StaticFiles(directory="app/static"), name="static")


cors_origins_env = os.getenv("CORS_ALLOW_ORIGINS")
if cors_origins_env:
    allowed_origins = [
        origin.strip()
        for origin in cors_origins_env.split(",")
        if origin.strip()
    ]
else:
    allowed_origins = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://localhost:5174",
        "https://ben-zvi.onrender.com",
    ]


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(crm_routes.router)
app.include_router(justification_routes.router)
app.include_router(admin_routes.router)


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "version": "0.1.0",
        "justification_forms_path": str(justification_forms.__file__),
    }
