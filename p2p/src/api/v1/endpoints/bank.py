import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select

from src.core.db import get_async_session
from src.models import Bank
from src.api.v1.schemas import BankCreate, BankResponse, BankUpdate
from src.utils import PaginationParams, PaginatedResponse

router = APIRouter()


@router.post("/banks/", response_model=BankResponse)
async def create_bank(bank: BankCreate,
                      session: AsyncSession = Depends(get_async_session)):
    try:
        db_bank = Bank(**bank.model_dump())
        session.add(db_bank)
        await session.commit()
        await session.refresh(db_bank)
        return db_bank
    except IntegrityError:
        raise HTTPException(
            400, detail='The currency with code already exists.')


@router.get("/banks/", response_model=PaginatedResponse[BankResponse])
async def get_banks(
    pagination: PaginationParams = Depends(),
    session: AsyncSession = Depends(get_async_session)
):
    total_result = await session.execute(select(Bank))
    total = len(total_result.unique().scalars().all())
    result = await session.execute(
        select(Bank).offset(pagination.offset).limit(pagination.limit))
    return PaginatedResponse(
        total=total, items=result.unique().scalars().all()
    )


@router.get("/banks/{bank_id}", response_model=BankResponse)
async def get_bank(bank_id: uuid.UUID,
                   session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(Bank).where(Bank.id == bank_id))
    bank = result.scalars().first()
    if not bank:
        raise HTTPException(status_code=404, detail="Bank not found")
    return bank


@router.patch("/banks/{bank_id}", response_model=BankResponse)
async def update_bank(bank_id: uuid.UUID, bank: BankUpdate,
                      session: AsyncSession = Depends(get_async_session)):
    try:
        result = await session.execute(select(Bank).where(Bank.id == bank_id))
        db_bank = result.scalars().first()
        if not db_bank:
            raise HTTPException(status_code=404, detail="Bank not found")
        for key, value in bank.model_dump().items():
            setattr(db_bank, key, value)
        await session.commit()
        return db_bank
    except IntegrityError:
        raise HTTPException(
            400, detail='The currency with code already exists.')


@router.delete("/banks/{bank_id}")
async def delete_bank(bank_id: uuid.UUID,
                      session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(Bank).where(Bank.id == bank_id))
    db_bank = result.scalars().first()
    if not db_bank:
        raise HTTPException(status_code=404, detail="Bank not found")
    await session.delete(db_bank)
    await session.commit()
    return {"detail": "Bank deleted"}
