"""
Merge into app/api/router.py.
"""

from app.api.routes.catalog import router as catalog_router
from app.api.routes.admin_full import router as admin_full_router

# api_router.include_router(catalog_router)
# If replacing old admin router:
# api_router.include_router(admin_full_router)
