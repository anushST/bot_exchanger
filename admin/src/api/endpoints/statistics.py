import logging
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum

from fastapi import Depends, Query, HTTPException
from fastapi.routing import APIRouter
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.core.db import get_async_session
from src.models import (
    MarketingLink, MarketingLinkUser, Transaction, User,
    TransactionStatuses)

logger = logging.getLogger(__name__)

router = APIRouter()


class PeriodEnum(str, Enum):
    day = "day"
    month = "month"
    year = "year"
    all_time = "all_time"


def aggregate_object(objects, period: PeriodEnum, need_objs=False):
    if need_objs:
        aggregation = defaultdict(list)
    else:
        aggregation = defaultdict(int)

    for txn in objects:
        ts: datetime = txn.created_at

        if period == PeriodEnum.day:
            key = ts.date()
        elif period == PeriodEnum.month:
            key = f'{ts.year}-{ts.month}'
        elif period == PeriodEnum.year:
            key = f'{ts.year}'
        elif period == PeriodEnum.all_time:
            key = 'all_time'
        else:
            raise ValueError("Неверный период. Используйте: 'day', 'week', "
                             "'month', 'year'")
        if need_objs:
            aggregation[key].append(txn)
        else:
            aggregation[key] += 1

    return dict(sorted(aggregation.items(), reverse=True))


async def get_marketing_link_users(link_name, session: AsyncSession):
    stmt = select(MarketingLink).where(MarketingLink.name == link_name)
    result = await session.execute(stmt)
    marketing_link = result.scalars().first()

    if not marketing_link:
        return []

    stmt = select(MarketingLinkUser.user_id).where(
        MarketingLinkUser.marketing_link_id == marketing_link.id)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/statistics/exchange-volume")
async def get_exchange_volume(
        period: PeriodEnum = Query(default=PeriodEnum.day),
        marketing_link_name: str = None,
        db: AsyncSession = Depends(get_async_session)):
    """
    Ежедневный, недельный, месячный объем обменов
    (сумма amount по транзакциям).
    /statistics/exchange-volume?period=day|week|month
    """

    stmt = (
        select(Transaction)
        .where(Transaction.status == TransactionStatuses.DONE.value)
    )

    if marketing_link_name:
        user_ids = await get_marketing_link_users(
            marketing_link_name, db) or []
        stmt = stmt.where(Transaction.user_id.in_(user_ids))

    result = await db.execute(stmt)
    transactions = result.scalars().all() or 0
    chart_data = None
    if transactions:
        chart_data = aggregate_object(transactions, period)

    return {
        'period': period,
        'data': chart_data or []
    }


@router.get("/statistics/new-users")
async def get_new_users(period: PeriodEnum = Query(default=PeriodEnum.day),
                        marketing_link_name: str = None,
                        db: AsyncSession = Depends(get_async_session)):
    """
    Новые пользователи за период.
    """
    stmt = select(User)
    if marketing_link_name:
        user_ids = await get_marketing_link_users(
            marketing_link_name, db) or []
        stmt = stmt.where(User.id.in_(user_ids))

    result = await db.execute(stmt)
    users = result.scalars().all() or 0
    chart_data = None
    if users:
        chart_data = aggregate_object(users, period)

    return {
        'period': period,
        'data': chart_data or []
    }


