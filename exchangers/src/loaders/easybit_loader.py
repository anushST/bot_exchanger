import asyncio
import json
import logging
from typing import Dict, Set
from redis.asyncio import StrictRedis
from src.config import config
from src.api.easybit.easybit_client import easybit_client
from src.exceptions import ClientError
from src.redis import redis_client
from src.api.schemas import Coin

logger = logging.getLogger(__name__)

class LoadEasyBitDataToRedis:
    EXCHANGER = 'easybit'
    COINS_KEY = 'coins'
    COIN_NETWORKS = '{coin_name}:networks'
    FULL_COIN_INFO_KEY = '{exchanger}:{coin_name}:{network}:info'
    RATE_KEY = '{exchanger}:{type}:{from_coin}:{send_network}:to:{to_coin}:{receive_network}:info'

    def __init__(self):
        self.redis_client = redis_client
        self.api_client = easybit_client

    async def load_currencies_and_networks(self) -> None:
        try:
            response = await self.api_client.get_currency_list()
            
            # Проверяем структуру ответа
            if hasattr(response, 'data'):
                currencies = response.data
            else:
                currencies = response
                
            for currency in currencies:
                # Проверяем, является ли currency объектом или кортежем
                if isinstance(currency, tuple):
                    logger.debug(f"Currency is a tuple: {currency}")
                    continue
                    
                coin_name = currency.currency.upper()
                await self.redis_client.sadd(self.COINS_KEY, coin_name)
                
                for network_info in currency.network_list:
                    network = network_info.network.upper()
                    await self.redis_client.sadd(
                        self.COIN_NETWORKS.format(coin_name=coin_name),
                        network
                    )
                    
                    # Create and store full coin info
                    await self.redis_client.set(
                        self.FULL_COIN_INFO_KEY.format(
                            exchanger=self.EXCHANGER,
                            coin_name=coin_name,
                            network=network
                        ),
                        Coin(
                            code=currency.currency,  # Using currency as code
                            coin=currency.currency,
                            network=network_info.network,
                            receive=network_info.receive_status,
                            send=network_info.send_status,
                            tag_name=network_info.tag_name if hasattr(network_info, 'tag_name') else None
                        ).model_dump_json(by_alias=True)
                    )
            
            logger.info("Currency and network list successfully loaded")
            
        except ClientError as e:
            logger.error(f"Error loading currency list: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Unexpected error loading currency list: {e}", exc_info=True)

    async def load_rates(self) -> None:
        try:
            response = await self.api_client.get_pair_list()
            
            if hasattr(response, 'data'):
                pair_list = response.data
            else:
                pair_list = response
                
            logger.debug(f"Received pairs from pair_list: {len(pair_list) if hasattr(pair_list, '__len__') else 'unknown length'}")
            processed_pairs = 0

            for pair_str in pair_list:
                try:
                    send, send_network, receive, receive_network = pair_str.split('_')
                    
                    processed_pairs += 1
                    logger.debug(f"Processing pair: {send}->{receive} ({send_network}->{receive_network})")
                    
                    try:
                        pair_info_response = await self.api_client.get_pair_info(
                            send=send,
                            receive=receive,
                            send_network=send_network,
                            receive_network=receive_network
                        )
                        
                        # Проверяем структуру ответа
                        if hasattr(pair_info_response, 'data'):
                            pair_info = pair_info_response.data
                        else:
                            pair_info = pair_info_response
                        
                        if pair_info and hasattr(pair_info, 'minimumAmount') and hasattr(pair_info, 'maximumAmount'):
                            min_amount = float(pair_info.minimumAmount)
                            max_amount = float(pair_info.maximumAmount)
                            amount = (min_amount + max_amount) / 2
                            logger.debug(f"For pair {send}->{receive}: min={min_amount}, max={max_amount}, amount={amount}")
                        else:
                            logger.warning(
                                f"Insufficient data for pair {send}->{receive} "
                                f"({send_network}->{receive_network}): no min/max amount"
                            )
                            continue
                        
                        try:
                            rate_response = await self.api_client.get_rate(
                                send=send,
                                receive=receive,
                                amount=amount,
                                send_network=send_network,
                                receive_network=receive_network
                            )
                            
                            if hasattr(rate_response, 'data'):
                                rate_data = rate_response.data
                            else:
                                rate_data = rate_response
                            
                            if rate_data:
                                key = self.RATE_KEY.format(
                                    exchanger=self.EXCHANGER,
                                    type='float',
                                    from_coin=send.upper(),
                                    send_network=send_network.upper(),
                                    to_coin=receive.upper(),
                                    receive_network=receive_network.upper()
                                )
                                
                                if hasattr(rate_data, 'model_dump_json'):
                                    value = rate_data.model_dump_json()
                                elif hasattr(rate_data, 'json'):
                                    value = rate_data.json()
                                else:
                                    value = json.dumps(rate_data.__dict__)
                                    
                                result = await self.redis_client.set(key, value)
                                if result:
                                    logger.info(f"Rate for {send}->{receive} ({send_network}->{receive_network}) saved to Redis")
                                else:
                                    logger.error(f"Failed to save rate for {send}->{receive} ({send_network}->{receive_network}) to Redis")
                            else:
                                logger.warning(
                                    f"No rate data for pair {send}->{receive} ({send_network}->{receive_network})"
                                )
                                continue
                        except ClientError as e:
                            logger.error(f"Error getting rate for {send}->{receive} ({send_network}->{receive_network}): {e}", exc_info=True)
                            continue
                    except ClientError as e:
                        logger.error(f"Error getting pair info for {send}->{receive} ({send_network}->{receive_network}): {e}", exc_info=True)
                        continue
                        
                except Exception as e:
                    logger.warning(
                        f"Error processing pair {pair_str}: {e}"
                    )
                    continue
            
            logger.info(f"Exchange rates successfully loaded, processed pairs: {processed_pairs}")
        except ClientError as e:
            logger.error(f"Error loading exchange rates: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Unexpected error loading exchange rates: {e}", exc_info=True)