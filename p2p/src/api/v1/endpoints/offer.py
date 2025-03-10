import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.core.db import get_async_session
from src.models import Arbitrager, Network, Offer, Bank, Currency
from src.api.v1.schemas import OfferCreate, OfferResponse, OfferUpdate
from src.enums import CurrencyType
from src.utils import (
    get_arbitrager, PaginationParams, PaginatedResponse
)

router = APIRouter()


async def validate_offer_data(offer, session: AsyncSession):
    if offer.fiat_currency_id:
        result = await session.execute(
            select(Currency)
            .where((Currency.id == offer.fiat_currency_id) &
                   (Currency.type == CurrencyType.FIAT.value))
        )
        if not result.scalars().first():
            raise HTTPException(
                status_code=400,
                detail=f"Fiat currency not found: {offer.fiat_currency_id}"
            )
    if offer.crypto_currency_id:
        result = await session.execute(
            select(Currency)
            .where((Currency.id == offer.crypto_currency_id) &
                   (Currency.type == CurrencyType.CRYPTO.value))
        )
        if not result.scalars().first():
            raise HTTPException(
                status_code=400,
                detail=f"Crypto currency not found: {offer.crypto_currency_id}"
            )


@router.post("/offers/", response_model=OfferResponse)
async def create_offer(
    offer: OfferCreate, arbitrager: Arbitrager = Depends(get_arbitrager),
    session: AsyncSession = Depends(get_async_session)
):
    await validate_offer_data(offer, session)

    result = await session.execute(
        select(Network).where(Network.id.in_(offer.network_ids)))
    networks = result.unique().scalars().all()
    if not networks:
        raise HTTPException(
            400, 'Networks not found. Select networks'
        )

    result = await session.execute(
        select(Bank).where(Bank.id.in_(offer.bank_ids)))
    banks = result.unique().scalars().all()
    if not banks:
        raise HTTPException(
            400, 'Banks not found. Select banks'
        )

    db_offer = Offer(
        arbitrager_id=arbitrager.id,
        **offer.model_dump(exclude={'network_ids', 'bank_ids'})
    )
    db_offer.networks = networks
    db_offer.banks = banks
    session.add(db_offer)
    await session.commit()
    await session.refresh(db_offer)
    return db_offer


@router.get("/offers/", response_model=PaginatedResponse[OfferResponse])
async def get_offers(
    pagination: PaginationParams = Depends(),
    session: AsyncSession = Depends(get_async_session),
):
    total_result = await session.execute(select(Offer))
    total = len(total_result.unique().scalars().all())
    result = await session.execute(
        select(Offer).offset(pagination.offset).limit(pagination.limit))
    return PaginatedResponse(
        total=total, items=result.unique().scalars().all()
    )


@router.get("/offers/{offer_id}", response_model=OfferResponse)
async def get_offer(offer_id: uuid.UUID,
                    session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(
        select(Offer).where(Offer.id == offer_id))
    offer = result.scalars().first()
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    return offer


@router.patch("/offers/{offer_id}", response_model=OfferResponse)
async def update_offer(
    offer_id: uuid.UUID, offer: OfferUpdate,
    session: AsyncSession = Depends(get_async_session),
    arbitrager: Arbitrager = Depends(get_arbitrager)
):
    result = await session.execute(
        select(Offer)
        .where((Offer.id == offer_id) & (Offer.arbitrager_id == arbitrager.id))
    )
    db_offer = result.scalars().first()
    if not db_offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    await validate_offer_data(db_offer, session)

    for key, value in offer.model_dump(
            exclude={"network_ids", 'bank_ids'},
            exclude_none=True).items():
        setattr(db_offer, key, value)

    if offer.network_ids:
        result = await session.execute(
            select(Network).where(Network.id.in_(offer.network_ids)))
        networks = result.unique().scalars().all()
        if not networks:
            raise HTTPException(
                400, 'Networks not found. Select networks'
            )
        db_offer.networks = networks

    if offer.bank_ids:
        result = await session.execute(
            select(Bank).where(Bank.id.in_(offer.bank_ids)))
        banks = result.unique().scalars().all()
        if not banks:
            raise HTTPException(
                400, 'Banks not found. Select banks'
            )
        db_offer.banks = banks
    await session.commit()
    await session.refresh(db_offer)

    return db_offer


@router.delete("/offers/{offer_id}")
async def delete_offer(
    offer_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    arbitrager: Arbitrager = Depends(get_arbitrager)
):
    result = await session.execute(
        select(Offer)
        .where(Offer.id == offer_id & Offer.arbitrator_id == arbitrager.id)
    )
    db_offer = result.scalars().first()
    if not db_offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    await session.delete(db_offer)
    await session.commit()
    return {"detail": "Offer deleted"}
