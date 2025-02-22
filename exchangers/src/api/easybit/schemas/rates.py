from typing import List,Optional
from pydantic import BaseModel, Field

class PairListResponse(BaseModel):
    success: int
    data: List[str] = Field(..., description='List of pairs in format "sendCurrency_sendNetwork_receiveCurrency_receiveNetwork"')

    class Config:
        allow_population_by_field_name = True

class PairInfoData(BaseModel):
    minimumAmount: Optional[str] = Field(None, alias="minimumAmount")
    maximumAmount: Optional[str] = Field(None, alias="maximumAmount")
    networkFee: Optional[str] = Field(None, alias="networkFee")
    confirmations: Optional[int] = None
    processingTime: Optional[str] = Field(None, alias="processingTime")
    # Поля для ошибок
    currency: Optional[str] = None
    network: Optional[str] = None
    side: Optional[str] = None

class PairInfoResponse(BaseModel):
    success: int
    errorCode: Optional[int] = None
    errorMessage: Optional[str] = None
    data: Optional[PairInfoData] = None


class RateData(BaseModel):
    rate: Optional[str] = None
    sendAmount: Optional[str] = None
    receiveAmount: Optional[str] = None
    networkFee: Optional[str] = None
    confirmations: Optional[int] = None
    processingTime: Optional[str] = None
    # Поля для ошибок
    currency: Optional[str] = None
    network: Optional[str] = None
    side: Optional[str] = None

class RateResponse(BaseModel):
    success: int
    errorCode: Optional[int] = None
    errorMessage: Optional[str] = None
    data: Optional[RateData] = None