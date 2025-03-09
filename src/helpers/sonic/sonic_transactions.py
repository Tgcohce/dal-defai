import requests
import logging
import os
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("helpers.sonic.sonic_transactions")

SONICSCAN_API_URL = "https://api.sonicscan.org/api"

class GetTransactions:
    """
    Returns an array of all transactions for the given wallet in JSON format using Sonicscan.
    """

    def __init__(self, wallet_address: str):
        self.wallet_address = wallet_address

    def fetch_transactions(self, startblock: int = 0, endblock: int = 99999999,
                           page: int = 1, offset: int = 100, sort: str = "asc") -> list:
        """
        Gets transaction history of the wallet using the txlist endpoint.
        """
        api_key = os.getenv("SONICSCAN_API_KEY", "")
        params = {
            "module": "account",
            "action": "txlist",
            "address": self.wallet_address,
            "startblock": startblock,
            "endblock": endblock,
            "page": page,
            "offset": offset,
            "sort": sort,
            "apikey": api_key,
        }
        try:
            response = requests.get(SONICSCAN_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "1":
                return data.get("result", [])
            else:
                logger.warning(f"Sonicscan txlist returned error: {data.get('message')}")
                return []
        except Exception as e:
            logger.error(f"Error fetching transactions: {e}")
            return []

    def get_wallet_start_date(self) -> Optional[str]:
        """
        Returns the start date (UTC) of the wallet by converting the timestamp of the first transaction.
        """
        transactions = self.fetch_transactions(offset=1, sort="asc")
        if transactions:
            first_tx_time = int(transactions[0]["timeStamp"])
            start_date = datetime.fromtimestamp(first_tx_time, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            return start_date
        else:
            return None
