from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class CreateTransactionDetails(BaseModel):
    id_: Optional[str | list[str]] = Field(None, alias="id")
    status: Optional[str | list[str]] = None
    currency: Optional[str | list[str]] = None
    address: Optional[str | list[str]] = None
    payout_address: Optional[str | list[str]] = Field(
        None, alias="payoutAddress")
    extra_id: Optional[str] = Field(None, alias="extraId")
    since: Optional[int] = None    # Unix timestamp в микросекундах
    limit: Optional[int] = None    # По умолчанию 10, макс. 100
    offset: Optional[int] = None   # Положение «курсора» выборки

    model_config = {
        "populate_by_name": True
    }


class CreateFloatTransaction(BaseModel):
    from_: str = Field(alias="from")
    to: str
    amount_from: str = Field(alias="amountFrom")
    address: str
    extra_id: Optional[str] = Field(None, alias="extraId")
    refund_address: Optional[str] = Field(None, alias="refundAddress")
    refund_extra_id: Optional[str] = Field(None, alias="refundExtraId")
    from_address: Optional[str] = Field(None, alias="fromAddress")
    from_extra_id: Optional[str] = Field(None, alias="fromExtraId")
    user_metadata: Optional[str] = Field(None, alias="userMetadata")

    model_config = {
        "populate_by_name": True
    }


class CreateFixedTransaction(BaseModel):
    from_: str = Field(alias="from")
    to: str
    rate_id: str = Field(alias="rateId")
    address: str
    amount_from: Optional[str] = Field(None, alias="amountFrom")
    amount_to: Optional[str] = Field(None, alias="amountTo")
    extra_id: Optional[str] = Field(None, alias="extraId")
    refund_address: str = Field(alias="refundAddress")
    refund_extra_id: Optional[str] = Field(None, alias="refundExtraId")
    from_address: Optional[str] = Field(None, alias="fromAddress")
    from_extra_id: Optional[str] = Field(None, alias="fromExtraId")
    user_metadata: Optional[str] = Field(None, alias="userMetadata")

    model_config = {
        "populate_by_name": True
    }


class TransactionDetails(BaseModel):
    id_: Optional[str] = Field(None, alias="id")
    created_at: Optional[int] = Field(None, alias="createdAt")
    type_: Optional[str] = Field(None, alias="type")
    money_received: Optional[int] = Field(None, alias="moneyReceived")
    money_sent: Optional[int] = Field(None, alias="moneySent")
    rate: Optional[Decimal] = Field(None, alias="rate")
    payin_confirmations: Optional[int] = Field(
        None, alias="payinConfirmations")
    status: Optional[str] = None
    currency_from: Optional[str] = Field(None, alias="currencyFrom")
    currency_to: Optional[str] = Field(None, alias="currencyTo")
    payin_address: Optional[str] = Field(None, alias="payinAddress")
    payin_extra_id: Optional[str] = Field(None, alias="payinExtraId")
    payin_extra_id_name: Optional[str] = Field(None, alias="payinExtraIdName")
    payin_hash: Optional[str] = Field(None, alias="payinHash")
    payout_hash_link: Optional[str] = Field(None, alias="payoutHashLink")
    refund_hash_link: Optional[str] = Field(None, alias="refundHashLink")
    amount_expected_from: Optional[Decimal] = Field(
        None, alias="amountExpectedFrom")
    payout_address: Optional[str] = Field(None, alias="payoutAddress")
    payout_extra_id: Optional[str] = Field(None, alias="payoutExtraId")
    payout_extra_id_name: Optional[str] = Field(None,
                                                alias="payoutExtraIdName")
    payout_hash: Optional[str] = Field(None, alias="payoutHash")
    refund_hash: Optional[str] = Field(None, alias="refundHash")
    refund_address: Optional[str] = Field(None, alias="refundAddress")
    refund_extra_id: Optional[str] = Field(None, alias="refundExtraId")
    amount_from: Optional[Decimal] = Field(None, alias="amountFrom")
    amount_to: Optional[Decimal] = Field(None, alias="amountTo")
    amount_expected_to: Optional[Decimal] = Field(
        None, alias="amountExpectedTo")
    network_fee: Optional[Decimal] = Field(None, alias="networkFee")
    exchange_fee: Optional[Decimal] = Field(None, alias="exchangeFee")
    api_extra_fee: Optional[Decimal] = Field(None, alias="apiExtraFee")
    total_fee: Optional[Decimal] = Field(None, alias="totalFee")
    can_push: Optional[bool] = Field(None, alias="canPush")
    can_refund: Optional[bool] = Field(None, alias="canRefund")


class FloatTransaction(BaseModel):
    id_: str = Field(alias="id")
    type_: str = Field(alias="type")
    payin_extra_id: Optional[str] = Field('', alias="payinExtraId")
    payout_extra_id: Optional[str] = Field('', alias="payoutExtraId")
    amount_expected_from: Decimal = Field(alias="amountExpectedFrom")
    status: str
    currency_from: str = Field(alias="currencyFrom")
    currency_to: str = Field(alias="currencyTo")
    amount_expected_to: Decimal = Field(alias="amountExpectedTo")
    payin_address: str = Field(alias="payinAddress")
    payout_address: str = Field(alias="payoutAddress")
    created_at: int = Field(alias="createdAt")
    network_fee: Decimal = Field(alias="networkFee")


class FixedTransaction(BaseModel):
    id_: str = Field(alias="id")
    type_: str = Field(alias="type")
    status: str
    pay_till: datetime = Field(alias="payTill")
    currency_from: str = Field(alias="currencyFrom")
    currency_to: str = Field(alias="currencyTo")
    payin_extra_id: Optional[str] = Field('', alias="payinExtraId")
    payout_extra_id: Optional[str] = Field('', alias="payoutExtraId")
    refund_address: str = Field(alias="refundAddress")
    amount_expected_from: Decimal = Field(alias="amountExpectedFrom")
    amount_expected_to: Decimal = Field(alias="amountExpectedTo")
    payin_address: str = Field(alias="payinAddress")
    payout_address: str = Field(alias="payoutAddress")
    created_at: int = Field(alias="createdAt")
    network_fee: Decimal = Field(alias="networkFee")
