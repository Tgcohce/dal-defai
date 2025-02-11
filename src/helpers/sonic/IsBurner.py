import requests

class isBurner:
    
    #Takes in 
    def __init__(self, wallet_address, api_key) -> bool:
        self.wallet_address = wallet_address
        self.api_key = api_key
        self.base_url = "" 