import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from src.core.db import get_async_session
from src.models import Arbitrager, Deal, Offer, User, Bank, Network
from src.api.v1.schemas import DealCreate, DealResponse
from src.enums import DirectionTypes, OfferType, UserRole
from src.utils import get_current_user, PaginatedResponse, PaginationParams

router = APIRouter()


@router.post("/", response_model=DealResponse)
async def create_deal(
    deal: DealCreate, session: AsyncSession = Depends(get_async_session),
    user: User = Depends(get_current_user)
):
    result = await session.execute(
        select(Offer).where(Offer.id == deal.arbitrator_offer_id))
    offer = result.scalars().first()
    if not offer:
        raise HTTPException(
            400, 'Offer not found please check data'
        )

    if user.id == offer.arbitrager.user.id:
        raise HTTPException(
            400, 'You can not make deal on your offer'
        )

    result = await session.execute(
        select(Bank).where(Bank.id == deal.bank_id))
    bank = result.scalars().first()

    if not bank:
        raise HTTPException(status_code=400, detail="Bank not found")
    if bank.id not in [b.id for b in offer.banks]:
        raise HTTPException(status_code=400, detail="Bank not found")

    result = await session.execute(
        select(Network).where(Network.id == deal.network_id))
    network = result.scalars().first()

    if not network:
        raise HTTPException(status_code=400, detail="Network not found")
    if network.id not in [n.id for n in offer.networks]:
        raise HTTPException(status_code=400, detail="Network not found")

    if deal.direction == DirectionTypes.CRYPTO:
        fiat_amount = deal.amount * offer.price
        crypto_amount = deal.amount
    elif deal.direction == DirectionTypes.FIAT:
        fiat_amount = deal.amount
        crypto_amount = deal.amount / offer.price
    else:
        raise Exception('Error')

    db_deal = Deal(
        buyer_id=user.id,
        arbitrager_offer_id=offer.id,
        crypto_amount=crypto_amount,
        fiat_amount=fiat_amount,
        bank_id=bank.id,
        network_id=network.id
    )
    session.add(db_deal)
    await session.commit()
    await session.refresh(db_deal)
    return db_deal


@router.get("/", response_model=PaginatedResponse[DealResponse])
async def get_deals(
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(get_current_user),
    pagination: PaginationParams = Depends()
):
    query = (select(Deal)
             .where((Deal.buyer_id == user.id) | (Deal.offer.has(
                     Offer.arbitrager.has(Arbitrager.user_id == user.id))))
             .options(joinedload(Deal.offer).joinedload(Offer.arbitrager)))
    total_result = await session.execute(query)
    total = len(total_result.unique().scalars().all())
    result = await session.execute(
        query.offset(pagination.offset).limit(pagination.limit))
    return {"total": total, "items": result.unique().scalars().all()}


@router.get("/{deal_id}", response_model=DealResponse)
async def get_deal(
    deal_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(get_current_user)
):
    result = await session.execute(
        select(Deal)
        .where(
            (Deal.id == deal_id) &
            ((Deal.buyer_id == user.id) |
             (Deal.offer.has(
                 Offer.arbitrager.has(Arbitrager.user_id == user.id))))
        )
        .options(joinedload(Deal.offer).joinedload(Offer.arbitrager))
    )
    deal = result.scalars().first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal


@router.patch('/confirm-pay/{deal_id}')
async def confirm_deal(
    deal_id: uuid.UUID, session: AsyncSession = Depends(get_async_session),
    user: User = Depends(get_current_user)
):
    result = await session.execute(select(Deal).where(Deal.id == deal_id))
    deal = result.scalars().first()

    not_found = HTTPException(status_code=404, detail="Deal not found")

    if not deal:
        raise not_found

    if user.role == UserRole.ARBITRAGER.value:
        if (user.id != deal.offer.arbitrager.user.id
                and user.id != deal.buyer_id):
            raise not_found
    elif user.role == UserRole.USER.value:
        if user.id != deal.buyer_id:
            raise not_found

    if deal.offer.type == OfferType.BUY.value:
        if (user.role == UserRole.ARBITRAGER.value
                and not deal.is_buyer_confirmed):
            raise HTTPException(400, 'Buyer did not confirm yet.')
        if user.role == UserRole.ARBITRAGER.value:
            deal.is_arbitrager_confirmed = True
        if user.role == UserRole.USER.value:
            deal.is_buyer_confirmed = True
    elif deal.offer.type == OfferType.SELL.value:
        if (user.role == UserRole.USER.value
                and not deal.is_arbitrager_confirmed):
            raise HTTPException(400, 'Arbitrager did not confirm yet.')
        if user.role == UserRole.ARBITRAGER.value:
            deal.is_arbitrager_confirmed = True
        if user.role == UserRole.USER.value:
            deal.is_buyer_confirmed = True
    else:
        raise Exception('Incorrect type')

    await session.commit()
    await session.refresh(deal)
    return {'deatail': 'Successfully confirmed'}
