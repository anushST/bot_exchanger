from fastapi import APIRouter

from .v1.routers import v1_router

main_router = APIRouter()

main_router.include_router(v1_router, prefix='/v1')
