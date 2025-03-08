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

    @classmethod
    def _get_token_decimals(cls, token_address: str, api_key: str) -> Optional[int]:
        """
        Retrieve the token's decimal count. If already have
        a web3 connection for Sonic/Ethereum, you might prefer calling
        the contract directly. This example tries Etherscan's 'getsourcecode' 
        and parses the result for decimal info (some advanced usage).
        
        Alternatively, skip Etherscan entirely and do:
          web3 = Web3(Web3.HTTPProvider(RPC_URL))
          contract = web3.eth.contract(address=Web3.to_checksum_address(token_address), abi=ERC20_ABI)
          decimals = contract.functions.decimals().call()
        """
        
        try:
            # Using the "getsourcecode" module might not always provide decimals directly.
            url = f"{cls.BASE_URL}?module=contract&action=getsourcecode&address={token_address}&apikey={api_key}"
            resp = requests.get(url)
            resp.raise_for_status()
            data = resp.json()
            # This endpoint returns a list in "result".
            # The contract's verified source might have a "CompilerVersion" or "ABI" key can parse.
            if data["status"] == "1" and len(data["result"]) > 0:
                # If it's a verified contract, data["result"][0]["ABI"] might exist. 
                return None  # or some logic if a known pattern
            return None
        except Exception as e:
            logger.warning(f"Failed to fetch token decimals from Etherscan: {e}")
            return None
        
    @classmethod
    def get_token_purchase_history(cls, wallet_address: str, token_address: str) -> Dict[str, Any]:
        """
        Returns token “purchase history” info: 
          - timestamp of earliest known inbound transfer 
          - time since last outbound
          - average holding time, etc.

        For simplicity, we’ll focus on earliest inbound and last outbound.
        This uses Etherscan’s 'tokentx' endpoint, which lists ERC-20 transfers.

        :param wallet_address: The Ethereum wallet address (0x...).
        :param token_address: The ERC-20 token contract address (0x...).
        :return: A dictionary with relevant purchase/hold data.
        """
        etherscan_api_key = os.getenv("ETHERSCAN_API_KEY", "")
        if not etherscan_api_key:
            raise ValueError("Missing Etherscan API key. Set ETHERSCAN_API_KEY in your environment.")

        # Etherscan 'tokentx' endpoint:
        #   ?module=account&action=tokentx&contractaddress=token_address&address=wallet_address&sort=asc
        params = {
            "module": "account",
            "action": "tokentx",
            "contractaddress": token_address,
            "address": wallet_address,
            "page": 1,
            "offset": 500,  # up to 500 results, can paginate if you need more
            "sort": "asc",
            "apikey": etherscan_api_key,
        }

        try:
            response = requests.get(cls.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            if data["status"] != "1":
                # status can be "0" if no transactions found
                logger.warning(f"No transactions found or Etherscan error: {data.get('message')}")
                return {
                    "first_purchase_timestamp": None,
                    "time_since_last_sale": None,
                    "average_holding_time": None,
                }

            transfers = data.get("result", [])
            if not transfers:
                logger.debug("No token transfers returned from Etherscan.")
                return {
                    "first_purchase_timestamp": None,
                    "time_since_last_sale": None,
                    "average_holding_time": None,
                }

            # Convert addresses to checksum
            checksummed_wallet = Web3.to_checksum_address(wallet_address)

            # Find the earliest inbound transfer (“purchase”)
            first_inbound_time = None
            last_outbound_time = None
            inbound_blocks = 0
            total_hold_durations = 0.0
            inbound_events = []
            outbound_events = []

            for tx in transfers:
                to_addr = Web3.to_checksum_address(tx["to"])
                from_addr = Web3.to_checksum_address(tx["from"])
                tstamp = int(tx["timeStamp"])

                # inbound means the wallet was `to`
                if to_addr == checksummed_wallet:
                    inbound_events.append(tstamp)
                    if first_inbound_time is None:
                        first_inbound_time = tstamp
                # outbound means the wallet was `from`
                if from_addr == checksummed_wallet:
                    outbound_events.append(tstamp)
                    last_outbound_time = tstamp

            # For a quick approximation, can see time difference between inbound events and outbound events.
            inbound_events.sort()
            outbound_events.sort()

            if inbound_events and outbound_events:
                # Pair them up in some naive way for “average holding time.”
                # This is a simple hack. A robust approach would require analyzing each lot.
                pair_count = min(len(inbound_events), len(outbound_events))
                for i in range(pair_count):
                    hold_duration = outbound_events[i] - inbound_events[i]
                    if hold_duration > 0:
                        total_hold_durations += hold_duration

                if pair_count > 0:
                    average_hold_time = total_hold_durations / pair_count
                else:
                    average_hold_time = None
            else:
                average_hold_time = None

            # Convert to a friendlier output
            now_ts = int(time.time())
            time_since_last_sale = (now_ts - last_outbound_time) if last_outbound_time else None

            results = {
                "first_purchase_timestamp": first_inbound_time,  # Unix timestamp
                "time_since_last_sale": time_since_last_sale,    # seconds
                "average_holding_time": average_hold_time,       # seconds
            }
            logger.debug(f"Purchase history for wallet {wallet_address}, token {token_address}: {results}")
            return results

        except Exception as e:
            logger.error(f"Failed to fetch token transfers: {e}")
            raise