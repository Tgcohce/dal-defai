import requests

"""_summary_ 
    returns an array of all the transaction for the given wallet in json format. 
    uses etherscan api

    Returns: a array of transaction for the given wallet. 
        _type_: Array _description_ all transactions in a wallet.
    """
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
            transactions = data["result"][:10000] #Limit to first 10,000 transactions
            return transactions
        else:
            return [] #If data is empty return an empty list    