from typing import List
from pydantic import BaseModel, Field

class PairListResponse(BaseModel):
    success: int
    data: List[str] = Field(..., description='List of pairs in format "sendCurrency_sendNetwork_receiveCurrency_receiveNetwork"')

    class Config:
        allow_population_by_field_name = True

class PairInfoData(BaseModel):
    minimum_amount: str = Field(..., alias="minimumAmount")
    maximum_amount: str = Field(..., alias="maximumAmount")
    network_fee: str = Field(..., alias="networkFee")
    confirmations: int
    processing_time: str = Field(..., alias="processingTime")

    class Config:
        allow_population_by_field_name = True

class PairInfoResponse(BaseModel):
    success: int
    data: PairInfoData

    class Config:
        allow_population_by_field_name = True

class RateData(BaseModel):
    rate: str
    send_amount: str = Field(..., alias="sendAmount")
    receive_amount: str = Field(..., alias="receiveAmount")
    network_fee: str = Field(..., alias="networkFee")
    confirmations: int
    processing_time: str = Field(..., alias="processingTime")

    class Config:
        allow_population_by_field_name = True

class RateResponse(BaseModel):
    success: int
    data: RateData

    class Config:
        allow_population_by_field_name = True