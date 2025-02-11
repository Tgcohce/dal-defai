import logging
import os
import requests
import time
from typing import Dict, Any, Optional
from dotenv import load_dotenv, set_key
from web3 import Web3
from web3.middleware import geth_poa_middleware
from src.constants.abi import ERC20_ABI
from src.connections.base_connection import BaseConnection, Action, ActionParameter
from src.constants.networks import SONIC_NETWORKS

logger = logging.getLogger("connections.sonic_connection")


class SonicConnectionError(Exception):
    """Base exception for Sonic connection errors"""
    pass


class SonicConnection(BaseConnection):

    def __init__(self, config: Dict[str, Any]):
        logger.info("Initializing Sonic connection...")
        self._web3 = None

        # Get network configuration
        network = config.get("network", "mainnet")
        if network not in SONIC_NETWORKS:
            raise ValueError(f"Invalid network '{network}'. Must be one of: {', '.join(SONIC_NETWORKS.keys())}")

        network_config = SONIC_NETWORKS[network]
        self.explorer = network_config["scanner_url"]
        self.rpc_url = network_config["rpc_url"]

        super().__init__(config)
        self._initialize_web3()
        self.ERC20_ABI = ERC20_ABI
        self.NATIVE_TOKEN = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"
        self.aggregator_api = "https://aggregator-api.kyberswap.com/sonic/api/v1"

    def _get_explorer_link(self, tx_hash: str) -> str:
        """Generate block explorer link for transaction"""
        return f"{self.explorer}/tx/{tx_hash}"

    def _initialize_web3(self):
        """Initialize Web3 connection"""
        if not self._web3:
            self._web3 = Web3(Web3.HTTPProvider(self.rpc_url))
            self._web3.middleware_onion.inject(geth_poa_middleware, layer=0)
            if not self._web3.is_connected():
                raise SonicConnectionError("Failed to connect to Sonic network")

            try:
                chain_id = self._web3.eth.chain_id
                logger.info(f"Connected to network with chain ID: {chain_id}")
            except Exception as e:
                logger.warning(f"Could not get chain ID: {e}")

    @property
    def is_llm_provider(self) -> bool:
        return False

    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Sonic configuration from JSON"""
        required = ["network"]
        missing = [field for field in required if field not in config]
        if missing:
            raise ValueError(f"Missing config fields: {', '.join(missing)}")

        if config["network"] not in SONIC_NETWORKS:
            raise ValueError(
                f"Invalid network '{config['network']}'. Must be one of: {', '.join(SONIC_NETWORKS.keys())}")

        return config

    def get_token_by_ticker(self, ticker: str) -> Optional[str]:
        """Get token address by ticker symbol"""
        try:
            if ticker.lower() in ["s", "S"]:
                return "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"

            response = requests.get(
                f"https://api.dexscreener.com/latest/dex/search?q={ticker}"
            )
            response.raise_for_status()

            data = response.json()
            if not data.get('pairs'):
                return None

            sonic_pairs = [
                pair for pair in data["pairs"] if pair.get("chainId") == "sonic"
            ]
            sonic_pairs.sort(key=lambda x: x.get("fdv", 0), reverse=True)

            sonic_pairs = [
                pair for pair in sonic_pairs
                if pair.get("baseToken", {}).get("symbol", "").lower() == ticker.lower()
            ]

            if sonic_pairs:
                return sonic_pairs[0].get("baseToken", {}).get("address")
            return None

        except Exception as error:
            logger.error(f"Error fetching token address: {str(error)}")
            return None

    def register_actions(self) -> None:
        self.actions = {
            "get-token-by-ticker": Action(
                name="get-token-by-ticker",
                parameters=[
                    ActionParameter("ticker", True, str, "Token ticker symbol to look up")
                ],
                description="Get token address by ticker symbol"
            ),
            "get-balance": Action(
                name="get-balance",
                parameters=[
                    ActionParameter("address", False, str, "Address to check balance for"),
                    ActionParameter("token_address", False, str, "Optional token address")
                ],
                description="Get $S or token balance"
            ),
            "transfer": Action(
                name="transfer",
                parameters=[
                    ActionParameter("to_address", True, str, "Recipient address"),
                    ActionParameter("amount", True, float, "Amount to transfer"),
                    ActionParameter("token_address", False, str, "Optional token address")
                ],
                description="Send $S or tokens"
            ),
            "swap": Action(
                name="swap",
                parameters=[
                    ActionParameter("token_in", True, str, "Input token address"),
                    ActionParameter("token_out", True, str, "Output token address"),
                    ActionParameter("amount", True, float, "Amount to swap"),
                    ActionParameter("slippage", False, float, "Max slippage percentage")
                ],
                description="Swap tokens"
            )
        }

    def configure(self) -> bool:
        logger.info("\n🔷 SONIC CHAIN SETUP")
        if self.is_configured():
            logger.info("Sonic connection is already configured")
            response = input("Do you want to reconfigure? (y/n): ")
            if response.lower() != 'y':
                return True

        try:
            if not os.path.exists('.env'):
                with open('.env', 'w') as f:
                    f.write('')

            private_key = input("\nEnter your wallet private key: ")
            if not private_key.startswith('0x'):
                private_key = '0x' + private_key
            set_key('.env', 'SONIC_PRIVATE_KEY', private_key)

            if not self._web3.is_connected():
                raise SonicConnectionError("Failed to connect to Sonic network")

            account = self._web3.eth.account.from_key(private_key)
            logger.info(f"\n✅ Successfully connected with address: {account.address}")
            return True

        except Exception as e:
            logger.error(f"Configuration failed: {e}")
            return False

    def is_configured(self, verbose: bool = False) -> bool:
        try:
            load_dotenv()
            if not os.getenv('SONIC_PRIVATE_KEY'):
                if verbose:
                    logger.error("Missing SONIC_PRIVATE_KEY in .env")
                return False

            if not self._web3.is_connected():
                if verbose:
                    logger.error("Not connected to Sonic network")
                return False
            return True

        except Exception as e:
            if verbose:
                logger.error(f"Configuration check failed: {e}")
            return False

    def get_balance(self, address: Optional[str] = None, token_address: Optional[str] = None) -> float:
        """Get balance for an address or the configured wallet"""
        try:
            if not address:
                private_key = os.getenv('SONIC_PRIVATE_KEY')
                if not private_key:
                    raise SonicConnectionError("No wallet configured")
                account = self._web3.eth.account.from_key(private_key)
                address = account.address

            if token_address:
                contract = self._web3.eth.contract(
                    address=Web3.to_checksum_address(token_address),
                    abi=self.ERC20_ABI
                )
                balance = contract.functions.balanceOf(address).call()
                decimals = contract.functions.decimals().call()
                return balance / (10 ** decimals)
            else:
                balance = self._web3.eth.get_balance(address)
                return self._web3.from_wei(balance, 'ether')

        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            raise

    def transfer(self, to_address: str, amount: float, token_address: Optional[str] = None) -> str:
        """Send $S or tokens to an address"""
        try:
            private_key = os.getenv('SONIC_PRIVATE_KEY')
            account = self._web3.eth.account.from_key(private_key)
            chain_id = self._web3.eth.chain_id

            if token_address:
                contract = self._web3.eth.contract(
                    address=Web3.to_checksum_address(token_address),
                    abi=self.ERC20_ABI
                )
                decimals = contract.functions.decimals().call()
                amount_raw = int(amount * (10 ** decimals))

                tx = contract.functions.transfer(
                    Web3.to_checksum_address(to_address),
                    amount_raw
                ).build_transaction({
                    'from': account.address,
                    'nonce': self._web3.eth.get_transaction_count(account.address),
                    'gasPrice': self._web3.eth.gas_price,
                    'chainId': chain_id
                })
            else:
                tx = {
                    'nonce': self._web3.eth.get_transaction_count(account.address),
                    'to': Web3.to_checksum_address(to_address),
                    'value': self._web3.to_wei(amount, 'ether'),
                    'gas': 21000,
                    'gasPrice': self._web3.eth.gas_price,
                    'chainId': chain_id
                }

            signed = account.sign_transaction(tx)
            tx_hash = self._web3.eth.send_raw_transaction(signed.rawTransaction)
            tx_link = self._get_explorer_link(tx_hash.hex())
            return f"⛓️ Transfer transaction sent: {tx_link}"

        except Exception as e:
            logger.error(f"Failed to send $S: {e}")
            raise

    def _get_swap_route(self, token_in: str, token_out: str, amount_in: float) -> Dict:
        """Get the best swap route from Kyberswap API"""
        try:
            if token_in.lower() == self.NATIVE_TOKEN.lower():
                amount_raw = self._web3.to_wei(amount_in, 'ether')
            else:
                token_contract = self._web3.eth.contract(
                    address=Web3.to_checksum_address(token_in),
                    abi=self.ERC20_ABI
                )
                decimals = token_contract.functions.decimals().call()
                amount_raw = int(amount_in * (10 ** decimals))

            url = f"{self.aggregator_api}/routes"
            headers = {"x-client-id": "ZerePyBot"}
            params = {
                "tokenIn": token_in,
                "tokenOut": token_out,
                "amountIn": str(amount_raw),
                "gasInclude": "true"
            }

            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            if data.get("code") != 0:
                raise SonicConnectionError(f"API error: {data.get('message')}")
            return data["data"]

        except Exception as e:
            logger.error(f"Failed to get swap route: {e}")
            raise

    def _get_encoded_swap_data(self, route_summary: Dict, slippage: float = 0.5) -> str:
        """Get encoded swap data from Kyberswap API"""
        try:
            private_key = os.getenv('SONIC_PRIVATE_KEY')
            account = self._web3.eth.account.from_key(private_key)

            url = f"{self.aggregator_api}/route/build"
            headers = {"x-client-id": "zerepy"}

            payload = {
                "routeSummary": route_summary,
                "sender": account.address,
                "recipient": account.address,
                "slippageTolerance": int(slippage * 100),
                "deadline": int(time.time() + 1200),
                "source": "ZerePyBot"
            }

            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            if data.get("code") != 0:
                raise SonicConnectionError(f"API error: {data.get('message')}")
            return data["data"]["data"]

        except Exception as e:
            logger.error(f"Failed to encode swap data: {e}")
            raise

    def _handle_token_approval(self, token_address: str, spender_address: str, amount: int) -> None:
        """Handle token approval for spender"""
        try:
            private_key = os.getenv('SONIC_PRIVATE_KEY')
            account = self._web3.eth.account.from_key(private_key)

            token_contract = self._web3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=self.ERC20_ABI
            )

            current_allowance = token_contract.functions.allowance(
                account.address,
                spender_address
            ).call()

            if current_allowance < amount:
                approve_tx = token_contract.functions.approve(
                    spender_address,
                    amount
                ).build_transaction({
                    'from': account.address,
                    'nonce': self._web3.eth.get_transaction_count(account.address),
                    'gasPrice': self._web3.eth.gas_price,
                    'chainId': self._web3.eth.chain_id
                })

                signed_approve = account.sign_transaction(approve_tx)
                tx_hash = self._web3.eth.send_raw_transaction(signed_approve.rawTransaction)
                logger.info(f"Approval transaction sent: {self._get_explorer_link(tx_hash.hex())}")
                self._web3.eth.wait_for_transaction_receipt(tx_hash)

        except Exception as e:
            logger.error(f"Approval failed: {e}")
            raise

    def swap(self, token_in: str, token_out: str, amount: float, slippage: float = 0.5) -> str:
        """Execute a token swap using the KyberSwap router"""
        try:
            private_key = os.getenv('SONIC_PRIVATE_KEY')
            account = self._web3.eth.account.from_key(private_key)

            current_balance = self.get_balance(
                address=account.address,
                token_address=None if token_in.lower() == self.NATIVE_TOKEN.lower() else token_in
            )

            if current_balance < amount:
                raise ValueError(f"Insufficient balance. Required: {amount}, Available: {current_balance}")

            route_data = self._get_swap_route(token_in, token_out, amount)
            encoded_data = self._get_encoded_swap_data(route_data["routeSummary"], slippage)
            router_address = route_data["routerAddress"]

            if token_in.lower() != self.NATIVE_TOKEN.lower():
                if token_in.lower() == "0x039e2fb66102314ce7b64ce5ce3e5183bc94ad38".lower():
                    amount_raw = self._web3.to_wei(amount, 'ether')
                else:
                    token_contract = self._web3.eth.contract(
                        address=Web3.to_checksum_address(token_in),
                        abi=self.ERC20_ABI
                    )
                    decimals = token_contract.functions.decimals().call()
                    amount_raw = int(amount * (10 ** decimals))
                self._handle_token_approval(token_in, router_address, amount_raw)

            tx = {
                'from': account.address,
                'to': Web3.to_checksum_address(router_address),
                'data': encoded_data,
                'nonce': self._web3.eth.get_transaction_count(account.address),
                'gasPrice': self._web3.eth.gas_price,
                'chainId': self._web3.eth.chain_id,
                'value': self._web3.to_wei(amount, 'ether') if token_in.lower() == self.NATIVE_TOKEN.lower() else 0
            }

            try:
                tx['gas'] = self._web3.eth.estimate_gas(tx)
            except Exception as e:
                logger.warning(f"Gas estimation failed: {e}, using default gas limit")
                tx['gas'] = 500000

            signed_tx = account.sign_transaction(tx)
            tx_hash = self._web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            tx_link = self._get_explorer_link(tx_hash.hex())
            return f"🔄 Swap transaction sent: {tx_link}"

        except Exception as e:
            logger.error(f"Swap failed: {e}")
            raise

    # -------------------------------
    # New method: Get wallet metrics by scanning the blockchain.
    # -------------------------------
    def get_wallet_metrics(self, wallet_address: str, start_block: int = None, end_block: int = None) -> Dict[
        str, float]:
        """
        Scan the blockchain for the given wallet address and compute real metrics.

        Metrics computed (all normalized to [0,1] using assumed thresholds):
          - num_transactions: Total transactions (as sender or receiver)
          - wallet_size: Current balance in ETH
          - account_age: Time since first transaction (in seconds)
          - avg_transaction_size: Average value of outgoing transactions (in ETH)
          - transaction_frequency: Transactions per second
          - overall_gain_loss: Net flow (incoming - outgoing)
          - rug_involvement: Placeholder (DOWN influence)
          - is_burner: 1 if very few transactions and low balance, else 0

        Parameters:
          wallet_address: The Ethereum address to scan.
          start_block: Starting block number for the scan. (If None, defaults to current_block - 5000)
          end_block: Ending block number for the scan. (If None, defaults to the latest block)

        Note: Scanning from genesis can be extremely heavy. Adjust the block range as needed.
        """
        wallet_address = Web3.to_checksum_address(wallet_address)
        current_block = self._web3.eth.get_block('latest', full_transactions=False)
        end_block = end_block or current_block.number
        start_block = start_block or max(0, end_block - 5000)

        txs = []  # All transactions involving wallet
        txs_sent = []  # Outgoing transactions
        txs_received = []  # Incoming transactions
        earliest_timestamp = None

        logger.info(f"Scanning blocks {start_block} to {end_block} for wallet {wallet_address}...")

        for block_num in range(start_block, end_block + 1):
            try:
                block = self._web3.eth.get_block(block_num, full_transactions=True)
            except Exception as e:
                logger.error(f"Error fetching block {block_num}: {e}")
                continue

            block_timestamp = block.timestamp
            for tx in block.transactions:
                tx_from = tx.get('from')
                tx_to = tx.get('to')
                if (tx_from and Web3.to_checksum_address(tx_from) == wallet_address) or \
                        (tx_to and Web3.to_checksum_address(tx_to) == wallet_address):
                    txs.append((tx, block_timestamp))
                    if earliest_timestamp is None or block_timestamp < earliest_timestamp:
                        earliest_timestamp = block_timestamp
                    if tx_from and Web3.to_checksum_address(tx_from) == wallet_address:
                        txs_sent.append((tx, block_timestamp))
                    if tx_to and Web3.to_checksum_address(tx_to) == wallet_address:
                        txs_received.append((tx, block_timestamp))

        current_timestamp = current_block.timestamp

        total_tx_count = len(txs)
        normalized_tx_count = min(total_tx_count / 1000.0, 1.0)

        try:
            balance_wei = self._web3.eth.get_balance(wallet_address)
            balance_eth = float(self._web3.from_wei(balance_wei, 'ether'))
        except Exception as e:
            logger.error(f"Error getting balance for {wallet_address}: {e}")
            balance_eth = 0.0
        normalized_balance = min(balance_eth / 1000.0, 1.0)

        if earliest_timestamp is None:
            account_age = 0
        else:
            account_age = current_timestamp - earliest_timestamp
        normalized_account_age = min(account_age / 315360000.0, 1.0)

        total_sent = sum(float(self._web3.from_wei(tx['value'], 'ether')) for tx, _ in txs_sent)
        avg_tx_size = (total_sent / len(txs_sent)) if txs_sent else 0.0
        normalized_avg_tx_size = min(avg_tx_size / 100.0, 1.0)

        frequency = total_tx_count / (account_age if account_age > 0 else 1)
        normalized_frequency = min(frequency / (1.0 / 60.0), 1.0)

        total_incoming = sum(float(self._web3.from_wei(tx['value'], 'ether')) for tx, _ in txs_received)
        net_flow = total_incoming - total_sent
        normalized_net_flow = min(abs(net_flow) / 500.0, 1.0)

        normalized_rug_involvement = 0.1
        is_burner = 1.0 if (total_tx_count < 3 and balance_eth < 0.1) else 0.0

        metrics = {
            "num_transactions": normalized_tx_count,
            "wallet_size": normalized_balance,
            "account_age": normalized_account_age,
            "avg_transaction_size": normalized_avg_tx_size,
            "transaction_frequency": normalized_frequency,
            "overall_gain_loss": normalized_net_flow,
            "rug_involvement": normalized_rug_involvement,
            "is_burner": is_burner
        }

        logger.info(f"Scanned wallet {wallet_address}: found {total_tx_count} transactions, "
                    f"earliest tx at {earliest_timestamp if earliest_timestamp else 'N/A'}, "
                    f"current balance {balance_eth} ETH")
        logger.info(f"Computed metrics: {metrics}")
        return metrics
