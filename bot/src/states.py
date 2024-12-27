from aiogram.fsm.state import StatesGroup, State


class ExchangeForm(StatesGroup):
    currency_from = State()
    currency_from_network = State()
    currency_from_nickname = State()

    currency_to = State()
    currency_to_network = State()
    currency_to_nickname = State()

    rate_type = State()
    wallet_address = State()
    tag = State()
    amount_currency = State()
    amount_value = State()
    amount_direction = State()

    confirm = State()
    exchange_id = State()

    emergency_address = State()
    emergency_tag = State()
