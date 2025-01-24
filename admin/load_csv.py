import csv
import aiofiles
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
import random

# Импортируем модели
from src.models import User, Transaction

async def load_csv_data(
    db: AsyncSession,
    user_csv_path: str,
    transaction_csv_path: str
):
    """
    Считывает данные из user.csv и transaction.csv и загружает их в таблицы User и Transaction.
    """

    # 1. Чтение и загрузка User
    async with aiofiles.open(user_csv_path, mode='r', encoding='utf-8') as f:
        content = await f.read()
    lines = content.splitlines()
    user_reader = csv.DictReader(lines)  # Парсим как словарь, где ключи — названия колонок

    user_objects = []
    for row in user_reader:
        # row — это словарь вида: {"id": "...", "tg_id": "...", "tg_name": "...", ...}

        # Преобразуем типы (id часто автогенерируется, так что возможно вы не будете вручную его задавать)
        # tg_id — bigint
        tg_id = int(row["tg_id"])

        # Даты. Если поле не пустое, конвертируем
        def parse_date(date_str: str):
            return datetime.fromisoformat(date_str) if date_str else None

        last_active_at = parse_date(row["last_active_at"])
        created_at = parse_date(row["created_at"]) or datetime.now()
        updated_at = parse_date(row["updated_at"]) or datetime.now()

        # Создаём экземпляр User
        user_obj = User(
            # Если у вас в модели User есть явный Primary Key id с автоинкрементом,
            # и вы не хотите его вручную задавать — можно пропустить.
            # id=int(row["id"])  # <-- Закомментируйте, если PK создаётся автоматически

            tg_id=tg_id,
            tg_name=row["tg_name"],
            tg_username=row["tg_username"] or None,  # пустые строки превращаем в None
            language=row["language"] or "ru",
            last_active_at=last_active_at,
            created_at=created_at,
            updated_at=updated_at,
        )
        user_objects.append(user_obj)
        db.add(user_obj)

    await db.commit()
    for u in user_objects:
        await db.refresh(u)

    user_ids = [u.id for u in user_objects]
    # 2. Чтение и загрузка Transaction
    async with aiofiles.open(transaction_csv_path, mode='r', encoding='utf-8') as f:
        content = await f.read()
    lines = content.splitlines()
    tx_reader = csv.DictReader(lines)

    tx_objects = []
    for row in tx_reader:
        # Преобразуем числовые поля, даты и т.д.
        def parse_date(date_str: str):
            try:
                return datetime.fromisoformat(date_str)
            except ValueError:
                return None

        def parse_decimal(dec_str: str):
            try:
                return Decimal(dec_str)
            except Exception:
                return None

        created_at = parse_date(row["created_at"]) or datetime.now()
        updated_at = parse_date(row["updated_at"]) or datetime.now()

        # Пример конвертации статуса к нужному Enum (если нужно)
        # status = TransactionStatuses(row["status"])  # если вы используете Enum в Python
        # а если в модели у вас Enum(*TransactionStatuses.OPTIONS...), можно передать строку напрямую

        # user_id: в CSV у нас user_id - это не UUID, а integer (если в тестовых данных).
        # В реальном проекте может быть иначе.
        user_id = row["user_id"]

        # amount — DECIMAL(precision=50, scale=10)
        amount = parse_decimal(row["amount"])

        tx_obj = Transaction(
            # Если у модели Transaction есть автогенерируемый PK, можно не задавать id:
            # id=int(row["id"]),

            name=row["name"],
            status_code=int(row["status_code"]) if row["status_code"] else None,
            status=row["status"],
            is_status_showed=(row["is_status_showed"].lower() == "true"),
            msg=row["msg"] or None,
            user_id=random.choice(user_ids),  # внешний ключ на таблицу user
            exchanger=row["exchanger"] or None,
            rate_type=row["rate_type"],
            from_currency=row["from_currency"],
            from_currency_network=row["from_currency_network"],
            to_currency=row["to_currency"],
            to_currency_network=row["to_currency_network"],
            direction=row["direction"],
            amount=amount,
            to_address=row["to_address"],
            # ... аналогично для остальных колонок ...
            created_at=created_at,
            updated_at=updated_at,
        )
        tx_objects.append(tx_obj)
        db.add(tx_obj)

    # Завершаем транзакцию
    await db.commit()
    print("CSV данные успешно импортированы в таблицы User и Transaction!")
