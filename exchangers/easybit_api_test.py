import asyncio
from exchangers.src.api.easybit.easybit_client import EasyBitClient
from exchangers.src.api.easybit.schemas.order import CreateOrderRequest

async def main():
    # Создание экземпляра клиента; API ключ загружается из .env автоматически
    client = EasyBitClient()
    
    # Проверка получения данных аккаунта
    try:
        account_info = await client.account()
        print("Account Info:")
        print(account_info)
    except Exception as e:
        print("Ошибка при запросе аккаунта:", e)
    
    # # Проверка получения списка валют
    # try:
    #     currency_list = await client.get_currency_list()
    #     print("\nCurrency List:")
    #     print(currency_list)
    # except Exception as e:
    #     print("Ошибка при получении списка валют:", e)
        
    # Проверка получения списка пар
    # try:
    #     pair_list = await client.get_pair_list()
    #     print("\nPair List:")
    #     print(pair_list)
    # except Exception as e:
    #     print("Ошибка при получении списка пар:", e)

    # Получение курса обмена валют
    try:
        send_currency = "BTC"  # Валюта для отправки
        receive_currency = "ETH"  # Валюта для получения
        amount = 0.001  # Сумма для отправки

        rate_response = await client.get_rate(
            send=send_currency,
            receive=receive_currency,
            amount=amount
        )
        print("\nExchange Rate Response:")
        print(rate_response)
    except Exception as e:
        print("Ошибка при получении курса обмена:", e)
    
    # Пример создания заказа (не забудьте заменить receiveAddress на корректное значение)
    try:
        order_data = CreateOrderRequest(
            send="BTC",
            receive="ETH",
            amount="1",  # Пример значения
            receiveAddress="0xYourReceiveAddress"  # Замените на реальный адрес
        )
        order_response = await client.create_order(order_data)
        print("\nOrder Response:")
        print(order_response)
    except Exception as e:
        print("Ошибка при создании заказа:", e)
    
    # Проверка получения списка заказов
    try:
        orders = await client.get_orders()
        print("\nOrders List:")
        print(orders)
    except Exception as e:
        print("Ошибка при получении списка заказов:", e)

if __name__ == "__main__":
    asyncio.run(main())