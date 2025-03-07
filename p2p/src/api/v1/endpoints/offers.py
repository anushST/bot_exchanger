from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, func
from sqlalchemy.orm import selectinload
from src.models import Offer, Network, Deal, arbitrator_offer_networks
from src.api.v1.schemas.offer import (
    NetworkSchema, OfferCreateSchema, OfferUpdateSchema, OfferSchema,
    DealSchema, StatisticsSchema
)
from src.core.db import get_async_session
from uuid import UUID
from typing import List

offer_router = APIRouter()

async def get_current_arbitrator_id() -> UUID:
    return UUID("550e8400-e29b-41d4-a716-446655440000")

@offer_router.get("/networks", response_model=List[NetworkSchema])
async def get_available_networks(session: AsyncSession = Depends(get_async_session)):
    """Получить список доступных сетей (банков)"""
    result = await session.execute(select(Network).where(Network.is_active == True))
    networks = result.unique().scalars().all()  
    return networks

@offer_router.post("/offers", response_model=OfferSchema)
async def create_offer(
    offer_data: OfferCreateSchema,
    session: AsyncSession = Depends(get_async_session),
    arbitrator_id: UUID = Depends(get_current_arbitrator_id)
):
    """Создать новое предложение"""
    async with session.begin():
        existing_networks = await session.execute(
            select(Network.id).where(Network.id.in_(offer_data.network_ids))
        )
        existing_ids = {n.id for n in existing_networks.scalars()}
        missing = set(offer_data.network_ids) - existing_ids
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Сети не найдены: {', '.join(map(str, missing))}"
            )
        
        offer_dict = offer_data.dict(exclude={"network_ids"})
        offer_dict["arbitrator_id"] = arbitrator_id
        offer = Offer(**offer_dict)
        session.add(offer)
        await session.flush()
        
        await session.execute(
            arbitrator_offer_networks.insert(),
            [{"offer_id": offer.id, "network_id": nid} for nid in offer_data.network_ids]
        )
    
    await session.refresh(offer, attribute_names=['networks'])
    return offer

@offer_router.put("/offers/{offer_id}", response_model=OfferSchema)
async def update_offer(
    offer_id: UUID,
    offer_data: OfferUpdateSchema,
    session: AsyncSession = Depends(get_async_session),
    arbitrator_id: UUID = Depends(get_current_arbitrator_id)
):
    """Обновить предложение"""
    async with session.begin():
        offer = await session.execute(
            select(Offer)
            .where(Offer.id == offer_id)
            .where(Offer.arbitrator_id == arbitrator_id)
            .options(selectinload(Offer.networks))
        )
        offer = offer.scalars().first()
        if not offer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        
        update_data = offer_data.dict(exclude_unset=True, exclude={"network_ids"})
        if update_data:
            await session.execute(
                update(Offer)
                .where(Offer.id == offer_id)
                .values(**update_data)
            )
        
        if offer_data.network_ids is not None:
            existing = await session.execute(
                select(Network.id).where(Network.id.in_(offer_data.network_ids))
        )
        existing_ids = set(existing.scalars())  
        missing = set(offer_data.network_ids) - existing_ids
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Сети не найдены: {', '.join(map(str, missing))}"
            )
        
        await session.execute(
            delete(arbitrator_offer_networks).where(
                arbitrator_offer_networks.c.offer_id == offer_id
            )
        )
        await session.execute(
            arbitrator_offer_networks.insert(),
            [{"offer_id": offer_id, "network_id": nid} for nid in offer_data.network_ids]
        )
    
    await session.commit()
    await session.refresh(offer)
    return offer

@offer_router.delete("/offers/{offer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_offer(
    offer_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    arbitrator_id: UUID = Depends(get_current_arbitrator_id)
):
    """Удалить предложение"""
    async with session.begin():
        offer = await session.get(Offer, offer_id)
        if not offer or offer.arbitrator_id != arbitrator_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
        await session.delete(offer)

@offer_router.get("/offers", response_model=List[OfferSchema])
async def get_offers(
    session: AsyncSession = Depends(get_async_session),
    arbitrator_id: UUID = Depends(get_current_arbitrator_id)
):
    """Получить все предложения арбитражника"""
    result = await session.execute(
        select(Offer)
        .where(Offer.arbitrator_id == arbitrator_id)
        .options(selectinload(Offer.networks))
    )
    return result.scalars().all()

@offer_router.get("/deals", response_model=List[DealSchema])
async def get_deal_history(
    session: AsyncSession = Depends(get_async_session),
    arbitrator_id: UUID = Depends(get_current_arbitrator_id)
):
    """Получить историю сделок"""
    result = await session.execute(
        select(Deal)
        .where(Deal.arbitrator_id == arbitrator_id)
        .options(selectinload(Deal.offer)) 
    )
    deals = result.unique().scalars().all()
    return deals

@offer_router.get("/statistics", response_model=StatisticsSchema)
async def get_statistics(
    session: AsyncSession = Depends(get_async_session),
    arbitrator_id: UUID = Depends(get_current_arbitrator_id)
):
    """Получить статистику по сделкам"""
    result = await session.execute(
        select(
            func.count(Deal.id),
            func.sum(Deal.fiat_amount),
            func.sum(Deal.crypto_amount)
        ).where(Deal.arbitrator_id == arbitrator_id)
    )
    total_deals, total_fiat, total_crypto = result.one()
    return {
        "total_deals": total_deals,
        "total_fiat": float(total_fiat or 0),
        "total_crypto": float(total_crypto or 0)
    }