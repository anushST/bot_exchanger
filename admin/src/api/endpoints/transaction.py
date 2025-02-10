import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.endpoints import schemas
from src.core.db import get_async_session
from src.models import Transaction, TransactionStatuses, User

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get('/', response_model=list[schemas.TransactionSummary])
async def get_user_transactions(
    session: AsyncSession = Depends(get_async_session),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    try:
        result = await session.execute(
            select(Transaction)
            .order_by(Transaction.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        transactions = result.scalars().all()

        return [
            schemas.TransactionSummary(
                rate_type=transaction.rate_type,
                transaction_id=transaction.name,
                status=transaction.status,
                from_amount=transaction.final_from_amount,
                from_currency=transaction.final_from_currency,
                to_amount=transaction.final_to_amount,
                to_currency=transaction.final_to_currency,
                time_created=transaction.created_at
            ) for transaction in transactions if (
                transaction.status not in (TransactionStatuses.NEW.value,
                                           TransactionStatuses.ERROR.value))
        ]
    except Exception as e:
        logger.error(e, exc_info=True)
        raise HTTPException(
            status_code=500, detail=f'Error retrieving transactions: {str(e)}'
        )


@router.get('/{transaction_id}')
async def get_transaction(
        transaction_id: str,
        session: AsyncSession = Depends(get_async_session)):
    try:
        result = await session.execute(
            select(Transaction).where(Transaction.name == transaction_id)
        )
        transaction = result.scalars().first()

        result = await session.execute(
            select(User).where(User.id == transaction.user_id)
        )

        if not transaction:
            raise HTTPException(status_code=404,
                                detail='Transaction not found')

        user = result.scalars().first()
        if user:
            user_model = schemas.User(
                tg_id=user.tg_id, tg_name=user.tg_name,
                tg_username=user.tg_username
            )

        if transaction.status == TransactionStatuses.NEW.value:
            return {'detail': 'Transaction is not processed yet'}
        elif transaction.status == TransactionStatuses.ERROR.value:
            return {'detail': 'Transaction finished with error',
                    'code': transaction.status_code}
        return schemas.Transaction(
            user=user_model,
            rate_type=transaction.final_rate_type,
            currency_from=transaction.final_from_currency,
            currency_from_network=transaction.final_from_network,
            currency_to=transaction.final_to_currency,
            currency_to_network=transaction.final_to_network,
            transaction_id=transaction.name,
            status=transaction.status,
            status_code=transaction.status_code,
            from_amount=transaction.final_from_amount,
            to_amount=transaction.final_to_amount,
            from_address=transaction.final_from_address,
            to_address=transaction.final_to_address,
            refund_address=transaction.refund_address,
            from_tag_name=transaction.final_from_tag_name,
            to_tag_name=transaction.final_to_tag_name,
            refund_tag_name=transaction.refund_tag_name,
            from_tag_value=transaction.final_from_tag_value,
            to_tag_value=transaction.final_to_tag_value,
            refund_tag_value=transaction.refund_tag_value,
            time_expiration=transaction.time_expiration,
            created_at=transaction.created_at,
            received_from_id=transaction.received_from_id,
            received_from_amount=transaction.received_from_amount,
            received_from_confirmations=transaction.received_from_confirmations, # noqa
            received_to_id=transaction.received_to_id,
            received_to_amount=transaction.received_to_amount,
            received_to_confirmations=transaction.received_to_confirmations,
            received_back_id=transaction.received_back_id,
            received_back_amount=transaction.received_back_amount,
            received_back_confirmations=transaction.received_back_confirmations
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(e, exc_info=True)
        raise HTTPException(
            status_code=500, detail=f'Error retrieving transaction: {str(e)}')
