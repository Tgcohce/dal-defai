import os
import logging
import requests
from typing import Dict, Any, Optional, List

class SonicReader:
    """
    A utility class to read data from Etherscan API.
    This is a simplified version that provides basic functionality
    needed by the SonicConnection class.
    """

    BASE_URL = "https://api.sonicscan.org/api"
    
    @classmethod
    def get_token_info(cls, token_address: str) -> Dict[str, Any]:
        """
        Gets information about a token from Etherscan.
        
        Args:
            token_address: The Ethereum address of the token contract
            
        Returns:
            A dictionary with token information
        """
        sonicscan_api_key = os.getenv("SONICSCAN_API_KEY")
        if not sonicscan_api_key:
            logging.warning("SONICSCAN_API_KEY not found in environment variables")
            return {"error": "API key not found"}
            
        params = {
            "module": "token",
            "action": "tokeninfo",
            "contractaddress": token_address,
            "apikey": sonicscan_api_key
        }
        
        try:
            response = requests.get(cls.BASE_URL, params=params)
            data = response.json()
            
            if data["status"] == "1":
                return data["result"]
            else:
                return {"error": data.get("message", "Unknown error")}
        except Exception as e:
            logging.error(f"Error fetching token info: {e}")
            return {"error": str(e)}
    
    @classmethod
    def get_token_by_ticker(cls, ticker: str) -> Optional[str]:
        """
        Attempts to find a token address by its ticker symbol.
        This is a basic implementation - in a real system, you would
        likely need a more sophisticated approach or a larger database.
        
        Args:
            ticker: The ticker symbol to look up (e.g. "ETH", "USDC")
            
        Returns:
            The token address if found, None otherwise
        """
        # This is just a small sample of common tokens - in a real system,
        # you would want a more comprehensive database or API call
        common_tokens = {
            "ETH": "0x0000000000000000000000000000000000000000",  # Native ETH
            "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
            "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
            "SONIC": "0xf8f34fA82D1f49C0E70A969E1a5cEDD36C196429"  # Example - replace with actual SONIC address
        }
        
        return common_tokens.get(ticker.upper())
    
    @classmethod
    def get_token_balance(cls, wallet_address: str, token_address: str = None) -> Dict[str, Any]:
        """
        Gets the balance of a token for a wallet.
        
        Args:
            wallet_address: The wallet address to check
            token_address: The token contract address, or None for ETH
            
        Returns:
            A dictionary with the balance information
        """
        sonicscan_api_key = os.getenv("SONICSCAN_API_KEY")
        if not sonicscan_api_key:
            logging.warning("SONICSCAN_API_KEY not found in environment variables")
            return {"error": "API key not found"}
        
        if token_address is None or token_address == "0x0000000000000000000000000000000000000000":
            # SONIC balance (native token)
            params = {
                "module": "account",
                "action": "balance",
                "address": wallet_address,
                "tag": "latest",
                "apikey": sonicscan_api_key
            }
        else:
            # ERC20 token balance
            params = {
                "module": "account",
                "action": "tokenbalance",
                "contractaddress": token_address,
                "address": wallet_address,
                "tag": "latest",
                "apikey": sonicscan_api_key
            }
        
        try:
            response = requests.get(cls.BASE_URL, params=params)
            data = response.json()
            
            if data["status"] == "1":
                raw_balance = int(data["result"])
                
                # For ETH, convert Wei to ETH
                if token_address is None or token_address == "0x0000000000000000000000000000000000000000":
                    balance = raw_balance / 10**18
                    return {"balance": balance, "symbol": "SONIC", "decimals": 18}
                
                # For ERC20 tokens, need to get decimals
                token_info = cls.get_token_info(token_address)
                decimals = int(token_info.get("decimals", 18))
                symbol = token_info.get("symbol", "UNKNOWN")
                
                balance = raw_balance / 10**decimals
                return {"balance": balance, "symbol": symbol, "decimals": decimals}
            else:
                return {"error": data.get("message", "Unknown error")}
        except Exception as e:
            logging.error(f"Error fetching token balance: {e}")
            return {"error": str(e)}
