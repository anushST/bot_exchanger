from fastapi import APIRouter

from . import endpoints

v1_router = APIRouter()


v1_router.include_router(
    endpoints.appeal_router, prefix='/appeals', tags=['Appeals']
)
v1_router.include_router(
    endpoints.bank_router, prefix='/banks', tags=['Banks']
)
v1_router.include_router(
    endpoints.messages_router, prefix='/messages', tags=['Messages']
)
v1_router.include_router(
    endpoints.currency_router, prefix='/currencies', tags=['Currencies']
)
v1_router.include_router(
    endpoints.network_router, prefix='/networks', tags=['Networks']
)
v1_router.include_router(
    endpoints.deal_router, prefix='/deals', tags=['Deals']
)
v1_router.include_router(
    endpoints.offer_router, prefix='/offers', tags=['Offers']
)
