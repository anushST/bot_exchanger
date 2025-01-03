from decimal import Decimal

from pydantic import BaseModel, Field


class Coin(BaseModel):
    name: str
    ticker: str
    full_name: str = Field(..., alias="fullName")
    enabled: bool
    enabled_from: bool = Field(..., alias="enabledFrom")
    enabled_to: bool = Field(..., alias="enabledTo")
    fix_rate_enabled: bool = Field(..., alias="fixRateEnabled")
    payin_confirmations: int = Field(..., alias="payinConfirmations")
    address_url: str = Field(..., alias="addressUrl")
    transaction_url: str = Field(..., alias="transactionUrl")
    image: str
    fixed_time: int = Field(..., alias="fixedTime")
    contract_address: str = Field(..., alias="contractAddress")
    protocol: str
    blockchain: str
    blockchain_precision: int = Field(..., alias="blockchainPrecision")


class CoinPairs(BaseModel):
    from_coin: str = Field(..., alias='from')
    to_coin: str = Field(..., alias='to')


class PairParams(BaseModel):
    from_coin: str = Field(..., alias='from')
    to_coin: str = Field(..., alias='to')

    model_config = {
        "populate_by_name": True,
    }


class PairParamsData(BaseModel):
    from_coin: str = Field(..., alias='from')
    to_coin: str = Field(..., alias='to')
    min_amount_float: Decimal = Field(..., alias="minAmountFloat")
    max_amount_float: Decimal = Field(..., alias="maxAmountFloat")
    min_amount_fixed: Decimal = Field(..., alias="minAmountFixed")
    max_amount_fixed: Decimal = Field(..., alias="maxAmountFixed")
