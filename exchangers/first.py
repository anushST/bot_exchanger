import redis
import json

from api.ff import FixedFloatApi
# Настройка подключения к Redis
redis_client = redis.StrictRedis(
    host='localhost',  # Адрес Redis сервера
    port=6379,         # Порт Redis
    db=0,              # Номер базы данных
    decode_responses=True  # Автоматическое декодирование строк
)

exchanger = 'ff.io'
# Функция для обработки данных и записи в Redis
def process_and_store_data(api_response):
    """
    Обрабатывает данные API и сохраняет их в Redis как множества (sets).

    :param api_response: Список словарей с данными монет
    """
    # # Очистка предыдущих данных
    # redis_client.delete('coins')  # Удаляем старый набор 'coins', если он есть

    # Обработка и запись информации по каждой монете
    for coin in api_response:
        coin_name = coin['coin']
        network = coin['network']

        # Добавление монеты в множество 'coins'
        redis_client.sadd('coins', coin_name)

        # Формирование ключа '<coin_name>:networks'
        key = f'{coin_name}:networks'

        # Добавление сети в множество для данной монеты
        redis_client.sadd(key, network)

        info_key = f'{exchanger}:{coin_name}:{network}:info'
        redis_client.set(info_key, json.dumps(coin))

    print('Данные успешно сохранены в Redis в формате множеств.')


def process_rates(rates):
    for item in rates:
        from_coin = item['from']
        to_coin = item['to']

        key = f'{exchanger}:fixed:{from_coin}:to:{to_coin}:info'
        print(key)
        redis_client.set(key, json.dumps(item))



if __name__ == '__main__':
    Api = FixedFloatApi('rOSLgo318f85Tfz6ODeKScpicdE5dDuJY2gttlc6', 'Qa3wT7MtTeC0NjZavuAqgxGfxZqD76F2CZPYF6qh')
    # api_response = Api.ccies()
    # process_and_store_data(api_response)
    # process_rates(Api.get_fixed_rates())
    print(redis_client.get('ff.io:fixed:ZRX:to:ZEC:info'))

# Вызов функции с примером ответа
# process_and_store_data(api_response)

