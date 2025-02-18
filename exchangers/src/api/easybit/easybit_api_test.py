import asyncio
from .easybit_client import EasyBitClient
from .schemas.order import CreateOrderRequest

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
    try:
        pair_list = await client.get_pair_list()
        print("\nPair List:")
        print(pair_list)
    except Exception as e:
        print("Ошибка при получении списка пар:", e)
    
    # Пример создания заказа (не забудьте заменить receiveAddress на корректное значение)
    try:
        order_data = CreateOrderRequest(
            send="BTC",
            receive="ETH",
            amount="0.001",  # Пример значения
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