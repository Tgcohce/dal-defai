import requests

"""_summary_
    Returns the balance of a given wallet in ETH and ERC-20 tokens.
    Uses the Etherscan API for ETH balance and Covalent API for ERC-20 tokens.

    Returns: A dictionary containing ETH balance and token balances.
        _type_: dict _description_ Wallet balances in ETH and tokens.
"""
class getSizeOfWallet:
    def __init__(self, wallet_address, etherscan_api_key, covalent_api_key):
        self.wallet_address = wallet_address
        self.etherscan_api_key = etherscan_api_key
        self.covalent_api_key = covalent_api_key
        self.etherscan_url = "https://api.etherscan.io/api"
        self.covalent_url = f"https://api.covalenthq.com/v1/eth-mainnet/address/{wallet_address}/balances_v2/"

    def get_eth_balance(self):
        """Fetches the ETH balance of the wallet."""
        url = f"{self.etherscan_url}?module=account&action=balance&address={self.wallet_address}&tag=latest&apikey={self.etherscan_api_key}"
        response = requests.get(url)
        data = response.json()

        if data["status"] == "1":
            balance_wei = int(data["result"])
            balance_eth = balance_wei / 10**18  # Convert Wei to ETH
            return {"ETH Balance": f"{balance_eth} ETH"}
        else:
            return {"error": data["message"]}

    def get_all_token_balances(self):
        """Fetches all ERC-20 token balances of the wallet using Covalent API."""
        headers = {"Authorization": f"Bearer {self.covalent_api_key}"}
        response = requests.get(self.covalent_url, headers=headers)
        data = response.json()

        if "data" in data and "items" in data["data"]:
            tokens = data["data"]["items"]
            token_balances = {
                token["contract_ticker_symbol"]: f"{int(token['balance']) / 10**token['contract_decimals']} {token['contract_ticker_symbol']}"
                for token in tokens
            }
            return token_balances
        else:
            return {"error": "Unable to fetch token balances"}
        