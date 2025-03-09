import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.core.db import get_async_session
from src.models import Network
from src.api.v1.schemas import NetworkCreate, NetworkUpdate, NetworkResponse
from src.utils import PaginationParams, PaginatedResponse


router = APIRouter()


@router.post("/", response_model=NetworkResponse)
async def create_network(network: NetworkCreate,
                         session: AsyncSession = Depends(get_async_session)):
    db_network = Network(**network.model_dump())
    session.add(db_network)
    await session.commit()
    await session.refresh(db_network)
    return db_network


@router.get("/", response_model=PaginatedResponse[NetworkResponse])
async def get_networks(
    pagination: PaginationParams = Depends(),
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(
        select(Network).offset(pagination.offset).limit(pagination.limit))
    total = await session.execute(select(Network))
    return PaginatedResponse(
        total=len(total.unique().scalars().all()),
        items=result.unique().scalars().all())


@router.get("/{network_id}", response_model=NetworkResponse)
async def get_network(network_id: uuid.UUID,
                      session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(
        select(Network).where(Network.id == network_id))
    network = result.scalars().first()
    if not network:
        raise HTTPException(status_code=404, detail="Network not found")
    return network


@router.patch("/{network_id}", response_model=NetworkResponse)
async def update_network(network_id: uuid.UUID, network: NetworkUpdate,
                         session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(
        Network).where(Network.id == network_id))
    db_network = result.scalars().first()
    if not db_network:
        raise HTTPException(status_code=404, detail="Network not found")
    for key, value in network.model_dump(exclude_none=True).items():
        setattr(db_network, key, value)
    await session.commit()
    await session.refresh(db_network)
    return db_network


@router.delete("/{network_id}")
async def delete_network(network_id: uuid.UUID,
                         session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(
        select(Network).where(Network.id == network_id))
    db_network = result.scalars().first()
    if not db_network:
        raise HTTPException(status_code=404, detail="Network not found")
    await session.delete(db_network)
    await session.commit()
    return {"detail": "Network deleted"}
