from fastapi import APIRouter

from app.api.routes.admin import router as admin_router
from app.api.routes.auth import router as auth_router
from app.api.routes.catalog import router as catalog_router
from app.api.routes.movies import router as movies_router
from app.api.routes.reviews import admin_router as admin_reviews_router
from app.api.routes.reviews import router as reviews_router
from app.api.routes.tmdb import router as tmdb_router
from app.api.routes.user_movies import router as user_movies_router


api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
api_router.include_router(movies_router)
api_router.include_router(user_movies_router)
api_router.include_router(reviews_router)
api_router.include_router(tmdb_router)
api_router.include_router(catalog_router)
api_router.include_router(admin_router)
api_router.include_router(admin_reviews_router)
