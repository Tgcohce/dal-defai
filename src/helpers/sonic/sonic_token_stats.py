import os
import logging
import requests
import time
from typing import Dict, Any, Optional
from web3 import Web3

logger = logging.getLogger("helpers.sonic.sonic_token_stats")
SONICSCAN_API_URL = "https://api.sonicscan.org/api"

# Default contract address for the $S token
DEFAULT_S_TOKEN_ADDRESS = "0x039e2fB66102314Ce7b64Ce5Ce3E5183bc94aD38"


class SonicTokenStats:
    """
    Provides token statistics for the $S token using Sonicscan's API.

    By default, the token contract address is hardcoded to $S (DEFAULT_S_TOKEN_ADDRESS),
    but users can override this by providing a different contract address.
    """

    @classmethod
    def get_token_balance(cls, wallet_address: str, token_address: Optional[str] = None) -> float:
        """
        Gets the ERC-20 token balance for a given wallet using Sonicscan.

        :param wallet_address: The Ethereum wallet address (0x...).
        :param token_address: (Optional) The ERC-20 token contract address.
                              Defaults to the $S token if not provided.
        :return: The balance as a floating point number (assuming 18 decimals).
        """
        if token_address is None:
            token_address = DEFAULT_S_TOKEN_ADDRESS

        api_key = os.getenv("SONICSCAN_API_KEY", "")
        if not api_key:
            raise ValueError("Missing SONICSCAN_API_KEY in your environment.")

        params = {
            "module": "account",
            "action": "tokenbalance",
            "contractaddress": token_address,
            "address": wallet_address,
            "tag": "latest",
            "apikey": api_key,
        }

        try:
            response = requests.get(SONICSCAN_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            if data.get("status") != "1":
                raise ValueError(f"Sonicscan returned error: {data.get('message')}")
            raw_balance_str = data.get("result", "0")
            raw_balance = float(raw_balance_str)

            # Assume 18 decimals for simplicity.
            decimals = 18
            balance = raw_balance / (10 ** decimals)
            logger.debug(f"Token balance for {wallet_address}: {balance} (raw: {raw_balance}, decimals: {decimals})")
            return balance

        except Exception as e:
            logger.error(f"Error fetching token balance from Sonicscan: {e}")
            raise

    @classmethod
    def get_token_purchase_history(cls, wallet_address: str, token_address: Optional[str] = None) -> Dict[str, Any]:
        """
        Returns token "purchase history" info using Sonicscan's tokentx endpoint.
        It computes:
          - first_purchase_timestamp: timestamp of the first inbound transfer.
          - time_since_last_sale: seconds since the last outbound transfer.
          - average_holding_time: average time difference between paired inbound and outbound events.

        :param wallet_address: The Ethereum wallet address.
        :param token_address: (Optional) The token contract address. Defaults to $S token.
        :return: A dictionary with purchase history data.
        """
        if token_address is None:
            token_address = DEFAULT_S_TOKEN_ADDRESS

        api_key = os.getenv("SONICSCAN_API_KEY", "")
        if not api_key:
            raise ValueError("Missing SONICSCAN_API_KEY in your environment.")

        params = {
            "module": "account",
            "action": "tokentx",
            "contractaddress": token_address,
            "address": wallet_address,
            "page": 1,
            "offset": 500,  # adjust pagination as needed
            "sort": "asc",
            "apikey": api_key,
        }
        try:
            response = requests.get(SONICSCAN_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            if data.get("status") != "1":
                logger.warning(f"Sonicscan tokentx returned error: {data.get('message')}")
                return {
                    "first_purchase_timestamp": None,
                    "time_since_last_sale": None,
                    "average_holding_time": None,
                }
            transfers = data.get("result", [])
            if not transfers:
                return {
                    "first_purchase_timestamp": None,
                    "time_since_last_sale": None,
                    "average_holding_time": None,
                }

            checksummed_wallet = Web3.to_checksum_address(wallet_address)
            first_inbound_time = None
            last_outbound_time = None
            total_hold_durations = 0.0
            inbound_events = []
            outbound_events = []

            for tx in transfers:
                to_addr = Web3.to_checksum_address(tx["to"])
                from_addr = Web3.to_checksum_address(tx["from"])
                tstamp = int(tx["timeStamp"])

                if to_addr == checksummed_wallet:
                    inbound_events.append(tstamp)
                    if first_inbound_time is None:
                        first_inbound_time = tstamp
                if from_addr == checksummed_wallet:
                    outbound_events.append(tstamp)
                    last_outbound_time = tstamp

            inbound_events.sort()
            outbound_events.sort()
            pair_count = min(len(inbound_events), len(outbound_events))
            for i in range(pair_count):
                hold_duration = outbound_events[i] - inbound_events[i]
                if hold_duration > 0:
                    total_hold_durations += hold_duration

            average_hold_time = (total_hold_durations / pair_count) if pair_count > 0 else None
            now_ts = int(time.time())
            time_since_last_sale = (now_ts - last_outbound_time) if last_outbound_time else None

            results = {
                "first_purchase_timestamp": first_inbound_time,
                "time_since_last_sale": time_since_last_sale,
                "average_holding_time": average_hold_time,
            }
            logger.debug(f"Purchase history for wallet {wallet_address}, token {token_address}: {results}")
            return results

        except Exception as e:
            logger.error(f"Failed to fetch token transfers from Sonicscan: {e}")
            raise
