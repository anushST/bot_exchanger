import os
import asyncio
import logging
from typing import Any, Dict, Optional, Union
import aiohttp
from pydantic import BaseModel, ValidationError

from . import constants as const
from . import schemas
from src.config import config
from src.api import exceptions as ex

logger = logging.getLogger(__name__)

class EasyBitClient:
    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or config.EASYBIT_API_KEY
        if not self.api_key:
            raise ValueError(
                "API key not set. Check config.EASYBIT_API_KEY."
            )
        self.base_url = "https://api.easybit.com"
        self.timeout = aiohttp.ClientTimeout(total=30)

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Union[Dict, BaseModel]] = None,
        data: Optional[Union[Dict, BaseModel]] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        headers = {"API-KEY": self.api_key}
        
        if isinstance(params, BaseModel):
            params = params.model_dump(exclude_none=True)
        if isinstance(data, BaseModel):
            data = data.model_dump(exclude_none=True)
            
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            for attempt in range(const.MAX_RETRIES):
                try:
                    async with session.request(
                        method=method,
                        url=url,
                        headers=headers,
                        params=params,
                        json=data,
                    ) as response:
                        if response.status == 429:
                            logger.warning(f"Rate limit exceeded, attempt {attempt + 1}")
                            await asyncio.sleep(const.RETRY_DELAY * (attempt + 1))
                            continue
                            
                        response_data = await response.json()
                        
                        # Check for API errors
                        if response.status >= 400:
                            error_message = response_data.get('errorMessage', 'Unknown API error')
                            error_code = response_data.get('errorCode', 0)
                            logger.error(f"API error: {error_message} (code: {error_code})")
                            raise ex.ApiError(f"API error: {error_message} (code: {error_code})")
                        
                        # Check for success flag
                        if response_data.get('success') == 0:
                            error_message = response_data.get('errorMessage', 'Unknown API error')
                            error_code = response_data.get('errorCode', 0)
                            logger.error(f"API response error: {error_message} (code: {error_code})")
                            
                            # Determine error type by code
                            if error_code in (1001, 1002, 1003):  # Validation error codes
                                raise ex.ValidationApiError(f"Validation error: {error_message} (code: {error_code})")
                            elif error_code in (2001, 2002):  # Authentication error codes
                                raise ex.AuthenticationError(f"Authentication error: {error_message} (code: {error_code})")
                            elif error_code in (3001, 3002):  # Rate limit error codes
                                raise ex.RateLimitError(f"Rate limit exceeded: {error_message} (code: {error_code})")
                            else:
                                raise ex.ApiError(f"API error: {error_message} (code: {error_code})")
                        
                        return response_data
                        
                except aiohttp.ClientError as e:
                    logger.warning(f"Request error: {e}, attempt {attempt + 1}")
                    if attempt == const.MAX_RETRIES - 1:
                        raise ex.NetworkError(f"Network error after {const.MAX_RETRIES} attempts: {e}")
                    await asyncio.sleep(const.RETRY_DELAY * (attempt + 1))

    async def account(self) -> Dict[str, Any]:
        """
        Get account data via API.
        Returns a dictionary with account data.
        """
        return await self._request("GET", "/account")

    async def get_currency_list(self) -> schemas.CurrencyListResponse:
        response = await self._request("GET", "/currencyList")
        try:
            return schemas.CurrencyListResponse(**response)
        except ValidationError as e:
            logger.error(f"CurrencyListResponse validation error: {e}")
            raise ex.DataProcessingError(f"CurrencyListResponse validation error: {e}")

    async def get_pair_list(self) -> schemas.PairListResponse:
        response = await self._request("GET", "/pairList")
        try:
            return schemas.PairListResponse(**response)
        except ValidationError as e:
            logger.error(f"PairListResponse validation error: {e}")
            raise ex.DataProcessingError(f"PairListResponse validation error: {e}")

    async def get_pair_info(
        self,
        send: str,
        receive: str,
        send_network: Optional[str] = None,
        receive_network: Optional[str] = None,
    ) -> schemas.PairInfoResponse:
        """
        Get information about an exchange pair.
        :param send: Currency to send.
        :param receive: Currency to receive.
        :param send_network: Network for sending (optional).
        :param receive_network: Network for receiving (optional).
        """
        request = schemas.PairInfoRequest(
            send=send,
            receive=receive,
            sendNetwork=send_network,
            receiveNetwork=receive_network
        )
        
        response = await self._request("GET", "/pairInfo", params=request)
        try:
            result = schemas.PairInfoResponse(**response)
            # Check for errors in data
            if result.data and (result.data.currency or result.data.network or result.data.side):
                error_msg = f"Pair data error: currency={result.data.currency}, network={result.data.network}, side={result.data.side}"
                logger.error(error_msg)
                raise ex.InvalidPairError(error_msg)
            return result
        except ValidationError as e:
            logger.error(f"PairInfoResponse validation error: {e}")
            raise ex.DataProcessingError(f"PairInfoResponse validation error: {e}")

    async def get_rate(
        self,
        send: str,
        receive: str,
        amount: float,
        send_network: Optional[str] = None,
        receive_network: Optional[str] = None,
        amount_type: Optional[str] = None,
        extra_fee_override: Optional[float] = None,
    ) -> schemas.RateResponse:
        """
        Get exchange rate.
        :param send: Currency to send.
        :param receive: Currency to receive.
        :param amount: Amount to exchange.
        :param send_network: Network for sending (optional).
        :param receive_network: Network for receiving (optional).
        :param amount_type: Amount type (optional).
        :param extra_fee_override: Extra fee override (optional).
        """
        if amount <= 0:
            raise ex.ValidationApiError("Amount must be a positive number")
            
        request = schemas.RateRequest(
            send=send,
            receive=receive,
            amount=amount,
            sendNetwork=send_network,
            receiveNetwork=receive_network,
            amountType=amount_type,
            extraFeeOverride=extra_fee_override
        )
        
        response = await self._request("GET", "/rate", params=request)
        try:
            result = schemas.RateResponse(**response)
            # Check for errors in data
            if result.data and (result.data.currency or result.data.network or result.data.side):
                error_msg = f"Rate data error: currency={result.data.currency}, network={result.data.network}, side={result.data.side}"
                logger.error(error_msg)
                raise ex.InvalidRateError(error_msg)
            return result
        except ValidationError as e:
            logger.error(f"RateResponse validation error: {e}")
            raise ex.DataProcessingError(f"RateResponse validation error: {e}")

    async def create_order(self, order_data: schemas.CreateOrderRequest) -> schemas.OrderResponse:
        """
        Create an exchange order.
        :param order_data: Order creation data.
        """
        # Check required fields
        if not order_data.send or not order_data.receive or not order_data.amount or not order_data.receive_address:
            raise ex.ValidationApiError("Required fields for order creation are missing")
            
        response = await self._request("POST", "/order", data=order_data)
        try:
            result = schemas.OrderResponse(**response)
            # Check for successful order creation
            if not result.data or not result.data.order_id:
                error_msg = "Failed to create order, order ID is missing in response"
                logger.error(error_msg)
                raise ex.OrderCreationError(error_msg)
            return result
        except ValidationError as e:
            logger.error(f"OrderResponse validation error: {e}")
            raise ex.DataProcessingError(f"OrderResponse validation error: {e}")

    async def get_order_status(self, order_id: str) -> schemas.OrderStatusResponse:
        """
        Get order status.
        :param order_id: Order ID.
        """
        if not order_id:
            raise ex.ValidationApiError("Order ID is not specified")
            
        request = schemas.OrderStatusRequest(order_id=order_id)
        response = await self._request("GET", "/orderStatus", params=request)
        try:
            result = schemas.OrderStatusResponse(**response)
            return result
        except ValidationError as e:
            logger.error(f"OrderStatusResponse validation error: {e}")
            raise ex.DataProcessingError(f"OrderStatusResponse validation error: {e}")

    async def get_orders(self) -> schemas.OrdersListResponse:
        """
        Get information about all orders.
        Returns a list of all user orders.
        """
        response = await self._request("GET", "/orders")
        try:
            return schemas.OrdersListResponse(**response)
        except ValidationError as e:
            logger.error(f"OrdersListResponse validation error: {e}")
            raise ex.DataProcessingError(f"OrdersListResponse validation error: {e}")

easybit_client = EasyBitClient()