import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.core.db import get_async_session
from src.models import Currency, Network
from src.api.v1.schemas import CurrencyCreate, CurrencyResponse, CurrencyUpdate
from src.enums import CurrencyType
from src.utils import PaginationParams, PaginatedResponse

router = APIRouter()


@router.post("/", response_model=CurrencyResponse)
async def create_currency(currency: CurrencyCreate,
                          session: AsyncSession = Depends(get_async_session)):
    try:
        db_currency = Currency(**currency.model_dump(exclude={"network_ids"}))
        session.add(db_currency)
        await session.commit()
        await session.refresh(db_currency)
        if currency.network_ids and currency.type == CurrencyType.CRYPTO:
            result = await session.execute(
                select(Network).where(Network.id.in_(currency.network_ids)))
            networks = result.unique().scalars().all()
            if not networks:
                raise HTTPException(
                    400, 'Please select Networks'
                )
            db_currency.networks = networks
            await session.commit()
            await session.refresh(db_currency)
        return db_currency
    except IntegrityError:
        raise HTTPException(
            400, detail='The currency with code already exists.')


@router.get("/", response_model=PaginatedResponse[CurrencyResponse])
async def get_currencies(
    pagination: PaginationParams = Depends(),
    session: AsyncSession = Depends(get_async_session)
):
    total_result = await session.execute(select(Currency))
    total = len(total_result.unique().scalars().all())
    result = await session.execute(
        select(Currency).offset(pagination.offset).limit(pagination.limit))
    return PaginatedResponse(
        total=total, items=result.unique().scalars().all()
    )


@router.get("/{currency_id}", response_model=CurrencyResponse)
async def get_currency(currency_id: uuid.UUID,
                       session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(
        select(Currency).where(Currency.id == currency_id))
    currency = result.scalars().first()
    if not currency:
        raise HTTPException(status_code=404, detail="Currency not found")
    return currency


@router.patch("/{currency_id}", response_model=CurrencyResponse)
async def update_currency(currency_id: uuid.UUID,
                          currency: CurrencyUpdate,
                          session: AsyncSession = Depends(get_async_session)):
    try:
        result = await session.execute(
            select(Currency).where(Currency.id == currency_id))
        db_currency = result.scalars().first()
        if not db_currency:
            raise HTTPException(status_code=404, detail="Currency not found")
        for key, value in currency.model_dump(
                exclude={"network_ids"}, exclude_none=True).items():
            setattr(db_currency, key, value)
        if currency.network_ids:
            result = await session.execute(select(Network).where(
                Network.id.in_(currency.network_ids)))
            db_currency.networks = result.unique().scalars().all()
        await session.commit()
        await session.refresh(db_currency)
        return db_currency
    except IntegrityError:
        raise HTTPException(
            400, detail='The currency with code already exists.')


@router.delete("/{currency_id}")
async def delete_currency(currency_id: uuid.UUID,
                          session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(Currency
                                          ).where(Currency.id == currency_id))
    db_currency = result.scalars().first()
    if not db_currency:
        raise HTTPException(status_code=404, detail="Currency not found")
    await session.delete(db_currency)
    await session.commit()
    return {"detail": "Currency deleted"}
