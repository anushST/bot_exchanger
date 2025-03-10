import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from typing import List
from src.core.db import get_async_session
from src.models import Currency, Network, Offer, Deal
from src.api.v1.schemas import DealCreate, DealResponse

router = APIRouter()


@router.post("/deals/", response_model=DealResponse)
async def create_deal(deal: DealCreate, session: AsyncSession = Depends(get_async_session)):
    db_deal = Deal(**deal.dict())
    session.add(db_deal)
    await session.commit()
    await session.refresh(db_deal)
    return db_deal

@router.get("/deals/", response_model=List[DealResponse])
async def get_deals(
    session: AsyncSession = Depends(get_async_session),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    total_result = await session.execute(select(Deal))
    total = len(total_result.scalars().all())
    result = await session.execute(select(Deal).options(
        joinedload(Deal.buyer),
        joinedload(Deal.arbitrator),
        joinedload(Deal.fiat_currency),
        joinedload(Deal.crypto_currency),
        joinedload(Deal.bank),
        joinedload(Deal.network),
        joinedload(Deal.offer)
    ).offset(offset).limit(limit))
    return {"total": total, "items": result.scalars().all()}

@router.get("/deals/{deal_id}", response_model=DealResponse)
async def get_deal(deal_id: uuid.UUID, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(Deal).options(
        joinedload(Deal.buyer),
        joinedload(Deal.arbitrator),
        joinedload(Deal.fiat_currency),
        joinedload(Deal.crypto_currency),
        joinedload(Deal.bank),
        joinedload(Deal.network),
        joinedload(Deal.offer)
    ).where(Deal.id == deal_id))
    deal = result.scalars().first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal

@router.put("/deals/{deal_id}", response_model=DealResponse)
async def update_deal(deal_id: uuid.UUID, deal: DealCreate, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(Deal).where(Deal.id == deal_id))
    db_deal = result.scalars().first()
    if not db_deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    for key, value in deal.dict().items():
        setattr(db_deal, key, value)
    await session.commit()
    return db_deal
