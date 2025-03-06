from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.core.db import get_async_session
from src.models import Deal, User, Bank, Network, Currency
from src.enums import DealStatus
from src.api.v1.schemas.deal import CreateDealRequest, DealResponse
import uuid

deals_router = APIRouter()

@deals_router.post("/deals", response_model=DealResponse)
async def create_deal(
    request: CreateDealRequest,
    db: AsyncSession = Depends(get_async_session)
):
    buyer = await db.scalar(
        select(User).where(User.id == request.buyer_identifier)
    )
    if not buyer:
        raise HTTPException(status_code=404, detail="Покупатель не найден")

    fiat_currency = await db.scalar(
        select(Currency).where(Currency.code == request.fiat_currency_code)
    )
    if not fiat_currency:
        raise HTTPException(status_code=404, detail="Фиатная валюта не найдена")

    crypto_currency = await db.scalar(
        select(Currency).where(Currency.code == request.crypto_currency_code)
    )
    if not crypto_currency:
        raise HTTPException(status_code=404, detail="Криптовалюта не найдена")

    bank_id = None
    network_id = None
    if request.deal_type == "buy":
        if not request.bank_code:
            raise HTTPException(status_code=400, detail="bank_code обязателен для покупки")
        bank = await db.scalar(
            select(Bank).where(Bank.code == request.bank_code)
        )
        if not bank:
            raise HTTPException(status_code=404, detail="Банк не найден")
        bank_id = bank.id
    elif request.deal_type == "sell":
        if not request.network_code or not request.crypto_address:
            raise HTTPException(status_code=400, detail="network_code и crypto_address обязательны для продажи")
        network = await db.scalar(
            select(Network).where(Network.code == request.network_code)
        )
        if not network:
            raise HTTPException(status_code=404, detail="Сеть не найдена")
        if crypto_currency not in network.currencies:
            raise HTTPException(status_code=400, detail="Сеть не поддерживает эту криптовалюту")
        network_id = network.id

    crypto_amount = request.fiat_amount / request.price

    arbitrator_id = uuid.UUID(request.arbitrator_id) if request.arbitrator_id else None

    deal = Deal(
        buyer_id=buyer.id,
        arbitrator_id=arbitrator_id,
        arbitrator_offer_id=None,
        fiat_currency_id=fiat_currency.id,
        crypto_currency_id=crypto_currency.id,
        fiat_amount=request.fiat_amount,
        crypto_amount=crypto_amount,
        bank_id=bank_id,
        network_id=network_id,
        crypto_address=request.crypto_address if request.deal_type == "sell" else None,
        status=DealStatus.PENDING
    )

    db.add(deal)
    await db.commit()
    await db.refresh(deal)

    return deal