from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src import schemas
from src.core.db import get_async_session
from src.models import Transaction

router = APIRouter()


@router.get('/{transaction_id}', response_model=schemas.Transaction)
async def get_transaction(
        transaction_id: str,
        session: AsyncSession = Depends(get_async_session)):
    try:
        transaction = await session.get(Transaction, transaction_id)
        if not transaction:
            raise HTTPException(status_code=404,
                                detail='Transaction not found')

        return schemas.Transaction(
            id='1fd3c0b8-07a4-40ad-a3d0-062b6a8aca0b',
            name=transaction.name,
            rate_type=transaction.rate_type,
            from_currency=transaction.from_currency,
            from_currency_network=transaction.from_currency_network,
            to_currency=transaction.to_currency,
            to_currency_network=transaction.to_currency_network,
            direction=transaction.direction,
            amount=transaction.amount,
            to_address=transaction.to_address,
            tag_value=transaction.tag_value,
            tag_name=transaction.tag_name,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f'Error retrieving transaction: {str(e)}')


@router.post('/' ) #, response_model=schemas.Transaction)
async def create_transaction(
    data: schemas.CreateTransaction,
    session: AsyncSession = Depends(get_async_session)
):
    return {'message': 'Transaction created'}
    try:
        transaction = Transaction(
            user_id='1fd3c0b8-07a4-40ad-a3d0-062b6a8aca0b',
            name=await Transaction.create_unique_name(session),
            rate_type=data.rate_type,
            from_currency=data.currency_from,
            from_currency_network=data.currency_from_network,
            to_currency=data.currency_to,
            to_currency_network=data.currency_to_network,
            direction=data.exchange_direction,
            amount=data.amount_value,
            to_address=data.wallet_address,
            tag_value=data.tag_value,
            tag_name=data.tag_name,
        )

        session.add(transaction)
        await session.commit()
        await session.refresh(transaction)

        return schemas.Transaction(
            name=transaction.name,
            status=transaction.status
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f'Error creating transaction: {str(e)}')
