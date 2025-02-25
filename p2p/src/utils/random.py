import random
import string


def generate_unique_name(length: int) -> str:
    return ''.join(random.choices(
        string.ascii_uppercase + string.digits, k=length))