@router.get("/statistics/active-users")
async def get_active_users(
    period: PeriodEnum = Query(default=PeriodEnum.day),
    marketing_link_name: str = None,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Активные пользователи (совершившие хотя бы 1 транзакцию) за период.
    """

    stmt = (
        select(Transaction)
        .where(Transaction.status == TransactionStatuses.DONE.value)
    )

    if marketing_link_name:
        user_ids = await get_marketing_link_users(
            marketing_link_name, db) or []
        stmt = stmt.where(Transaction.user_id.in_(user_ids))

    result = await db.execute(stmt)
    transactions = result.scalars().all() or 0
    if transactions:
        chart_data = aggregate_object(transactions, period, need_objs=True)

    for date, data in chart_data.items():
        unique_users = set()
        for d in data:
            unique_users.add(d.user_id)
        chart_data[date] = len(unique_users)

    return {
        'period': period,
        'data': chart_data or []
    }


@router.get("/statistics/average-transaction-amount")
async def get_average_transaction_amount(
    period: PeriodEnum = Query(default=PeriodEnum.day),
    marketing_link_name: str = None,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Средняя стоимость транзакции = сумма транзакций / кол-во
    транзакций за период.
    """
    stmt = (
        select(Transaction)
        .where(Transaction.status == TransactionStatuses.DONE.value)
    )

    if marketing_link_name:
        user_ids = await get_marketing_link_users(
            marketing_link_name, db) or []
        stmt = stmt.where(Transaction.user_id.in_(user_ids))

    result = await db.execute(stmt)
    transactions = result.scalars().all() or 0
    if transactions:
        chart_data = aggregate_object(transactions, period, need_objs=True)

    for date, data in chart_data.items():
        transaction_total_value = Decimal('0')
        for d in data:
            transaction_total_value += d.amount
        chart_data[date] = transaction_total_value / Decimal(len(data))

    return {
        'period': period,
        'data': chart_data or []
    }


@router.get("/statistics/arpu")
async def get_arpu(
        period: PeriodEnum = Query(default=PeriodEnum.day),
        marketing_link_name: str = None,
        db: AsyncSession = Depends(get_async_session)):
    """
    ARPU = Общий доход / кол-во пользователей
    Предположим, что доход = сумма комиссий с транзакций (пример).
    В реальности нужно уточнить, как именно считается "доход".
    """

    stmt = (
        select(Transaction)
        .where(Transaction.status == TransactionStatuses.DONE.value)
    )

    if marketing_link_name:
        user_ids = await get_marketing_link_users(
            marketing_link_name, db) or []
        stmt = stmt.where(Transaction.user_id.in_(user_ids))

    result = await db.execute(stmt)
    transactions = result.scalars().all() or 0
    if transactions:
        chart_data = aggregate_object(transactions, period, need_objs=True)

    stmt_users = select(func.count(User.id))
    result_users = await db.execute(stmt_users)
    total_users = result_users.scalar() or 0

    for date, data in chart_data.items():
        transaction_total_value = Decimal('0')
        for d in data:
            transaction_total_value += d.amount
        chart_data[date] = transaction_total_value / total_users

    return {
        'period': period,
        'data': chart_data or []
    }


@router.get("/statistics/retention-churn")
async def get_retention_churn(
        period_1: int = 30, period_2: int = 14,
        marketing_link_name: str = None,
        db: AsyncSession = Depends(get_async_session)):
    """
    Например, возьмём период N (в днях) и посмотрим,
    сколько пользователей вернулись/не вернулись.
    Для упрощённого примера:
      - RetentionRate = (кол-во пользователей, пришедших в период 1, которые
      активны в период 2) / (кол-во пользователей, пришедших в период 1)
      - ChurnRate = 1 - RetentionRate
    """
    if period_1 <= period_2:
        raise HTTPException(400, 'Period_1 can"t be less or equal to period_2')
    now = datetime.now()
    one_month_ago = now - timedelta(days=period_1)
    two_weeks_ago = now - timedelta(days=period_2)

    stmt = (
        select(User)
        .where(User.created_at < one_month_ago)
    )
    if marketing_link_name:
        user_ids = await get_marketing_link_users(
            marketing_link_name, db) or []
        stmt = stmt.where(User.id.in_(user_ids))
    result_registered_month_ago = await db.execute(stmt)
    users_registered_month_ago = result_registered_month_ago.scalars().all()
    count_month_ago = len(users_registered_month_ago)

    retained_users = [
        u for u in users_registered_month_ago
        if u.last_active_at and u.last_active_at > two_weeks_ago
    ]
    count_retained = len(retained_users)

    retention_rate = 0.0
    churn_rate = 0.0

    if count_month_ago > 0:
        retention_rate = count_retained / count_month_ago
        churn_rate = 1 - retention_rate

    return {
        "retention_rate": f"{retention_rate * 100:.2f}%",
        "churn_rate": f"{churn_rate * 100:.2f}%"
    }


@router.get("/statistics/transaction-completion-rate")
async def get_transaction_completion_rate(
    period: PeriodEnum = Query(default=PeriodEnum.day),
    marketing_link_name: str = None,
    db: AsyncSession = Depends(get_async_session)
):
    """
    % успешно завершённых транзакций (status="done")
    относительно всех начатых (status="started" или других).
    """
    stmt = select(Transaction)

    if marketing_link_name:
        user_ids = await get_marketing_link_users(
            marketing_link_name, db) or []
        stmt = stmt.where(Transaction.user_id.in_(user_ids))

    result_started = await db.execute(stmt)
    transactions = result_started.scalars().all() or 0

    if transactions:
        chart_data = aggregate_object(transactions, period, need_objs=True)

    for date, data in chart_data.items():
        done_transactions = 0
        for d in data:
            if d.status == TransactionStatuses.DONE.value:
                done_transactions += 1
        chart_data[date] = done_transactions / len(data)

    return {
        'period': period,
        'data': chart_data or []
    }
