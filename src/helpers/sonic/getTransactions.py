import requests

class getTransactions:
    def __init__(self, wallet_address, api_key):
        self.wallet_address = wallet_address
        self.api_key = api_key
        self.base_url = "https://api.etherscan.io/api"
    
    def fetch_transactions(self):
        """Gets transaction history of the wallet."""
        url = f"{self.base_url}?module=account&action=txlist&address={self.wallet}&apikey={self.api_key}"
        response = requests.get(url)
        data = response.json()
        
        #If data return the results.
        if data["status"] == "1":
            return data["result"]
        else:
            return [] #If data is empty return an empty list    