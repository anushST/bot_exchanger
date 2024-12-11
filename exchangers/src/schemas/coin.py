from pydantic import BaseModel


class CoinSchema(BaseModel):
    coin_name: str
