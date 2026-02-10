from fastapi import APIRouter

from app.api.v1.jobs import router as jobs_router
from app.api.v1.translate import router as translate_router

api_router = APIRouter()
api_router.include_router(translate_router, tags=["translate"])
api_router.include_router(jobs_router, tags=["jobs"])
