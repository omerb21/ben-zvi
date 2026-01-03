from contextlib import asynccontextmanager

import os
from dotenv import load_dotenv

load_dotenv(override=True)

from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import JSONResponse

import app.models  # noqa: F401
from app.database import Base, engine
from app.migration.schema_upgrade import ensure_schema_up_to_date
from app.routes import crm as crm_routes
from app.routes import justification as justification_routes
from app.routes import admin as admin_routes

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


static_dir = None
for candidate in ("app/static", "backend/app/static"):
    if os.path.isdir(candidate):
        static_dir = candidate
        break

if static_dir:
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


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
        "https://bzclient.onrender.com",
        "https://ben-zvi-production.up.railway.app",
        "https://bzclient-production.up.railway.app",
    ]


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


APP_PASSWORD = os.getenv("APP_PASSWORD", "benzvi5090")


@app.middleware("http")
async def password_protect_api(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)

    path = request.url.path
    if path == "/health" or path.startswith("/static"):
        return await call_next(request)

    # Public client signing pages must work in a normal browser tab without X-App-Password.
    # These routes still validate their token internally.
    if path.startswith("/api/v1/justification/client-sign/"):
        return await call_next(request)

    # Allow /api/v1/crm/* with X-Client-Token to bypass APP_PASSWORD
    if path.startswith("/api/v1/crm") and request.headers.get("x-client-token"):
        # Still verify client token in the CRM router, just skip APP_PASSWORD
        response = await call_next(request)
        # Ensure CORS headers for 401 responses from CRM routes
        if response.status_code == 401:
            origin = request.headers.get("origin")
            if origin and origin in allowed_origins:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Vary"] = "Origin"
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Methods"] = "*"
                response.headers["Access-Control-Allow-Headers"] = "*"
        return response

    if path.startswith("/api") or path.startswith("/docs") or path.startswith("/openapi.json"):
        provided = request.headers.get("x-app-password")
        if not provided or provided != APP_PASSWORD:
            response = JSONResponse(status_code=401, content={"detail": "Unauthorized"})

            origin = request.headers.get("origin")
            if origin and origin in allowed_origins:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Vary"] = "Origin"
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Methods"] = "*"
                response.headers["Access-Control-Allow-Headers"] = "*"

            return response

    return await call_next(request)


app.include_router(crm_routes.router)
app.include_router(justification_routes.router)
app.include_router(admin_routes.router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
