from fastapi import APIRouter

from . import endpoints

main_router = APIRouter()

main_router.include_router(
    endpoints.transaction_router, prefix='/transactions', tags=['Transactions']
)
main_router.include_router(
    endpoints.rate_router, prefix='/rate', tags=['Rate']
)
main_router.include_router(
    endpoints.currency_router, prefix='/currencies', tags=['Currencies']
)
main_router.include_router(
    endpoints.user_router, prefix='/users', tags=['Users']
)
