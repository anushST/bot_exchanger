from fastapi import APIRouter

from . import endpoints

v1_router = APIRouter()

v1_router.include_router(endpoints.user_router, prefix='/users')
v1_router.include_router(endpoints.auth_router, prefix='/auth', tags=['Auth'])
