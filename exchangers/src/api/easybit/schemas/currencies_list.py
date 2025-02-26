from typing import List, Optional
from pydantic import BaseModel, Field

class NetworkInfo(BaseModel):
    network: str
    name: str
    is_default: Optional[bool] = Field(alias="isDefault", default=None)
    send_status: bool = Field(alias="sendStatus")
    receive_status: bool = Field(alias="receiveStatus")
    receive_decimals: int = Field(alias="receiveDecimals")
    confirmations_minimum: int = Field(alias="confirmationsMinimum")
    confirmations_maximum: int = Field(alias="confirmationsMaximum")
    explorer: str
    explorer_hash: str = Field(alias="explorerHash")
    explorer_address: str = Field(alias="explorerAddress")
    has_tag: bool = Field(alias="hasTag")
    tag_name: Optional[str] = Field(alias="tagName", default=None)
    contract_address: Optional[str] = Field(alias="contractAddress", default=None)
    explorer_contract: Optional[str] = Field(alias="explorerContract", default=None)

    model_config = {
        "populate_by_name": True
    }

class Currency(BaseModel):
    currency: str
    name: str
    send_status_all: bool = Field(alias="sendStatusAll")
    receive_status_all: bool = Field(alias="receiveStatusAll")
    network_list: List[NetworkInfo] = Field(alias="networkList")

    model_config = {
        "populate_by_name": True
    }

class CurrencyListResponse(BaseModel):
    success: int
    data: List[Currency]

    model_config = {
        "populate_by_name": True
    }