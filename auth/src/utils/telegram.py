import hashlib
import hmac
import time


def verify_telegram_auth(data: dict, bot_token: str) -> bool:
    auth_date = int(data.get('auth_date', 0))
    hash_received = data.get('hash', '')

    if time.time() - auth_date > 300:
        return False

    data_check_string = '\n'.join(
        f'{k}={v}' for k, v in sorted(data.items()) if k != 'hash'
    )

    # Создаем ключ HMAC-SHA256 с использованием bot_token
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    hash_calculated = hmac.new(secret_key, data_check_string.encode(),
                               hashlib.sha256).hexdigest()

    return hmac.compare_digest(hash_received, hash_calculated)
