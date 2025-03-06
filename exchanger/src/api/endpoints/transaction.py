import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api import schemas
from src.core.db import get_async_session
from src.models import RateTypes, Transaction, TransactionStatuses

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
            select(Transaction).where(
                Transaction.user_id == '2597d58d-0e85-48c1-a179-9b627b2d0e5a')
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
            status_code=500, detail=f'Error retrieving transactions: {str(e)}')


@router.get('/{transaction_id}')
async def get_transaction(
        transaction_id: str,
        session: AsyncSession = Depends(get_async_session)):
    try:
        result = await session.execute(
            select(Transaction).where(Transaction.name == transaction_id)
        )
        transaction = result.scalars().first()
        if not transaction:
            raise HTTPException(status_code=404,
                                detail='Transaction not found')
        if transaction.status == TransactionStatuses.NEW.value:
            return {'detail': 'Transaction is not processed yet'}
        elif transaction.status == TransactionStatuses.ERROR.value:
            return {'detail': 'Transaction finished with error',
                    'code': transaction.status_code}
        return schemas.Transaction(
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


@router.post('/')
async def create_transaction(
    data: schemas.CreateTransaction,
    session: AsyncSession = Depends(get_async_session)
):
    try:
        rate_type = data.rate_type
        refund_address = data.refund_address

        if rate_type == RateTypes.FIXED:
            if not refund_address:
                raise HTTPException(
                    status_code=400,
                    detail='Return address is required for FIXED rate type'
                )

        transaction = Transaction(
            user_id='2597d58d-0e85-48c1-a179-9b627b2d0e5a',
            name=await Transaction.create_unique_name(session),
            rate_type=data.rate_type.value,
            from_currency=data.currency_from,
            from_currency_network=data.currency_from_network,
            to_currency=data.currency_to,
            to_currency_network=data.currency_to_network,
            direction=data.exchange_direction.value,
            amount=data.amount_value,
            to_address=data.wallet_address,
            tag_value=data.tag_value,
            refund_address=data.refund_address,
            refund_tag_value=data.refund_tag_value
        )

        session.add(transaction)
        await session.commit()
        await session.refresh(transaction)

        return {'id': transaction.name}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(e, exc_info=True)
        raise HTTPException(
            status_code=500, detail=f'Error creating transaction: {str(e)}')
