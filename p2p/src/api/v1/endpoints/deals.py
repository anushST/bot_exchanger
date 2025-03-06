from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.core.db import get_async_session
from src.models import Deal, User, Currency, Bank, Network, Arbitrager
from src.api.v1.schemas.deal import CreateDealRequest, DealResponse
import uuid

deals_router = APIRouter()

@deals_router.post("/deals", response_model=DealResponse)
async def create_deal(request: CreateDealRequest, db: AsyncSession = Depends(get_async_session)):
    buyer = await db.scalar(select(User).where(User.id == request.buyer_identifier))
    if not buyer:
        raise HTTPException(status_code=404, detail="Покупатель не найден")

    fiat_currency = await db.scalar(select(Currency).where(Currency.code == request.fiat_currency_code))
    if not fiat_currency:
        raise HTTPException(status_code=404, detail="Фиатная валюта не найдена")

    crypto_currency = await db.scalar(select(Currency).where(Currency.code == request.crypto_currency_code))
    if not crypto_currency:
        raise HTTPException(status_code=404, detail="Криптовалюта не найдена")

    bank = None
    if request.bank_code:
        bank = await db.scalar(select(Bank).where(Bank.code == request.bank_code))
        if not bank:
            raise HTTPException(status_code=404, detail="Банк не найден")

    network = None
    if request.network_code:
        network = await db.scalar(select(Network).where(Network.code == request.network_code))
        if not network:
            raise HTTPException(status_code=404, detail="Сеть не найдена")

    arbitrator = None
    if request.arbitrator_id:
        try:
            arbitrator_id = uuid.UUID(request.arbitrator_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Некорректный UUID для арбитражника")
        arbitrator = await db.scalar(select(Arbitrager).where(Arbitrager.id == arbitrator_id))
        if not arbitrator:
            raise HTTPException(status_code=404, detail="Арбитражник не найден")

    crypto_amount = request.fiat_amount / request.price

    deal = Deal(
        buyer_id=buyer.id,
        arbitrator_id=arbitrator.id if arbitrator else None,
        fiat_currency_id=fiat_currency.id,
        crypto_currency_id=crypto_currency.id,
        fiat_amount=request.fiat_amount,
        crypto_amount=crypto_amount,
        bank_id=bank.id if bank else None,
        network_id=network.id if network else None,
        crypto_address=request.crypto_address,
        status="PENDING"
    )

    db.add(deal)
    await db.commit()
    await db.refresh(deal)

    return deal