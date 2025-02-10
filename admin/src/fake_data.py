import random
import uuid
import logging
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from src.models import User, MarketingLink, MarketingLinkUser
from src.models.transaction import Transaction, TransactionStatuses, RateTypes, DirectionTypes
from src.utils.random import generate_unique_name

logger = logging.getLogger(__name__)


# Генерация случайных дат в диапазоне 4 лет
def random_date(start, end):
    delta = end - start
    random_days = random.randint(0, delta.days)
    random_seconds = random.randint(0, 86400)
    return start + timedelta(days=random_days, seconds=random_seconds)


# Генерация случайных данных для транзакции
def generate_random_transaction(user_id):
    now = datetime.now()
    start_date = now - timedelta(days=4 * 365)  # 4 года назад

    return Transaction(
        name=generate_unique_name(length=6),
        status=random.choice([status.value for status in TransactionStatuses]),
        user_id=user_id,
        exchanger=random.choice(['Binance', 'Kraken', 'Coinbase', 'Huobi']),
        rate_type=random.choice([rate.value for rate in RateTypes]),
        from_currency=random.choice(['BTC', 'ETH', 'USDT', 'BNB']),
        from_currency_network=random.choice(['ERC20', 'TRC20', 'BEP20']),
        to_currency=random.choice(['USDT', 'ETH', 'BTC', 'BNB']),
        to_currency_network=random.choice(['ERC20', 'TRC20', 'BEP20']),
        direction=random.choice([d.value for d in DirectionTypes]),
        amount=round(random.uniform(0.01, 1000), 8),
        to_address=str(uuid.uuid4())[:34],
        transaction_id=str(uuid.uuid4()),
        time_registred=random_date(start_date, now),
        time_expiration=random_date(now, now + timedelta(days=30)),
        created_at=random_date(start_date, now),
        updated_at=random_date(start_date, now)
    )


async def generate_random_users(session, links):
    now = datetime.now()
    start_date = now - timedelta(days=4 * 365)  # 4 года назад

    user = User(
        tg_id=random.randint(10000000, 999999999),
        tg_name='anush',
        created_at=random_date(start_date, now),
        updated_at=random_date(start_date, now)
    )
    try:
        session.add(user)
        await session.commit()
        await session.refresh(user)

        marketing_link_user = MarketingLinkUser(
            user_id=user.id,
            marketing_link_id=random.choice(links)
        )

        session.add(marketing_link_user)
        await session.commit()
        await session.refresh(marketing_link_user)
    except Exception:
        logger.error('Error', exc_info=True)
        return
    return user.id


async def generate_marketing_links(session: AsyncSession):
    try:
        link = MarketingLink(
            name=str(random.randint(10000000, 999999999))
        )
        session.add(link)
        await session.commit()
        await session.refresh(link)
        return link.id
    except Exception:
        logger.error('Error', exc_info=True)
        return


async def generate_transactions(session: AsyncSession,
                                num_transactions: int = 30000,
                                num_users: int = 1000,
                                marketing_links: int = 5):
    links = []
    for _ in range(marketing_links):
        link = await generate_marketing_links(session)
        if link:
            links.append(link)

    users = []
    for _ in range(num_users):
        user = await generate_random_users(session, links)
        if user:
            users.append(user)

    transactions = [generate_random_transaction(random.choice(users))
                    for _ in range(num_transactions)]

    session.add_all(transactions)
    await session.commit()
    print(f"{num_transactions} транзакций успешно добавлены в базу данных.")
