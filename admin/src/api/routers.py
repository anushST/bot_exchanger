from fastapi import APIRouter

from . import endpoints

main_router = APIRouter()


main_router.include_router(
    endpoints.admin_statistics_router, prefix='/admin', tags=['Statistics']
)
main_router.include_router(
    endpoints.admin_marketing_link_router, prefix='/admin/marketing_links',
    tags=["Marketing Links"]
)
main_router.include_router(
    endpoints.admin_user_router, prefix='/admin/users', tags=['Admin Users']
)
main_router.include_router(
    endpoints.admin_transaction_router, prefix='/admin/transactions',
    tags=['Transactions']
)
