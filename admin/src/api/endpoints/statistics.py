import logging
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum

from fastapi import Depends, Query, Request
from fastapi.routing import APIRouter
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from .utils import get_period_range
from src.core.db import get_async_session
from src.models import Transaction, User, TransactionStatuses

logger = logging.getLogger(__name__)

router = APIRouter()


class PeriodEnum(str, Enum):
    day = "day"
    week = "week"
    month = "month"
    year = "year"


@router.get("/statistics/exchange-volume")
async def get_exchange_volume(
        request: Request,
        period: PeriodEnum = Query(default=PeriodEnum.day),
        db: AsyncSession = Depends(get_async_session)):
    """
    Ежедневный, недельный, месячный объем обменов
    (сумма amount по транзакциям).
    /statistics/exchange-volume?period=day|week|month
    """
    telegram_initdata = request.headers.get('X-Telegram-Initdata',
                                            'Not Provided')

    logger.info(f'X-Telegram-InitData: {telegram_initdata}')
    start, end = get_period_range(period)

    stmt = (
        select(func.sum(Transaction.amount))
        .where(
            Transaction.created_at >= start,
            Transaction.created_at < end,
            Transaction.status == TransactionStatuses.DONE
        )
    )

    result = await db.execute(stmt)
    total_volume = result.scalar() or 0.0

    return {
        "period": period,
        "total_exchange_volume": total_volume
    }


@router.get("/statistics/new-users")
async def get_new_users(period: PeriodEnum = Query(default=PeriodEnum.day),
                        db: AsyncSession = Depends(get_async_session)):
    """
    Новые пользователи за период.
    /statistics/new-users?period=day|week|month
    """
    start, end = get_period_range(period)

    stmt = (
        select(func.count(User.id))
        .where(User.created_at >= start, User.created_at < end)
    )

    result = await db.execute(stmt)
    count_new_users = result.scalar() or 0

    return {"period": period, "new_users": count_new_users}


@router.get("/statistics/active-users")
async def get_active_users(
    period: PeriodEnum = Query(default=PeriodEnum.day),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Активные пользователи (совершившие хотя бы 1 транзакцию) за период.
    """
    start, end = get_period_range(period)

    subq = (
        select(Transaction.user_id)
        .where(
            Transaction.created_at >= start,
            Transaction.created_at < end,
            Transaction.status == TransactionStatuses.DONE
        )
        .distinct()
        .subquery()
    )

    stmt = select(func.count("*")).select_from(subq)
    result = await db.execute(stmt)
    active_users_count = result.scalar() or 0

    return {"period": period, "active_users": active_users_count}


@router.get("/statistics/average-transaction-amount")
async def get_average_transaction_amount(
    period: PeriodEnum = Query(default=PeriodEnum.day),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Средняя стоимость транзакции = сумма транзакций / кол-во
    транзакций за период.
    """
    start, end = get_period_range(period)

    # Запрос для суммы
    stmt_sum = (
        select(func.sum(Transaction.amount))
        .where(
            Transaction.created_at >= start,
            Transaction.created_at < end,
            Transaction.status == TransactionStatuses.DONE
        )
    )
    result_sum = await db.execute(stmt_sum)
    total_sum = result_sum.scalar() or 0.0

    stmt_count = (
        select(func.count(Transaction.id))
        .where(
            Transaction.created_at >= start,
            Transaction.created_at < end,
            Transaction.status == TransactionStatuses.DONE
        )
    )
    result_count = await db.execute(stmt_count)
    total_count = result_count.scalar() or 0

    average = 0.0
    if total_count > 0:
        average = total_sum / total_count

    return {"period": period, "average_transaction_amount": average}


@router.get("/statistics/conversion")
async def get_conversion(db: AsyncSession = Depends(get_async_session)):
    """
    Процент зарегистрированных пользователей, совершивших хотя бы
    одну транзакцию.
    """

    stmt_total_users = select(func.count(User.id))
    result_total_users = await db.execute(stmt_total_users)
    total_users = result_total_users.scalar() or 0

    subq_users_with_transactions = (
        select(Transaction.user_id)
        .where(Transaction.status == TransactionStatuses.DONE)
        .distinct()
        .subquery()
    )

    stmt_count_with_transactions = select(
        func.count("*")).select_from(subq_users_with_transactions)
    result_count_with_transactions = await db.execute(
        stmt_count_with_transactions)
    total_users_with_transactions = (
        result_count_with_transactions.scalar() or 0)

    if total_users > 0:
        conversion_registered_to_active = (
            total_users_with_transactions / total_users) * 100
    else:
        conversion_registered_to_active = 0.0

    return {
        "conversion_registered_to_active": (
            f"{conversion_registered_to_active:.2f}%")
    }


@router.get("/statistics/arpu")
async def get_arpu(db: AsyncSession = Depends(get_async_session)):
    """
    ARPU = Общий доход / кол-во пользователей
    Предположим, что доход = сумма комиссий с транзакций (пример).
    В реальности нужно уточнить, как именно считается "доход".
    """

    stmt_transactions = (
        select(func.sum(Transaction.amount))
        .where(Transaction.status == TransactionStatuses.DONE)
    )
    result_transactions = await db.execute(stmt_transactions)
    total_transactions = result_transactions.scalar() or 0
    total_revenue = total_transactions * Decimal(0.01)

    stmt_users = select(func.count(User.id))
    result_users = await db.execute(stmt_users)
    total_users = result_users.scalar() or 0

    arpu = 0.0
    if total_users > 0:
        arpu = total_revenue / total_users

    return {"arpu": arpu}


@router.get("/statistics/retention-churn")
async def get_retention_churn(db: AsyncSession = Depends(get_async_session)):
    """
    Например, возьмём период N (в днях) и посмотрим,
    сколько пользователей вернулись/не вернулись.
    Для упрощённого примера:
      - RetentionRate = (кол-во пользователей, пришедших в период 1, которые
      активны в период 2) / (кол-во пользователей, пришедших в период 1)
      - ChurnRate = 1 - RetentionRate
    """
    now = datetime.utcnow()
    one_month_ago = now - timedelta(days=30)
    two_weeks_ago = now - timedelta(days=14)

    stmt_registered_month_ago = (
        select(User)
        .where(User.created_at < one_month_ago)
    )
    result_registered_month_ago = await db.execute(stmt_registered_month_ago)
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
    db: AsyncSession = Depends(get_async_session)
):
    """
    % успешно завершённых транзакций (status="completed")
    относительно всех начатых (status="started" или других).
    """
    start, end = get_period_range(period)

    stmt_started = (
        select(func.count(Transaction.id))
        .where(
            Transaction.created_at >= start,
            Transaction.created_at < end
        )
    )
    result_started = await db.execute(stmt_started)
    total_started = result_started.scalar() or 0

    stmt_completed = (
        select(func.count(Transaction.id))
        .where(
            Transaction.created_at >= start,
            Transaction.created_at < end,
            Transaction.status == TransactionStatuses.DONE
        )
    )
    result_completed = await db.execute(stmt_completed)
    total_completed = result_completed.scalar() or 0

    completion_rate = 0.0
    if total_started > 0:
        completion_rate = total_completed / total_started

    return {
        "period": period,
        "transaction_completion_rate": f"{completion_rate * 100:.2f}%"
    }
