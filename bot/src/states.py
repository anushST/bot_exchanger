from aiogram.fsm.state import StatesGroup, State


class ExchangeForm(StatesGroup):
    currency_from = State()
    currency_from_id = State()
    currency_from_network = State()
    currency_from_name = State()

    currency_to = State()
    currency_to_id = State()
    currency_to_network = State()
    currency_from_network_name = State()

    is_fixed_rate = State()
    wallet_address = State()
    amount_currency = State()
    amount_value = State()
    amount_direction = State()

    confirm = State()
    exchange_id = State()
