from pydantic import BaseModel, Field

class AccountData(BaseModel):
    level: int
    volume: str
    fee: str
    extra_fee: str = Field(alias="extraFee")
    total_fee: str = Field(alias="totalFee")

    class Config:
        allow_population_by_field_name = True

class AccountResponse(BaseModel):
    success: int
    data: AccountData

    class Config:
        allow_population_by_field_name = True