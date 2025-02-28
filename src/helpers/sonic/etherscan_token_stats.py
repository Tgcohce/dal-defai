import os
import logging
import requests
import time
from typing import Dict, Any, Optional
from web3 import Web3
from venv import logger


class EtherscanTokenStats:
    """
    Provides token statistics by querying the Etherscan API.
    This can help determine:
      - Current token balance
      - Timestamp of first purchase
      - Time since last sale
      - Average hold time
    """

    BASE_URL = "https://api.etherscan.io/api"

    @classmethod
    def get_token_balance(cls, wallet_address: str, token_address: str) -> float:
        """
        Gets the ERC-20 token balance for a given wallet.

        :param wallet_address: The Ethereum wallet address (0x...).
        :param token_address: The ERC-20 token contract address (0x...).
        :return: The balance as a floating number of tokens (accounting for decimals).
        """
        etherscan_api_key = os.getenv("ETHERSCAN_API_KEY", "")
        if not etherscan_api_key:
            raise ValueError("Missing Etherscan API key. Set ETHERSCAN_API_KEY in your environment.")

        # 1) Query token decimals by calling Etherscan's 'tokeninfo' or a separate contract call
        #    For simplicity, do a normal “balanceOf” call. Etherscan can return raw balances,
        #    but need to know decimals to convert properly. 

        # NOTE: Etherscan provides a specialized endpoint for token balance:
        #   ?module=account&action=tokenbalance&contractaddress=xxx&address=xxx
        # That returns the raw balance but not the decimals. Can call it, then fetch decimals separately.

        params = {
            "module": "account",
            "action": "tokenbalance",
            "contractaddress": token_address,
            "address": wallet_address,
            "tag": "latest",
            "apikey": etherscan_api_key,
        }

        try:
            response = requests.get(cls.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            if data["status"] != "1":
                raise ValueError(f"Etherscan returned error: {data.get('message')}")

            raw_balance_str = data.get("result", "0")
            raw_balance = float(raw_balance_str)

            # 2) Query the token’s decimals from Etherscan’s “tokeninfo” approach or do it via a contract call.
            #    For simplicity, call another endpoint. ]
            decimals = cls._get_token_decimals(token_address, etherscan_api_key)
            if decimals is None:
                logger.warning("Unable to determine token decimals, defaulting to 18.")
                decimals = 18

            balance = raw_balance / (10 ** decimals)
            logger.debug(f"Token balance for {wallet_address}: {balance} (raw: {raw_balance}, decimals: {decimals})")
            return balance

        except Exception as e:
            logger.error(f"Error fetching token balance from Etherscan: {e}")
            raise