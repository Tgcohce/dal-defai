import requests
from getTransactions import GetTransactions

"""_summary_
    This class returns True or False depending on if the wallet is flagged for burner activities
    A burner is an account that recives a transaction, 
    then instantly sends that transaction away multiple times.

    Returns:
        _type_: Boolean 
        _description_ Returns True or False depending on if the account acts like a burner
     """

class isBurner:
    
    #Takes in wallet address, api key
    def __init__(self, wallet_address, api_key):
        self.wallet = wallet_address.lower()
        self.tx_fetcher = GetTransactions(wallet_address, api_key)
        
    
    def check_burner(self):
        """Determin if wallet acts like a burner. 
        (wallet recives funds then sends same funds)"""
        transactions = self.tx_fetcher.fetch_transactions()
        if not transactions:
            #No transactions found
            return False
        
        received = {}
        sent = {}
        burner_count = 0
        
        for tx in transactions:
            from_addr = tx["from"].lower()
            to_addr = tx["to"].lower()
            value = int(tx["value"]) / 10**8 # Conversion rate, (WEI to ETH) 
            timestamp = int(tx["timeStamp"]) # Transaction time
            tx_hash = tx["hash"]
            
            if to_addr == self.wallet:
                received[tx_hash] = {"value": value, "timestamp": timestamp}
                
            if from_addr == self.wallet:
                sent[tx_hash] = {"value": value, "timestamp": timestamp}
            
        for r_data in received.items():
            for s_data in sent.items():
                time_diff = abs(s_data["timeStamp"] - r_data["timeStamp"])
                if abs(r_data["value"] - s_data["value"]) < 0.001 and time_diff < 600:
                    burner_count += 1
                    if burner_count > 10: 
                        return True
        
        
        return False