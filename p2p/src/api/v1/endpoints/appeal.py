import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from src.core.db import get_async_session
from src.models import Appeal, Arbitrager, Deal, Offer, User
from src.api.v1.schemas import AppealCreate, AppealResponse
from src.enums import AppealStatus, DealStatus
from src.utils import (
    get_current_user, get_moderator, PaginatedResponse, PaginationParams
)

router = APIRouter()


async def get_deal_by_id(session: AsyncSession, deal_id, user_id):
    result = await session.execute(
            select(Deal)
            .where(
                (Deal.id == deal_id) &
                ((Deal.buyer_id == user_id) |
                 (Deal.offer.has(
                     Offer.arbitrager.has(Arbitrager.user_id == user_id))))
            )
            .options(joinedload(Deal.offer).joinedload(Offer.arbitrager))
        )
    deal = result.scalars().first()
    return deal


@router.post('/{deal_id}', response_model=AppealResponse)
async def appeal_crate(
    appeal: AppealCreate, session: AsyncSession = Depends(get_async_session),
    user: User = Depends(get_current_user)
):
    not_found = HTTPException(status_code=404, detail="Deal not found")

    deal = await get_deal_by_id(session, appeal.deal_id, user.id)

    if not deal:
        raise not_found

    # if user.role == UserRole.ARBITRAGER.value:
    #     if (user.id != deal.offer.arbitrager.user.id
    #             and user.id != deal.buyer_id):
    #         raise not_found
    # elif user.role == UserRole.USER.value:
    #     if user.id != deal.buyer_id:
    #         raise not_found

    if deal.status == DealStatus.CANCELED.value:
        raise HTTPException(400, 'Deal has ben canceled')

    if deal.status == DealStatus.APPEAL.value:
        raise HTTPException(400, 'It was already sent to appeal')

    if deal.status == DealStatus.COMPLETED.value:
        raise HTTPException(400, 'Deal already completed')

    if not (deal.is_arbitrager_confirmed or deal.is_buyer_confirmed):
        raise HTTPException(400, 'Can not make appeal at this stage')

    appeal_obj = Appeal(
        deal_id=deal.id,
        requested_by_id=user.id,
        reason=appeal.reason
    )
    session.add(appeal_obj)

    deal.status = DealStatus.APPEAL.value

    await session.commit()
    await session.refresh(appeal_obj)
    return appeal_obj


@router.get("/", response_model=PaginatedResponse[AppealResponse])
async def get_appeals(
    session: AsyncSession = Depends(get_async_session),
    moderator: User = Depends(get_moderator),
    pagination: PaginationParams = Depends()
):
    query = select(Appeal)
    total_result = await session.execute(query)
    total = len(total_result.unique().scalars().all())
    result = await session.execute(
        query.offset(pagination.offset).limit(pagination.limit))
    return PaginatedResponse(
        total=total, items=result.unique().scalars().all()
    )


@router.get("/{appeal_id}", response_model=AppealResponse)
async def get_appeal(
    appeal_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    moderator: User = Depends(get_moderator)
):
    query = select(Appeal).where(Appeal.id == appeal_id)
    result = await session.execute(query)
    appeal = result.scalars().first()

    if not appeal:
        raise HTTPException(status_code=404, detail="Appeal not found")
    return appeal


@router.get("/mark_as_resolved/{appeal_id}", response_model=AppealResponse)
async def mark_appeal_as_resolved(
    appeal_id: uuid.UUID,
    session: AsyncSession = Depends(get_async_session),
    moderator: User = Depends(get_moderator)
):
    query = select(Appeal).where(Appeal.id == appeal_id)
    result = await session.execute(query)
    appeal = result.scalars().first()

    if not appeal:
        raise HTTPException(status_code=404, detail="Appeal not found")

    appeal.status = AppealStatus.RESOLVED.value
    await session.commit()
    await session.refresh(appeal)
    return appeal
