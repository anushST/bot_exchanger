from fastapi import APIRouter

from . import endpoints

main_router = APIRouter()

main_router.include_router(
    endpoints.transaction_router, prefix='/transactions', tags=['Transactions']
)
