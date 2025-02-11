import requests
from datetime import datetime

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
            return data["result"] #Limit to first 10,000 transactions [-10000:]
        else:
            return [] #If data is empty return an empty list    
    
    def get_wallet_start_date(self):
        
        #Get the start date of the wallet by checking the first transaction
        transactions = self.fetch_transactions()
        if transactions:
            first_tx_time = int(transactions[0]["timeStamp"])
            start_date = start_date = datetime.utcfromtimestamp(first_tx_time).strftime('%Y-%m-%d %H:%M:%S')
            return start_date
        else:
            return None