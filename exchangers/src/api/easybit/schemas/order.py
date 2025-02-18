from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional

class OrderStatusEnum(str, Enum):
    AWAITING_DEPOSIT = "Awaiting Deposit"
    CONFIRMING_DEPOSIT = "Confirming Deposit"
    EXCHANGING = "Exchanging"
    SENDING = "Sending"
    COMPLETE = "Complete"
    REFUND = "Refund"
    FAILED = "Failed"
    VOLATILITY_PROTECTION = "Volatility Protection"
    ACTION_REQUEST = "Action Request"
    REQUEST_OVERDUE = "Request Overdue"

class CreateOrderRequest(BaseModel):
    send: str
    receive: str
    amount: str  
    receive_address: str = Field(alias="receiveAddress")
    payload: Optional[str] = None
    user_device_id: Optional[str] = Field(alias="userDeviceId", default=None)
    user_id: Optional[str] = Field(alias="userId", default=None)
    send_network: Optional[str] = Field(alias="sendNetwork", default=None)
    receive_network: Optional[str] = Field(alias="receiveNetwork", default=None)
    receive_tag: Optional[str] = Field(alias="receiveTag", default=None)
    amount_type: Optional[str] = Field(alias="amountType", default=None)
    extra_fee_override: Optional[float] = Field(alias="extraFeeOverride", default=None)
    vpm: Optional[str] = None
    refund_address: Optional[str] = Field(alias="refundAddress", default=None)
    refund_tag: Optional[str] = Field(alias="refundTag", default=None)

class OrderData(BaseModel):
    id: str
    send: str
    receive: str
    send_network: str = Field(alias="sendNetwork")
    receive_network: str = Field(alias="receiveNetwork")
    send_amount: str = Field(alias="sendAmount")
    receive_amount: str = Field(alias="receiveAmount")
    send_address: str = Field(alias="sendAddress")
    send_tag: Optional[str] = Field(alias="sendTag", default=None)
    receive_address: str = Field(alias="receiveAddress")
    receive_tag: Optional[str] = Field(alias="receiveTag", default=None)
    refund_address: Optional[str] = Field(alias="refundAddress", default=None)
    refund_tag: Optional[str] = Field(alias="refundTag", default=None)
    vpm: str
    created_at: int = Field(alias="createdAt")

class OrderResponse(BaseModel):
    success: int
    data: OrderData

class OrderStatusData(BaseModel):
    id: str
    status: OrderStatusEnum
    receive_amount: str = Field(alias="receiveAmount")
    hash_in: Optional[str] = Field(alias="hashIn", default=None)
    hash_out: Optional[str] = Field(alias="hashOut", default=None)
    validation_link: Optional[str] = Field(alias="validationLink", default=None)
    created_at: int = Field(alias="createdAt")
    updated_at: int = Field(alias="updatedAt")

class OrderStatusResponse(BaseModel):
    success: int
    data: OrderStatusData