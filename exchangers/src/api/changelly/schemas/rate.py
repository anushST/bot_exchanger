from pydantic import BaseModel, Field


class CreateRate(BaseModel):
    from_coin: str = Field(..., alias='from')
    to_coin: str = Field(..., alias='to')

    model_config = {
        "populate_by_name": True,
    }
