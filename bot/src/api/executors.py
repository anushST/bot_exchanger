from asyncio import sleep
from src.database import session
from sqlalchemy.future import select
from src.models import Transaction
from src.config import FFIO_APIKEY, FFIO_SECRET

from .ff import FixedFloatApi

Api = FixedFloatApi(FFIO_APIKEY, FFIO_SECRET)

import logging
logger = logging.getLogger(__name__)


async def show_rate(transaction):
    data = {
        'type': transaction.type,
        'fromCcy': transaction.from_ccy,
        'toCcy': transaction.to_ccy,
        'direction': transaction.direction,
        'amount': transaction.amount,
        'toAddress': transaction.to_address
    }
    result = Api.price(data)
    return result

async def create_transactions(transaction: Transaction, bot, chat_id):
    data = {
        'type': transaction.type,
        'fromCcy': transaction.from_ccy,
        'toCcy': transaction.to_ccy,
        'direction': transaction.direction,
        'amount': transaction.amount,
        'toAddress': transaction.to_address
    }
    result = Api.create(data)
    logger.critical(result)
    if 'status' in result.keys():
        wallet_to_send = result['from']['address']
        amount = result['from']['amount']
        coin = result['from']['coin']
        await bot.send_message(
            chat_id=chat_id,
            text=f'Отправьте {amount} {coin} на адрес {wallet_to_send}'
        )

    return {'id': result['id'], 'token': result['token']}


async def stay_tuned(credentials, bot, chat_id):
    while True:
        data = {
            'id': credentials['id'],
            'token': credentials['token']
        }
        result = Api.order(data)

        if 'status' in result.keys() and result['status'] == 'EXCHANGE':
            await bot.send_message(
                chat_id=chat_id,
                text='Валюта была получена дождитесь обработки'
            )
            break
        await sleep(10)


async def success(credentials, bot, chat_id):
    while True:
        data = {
            'id': credentials['id'],
            'token': credentials['token']
        }
        result = Api.order(data)

        if 'status' in result.keys() and result['status'] == 'DONE':
            await bot.send_message(
                chat_id=chat_id,
                text='Ваша валюты была успешна отправлена'
            )
            break
        await sleep(10)


async def process_transaction(transaction, bot, chat_id):
    credentials = await create_transactions(transaction, bot, chat_id)
    await stay_tuned(credentials, bot, chat_id)
    await success(credentials, bot, chat_id)
