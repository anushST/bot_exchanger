from fastapi import APIRouter

from . import endpoints

v1_router = APIRouter()

v1_router.include_router(
    endpoints.messages_router, prefix='/messages', tags=['Messages']
)
