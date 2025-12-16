from fastapi import APIRouter

from app.routes import justification_products as justification_products_routes
from app.routes import justification_pdfs as justification_pdfs_routes
from app.routes import justification_signing as justification_signing_routes


router = APIRouter(prefix="/api/v1/justification", tags=["justification"])

router.include_router(justification_products_routes.router)
router.include_router(justification_pdfs_routes.router)
router.include_router(justification_signing_routes.router)
