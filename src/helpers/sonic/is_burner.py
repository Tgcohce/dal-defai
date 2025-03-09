import logging
from src.helpers.sonic.sonic_transactions import GetTransactions

logger = logging.getLogger("helpers.sonic.is_burner")


class IsBurner:
    """
    Determines if a wallet behaves like a burner (rapid receive-and-send transactions).
    """

    def __init__(self, wallet_address: str):
        self.wallet_address = wallet_address.lower()
        self.tx_fetcher = GetTransactions(wallet_address)

    def check_burner(self) -> bool:
        """
        Checks if the wallet exhibits burner-like activity.
        """
        transactions = self.tx_fetcher.fetch_transactions()
        if not transactions:
            return False

        received = {}
        sent = {}
        burner_count = 0  # Count burner-like events

        for tx in transactions:
            from_addr = tx["from"].lower()
            to_addr = tx["to"].lower()
            try:
                value = float(tx["value"]) / 10 ** 18  # Convert from wei to ETH
            except Exception:
                value = 0.0
            timestamp = int(tx["timeStamp"])
            tx_hash = tx["hash"]

            if to_addr == self.wallet_address:
                received[tx_hash] = {"value": value, "timestamp": timestamp}
            if from_addr == self.wallet_address:
                sent[tx_hash] = {"value": value, "timestamp": timestamp}

        for r_hash, r_data in received.items():
            for s_hash, s_data in sent.items():
                time_diff = abs(s_data["timestamp"] - r_data["timestamp"])
                # If the sent amount closely matches the received and happens within 10 minutes
                if abs(r_data["value"] - s_data["value"]) < 0.001 and time_diff < 600:
                    burner_count += 1
                    if burner_count > 10:
                        return True
        return False
