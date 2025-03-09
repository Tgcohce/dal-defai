import requests
import logging
import os

logger = logging.getLogger("helpers.sonic.sonic_wallet_size")

SONICSCAN_API_URL = "https://api.sonicscan.org/api"

class SonicWalletSize:
    """
    Returns the balance of a given wallet in ETH and ERC-20 tokens using Sonicscan.
    """

    def __init__(self, wallet_address: str):
        self.wallet_address = wallet_address

    def get_eth_balance(self):
        """Fetches the ETH balance of the wallet using Sonicscan."""
        api_key = os.getenv("SONICSCAN_API_KEY", "")
        url = SONICSCAN_API_URL
        params = {
            "module": "account",
            "action": "balance",
            "address": self.wallet_address,
            "tag": "latest",
            "apikey": api_key,
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "1":
                balance_wei = int(data.get("result", "0"))
                balance_eth = balance_wei / 10**18
                return {"SONIC Balance": f"{balance_eth} SONIC"}
            else:
                return {"error": data.get("message", "Unknown error")}
        except Exception as e:
            logger.error(f"Error fetching ETH balance: {e}")
            return {"error": str(e)}

    def get_all_token_balances(self):
        """
        Fetches token balances by iterating over a predefined list of token contract addresses.
        (Since Sonicscan does not offer an endpoint to list all tokens for a wallet.)
        """
        # Replace or extend this dictionary with token ticker: contract_address mappings
        tokens = {
            "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
            "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
            # Add your own tokens as needed
        }
        api_key = os.getenv("SONICSCAN_API_KEY", "")
        url = SONICSCAN_API_URL
        token_balances = {}
        for symbol, contract_address in tokens.items():
            params = {
                "module": "account",
                "action": "tokenbalance",
                "contractaddress": contract_address,
                "address": self.wallet_address,
                "tag": "latest",
                "apikey": api_key,
            }
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                if data.get("status") == "1":
                    raw_balance = float(data.get("result", "0"))
                    # Without a dedicated endpoint for decimals, assume 18; you can improve this by using SonicReader.get_token_info
                    decimals = 18
                    balance = raw_balance / (10 ** decimals)
                    token_balances[symbol] = f"{balance} {symbol}"
                else:
                    token_balances[symbol] = f"Error: {data.get('message', 'Unknown error')}"
            except Exception as e:
                logger.error(f"Error fetching token balance for {symbol}: {e}")
                token_balances[symbol] = f"Error: {str(e)}"
        return token_balances
