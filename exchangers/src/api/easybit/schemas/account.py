from pydantic import BaseModel, Field, ConfigDict

class AccountData(BaseModel):
    level: int
    volume: str
    fee: str
    extra_fee: str = Field(alias="extraFee")
    total_fee: str = Field(alias="totalFee")

    model_config = ConfigDict(populate_by_name=True)

class AccountResponse(BaseModel):
    success: int
    data: AccountData

    model_config = ConfigDict(populate_by_name=True)