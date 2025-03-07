from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, and_, exists, desc, asc
from sqlalchemy.orm import aliased
import uuid
from src.models.user import Arbitrager
from src.models.currency import Currency
from src.core.db import get_async_session
from src.models.offer import Offer, OfferType
from sqlalchemy.ext.asyncio import AsyncSession
    
swaps_router = APIRouter()

@swaps_router.get("/", response_model=dict)
async def get_swaps_with_details(
    arbitrator_id: uuid.UUID | None = None,
    fiat_currency_id: uuid.UUID | None = None,
    crypto_currency_id: uuid.UUID | None = None,
    type: OfferType = None,  
    session: AsyncSession = Depends(get_async_session)
):
    if not type:
        raise HTTPException(status_code=400, detail="Параметр 'type' обязателен")
    
    # Условия для фильтрации
    filters = [
        Offer.is_active == True,
        Offer.type == type.value
    ]
    if arbitrator_id:
        filters.append(Offer.arbitrator_id == arbitrator_id)
    if fiat_currency_id:
        filters.append(Offer.fiat_currency_id == fiat_currency_id)
    if crypto_currency_id:
        filters.append(Offer.crypto_currency_id == crypto_currency_id)
    
    # Проверка существования предложений
    exists_query = await session.execute(
        select(exists().where(and_(*filters)))
    )
    if not exists_query.scalar():
        raise HTTPException(
            status_code=404, 
            detail=f"Предложений типа '{type.value}' с заданными фильтрами не найдено"
        )
    
    # Подзапрос с правильной сортировкой
    subquery = (
        select(Offer)
        .where(and_(*filters))
        .order_by(
            asc(Offer.price) if type == OfferType.BUY else desc(Offer.price)
        )
        .limit(1)
        .subquery()
    )

    # Алиас для криптовалюты
    crypto_currency_alias = aliased(Currency)

    # Основной запрос с использованием подзапроса
    query = (
        select(
            subquery.c.id,
            subquery.c.price,
            subquery.c.type,
            subquery.c.is_active,
            subquery.c.created_at,
            subquery.c.updated_at,
            
            Arbitrager.id.label("arbitrator_id"),
            
            Currency.id.label("fiat_currency_id"),
            Currency.name.label("fiat_currency_name"),
            Currency.code.label("fiat_currency_code"),
            
            crypto_currency_alias.id.label("crypto_currency_id"),
            crypto_currency_alias.name.label("crypto_currency_name"),
            crypto_currency_alias.code.label("crypto_currency_code"),
        )
        .join(Arbitrager, subquery.c.arbitrator_id == Arbitrager.id)
        .join(Currency, subquery.c.fiat_currency_id == Currency.id, isouter=True)
        .join(
            crypto_currency_alias,
            subquery.c.crypto_currency_id == crypto_currency_alias.id,
            isouter=True
        )
    )

    result = await session.execute(query)
    row = result.first()

    if not row:
        raise HTTPException(
            status_code=404, 
            detail=f"Свопы с типом '{type.value}' и указанными фильтрами не найдены"
        )

    return {
            "offer": {
                "id": str(row.id),
                "type": row.type,
                "price": float(row.price),
                "is_active": row.is_active,
                "created_at": row.created_at.isoformat(),
                "updated_at": row.updated_at.isoformat(),
            
            "arbitrator": {
                "id": str(row.arbitrator_id),
            },
            "fiat_currency": {
                "id": str(row.fiat_currency_id),
                "name": row.fiat_currency_name,
                "code": row.fiat_currency_code,
            },
            "crypto_currency": {
                "id": str(row.crypto_currency_id),
                "name": row.crypto_currency_name,
                "code": row.crypto_currency_code,
            }
        }
    }