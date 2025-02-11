import logging
import os
from dotenv import load_dotenv
from src.action_handler import register_action

logger = logging.getLogger("actions.sonic_actions")


@register_action("get-token-by-ticker")
def get_token_by_ticker(agent, **kwargs):
    """Get token address by ticker symbol."""
    try:
        ticker = kwargs.get("ticker")
        if not ticker:
            logger.error("No ticker provided")
            return None
        agent.connection_manager.connections["sonic"].get_token_by_ticker(ticker)
        return
    except Exception as e:
        logger.error(f"Failed to get token by ticker: {str(e)}")
        return None


@register_action("get-sonic-balance")
def get_sonic_balance(agent, **kwargs):
    """Get $S or token balance."""
    try:
        address = kwargs.get("address")
        token_address = kwargs.get("token_address")
        if not address:
            load_dotenv()
            private_key = os.getenv('SONIC_PRIVATE_KEY')
            web3 = agent.connection_manager.connections["sonic"]._web3
            account = web3.eth.account.from_key(private_key)
            address = account.address
        agent.connection_manager.connections["sonic"].get_balance(
            address=address,
            token_address=token_address
        )
        return
    except Exception as e:
        logger.error(f"Failed to get balance: {str(e)}")
        return None


@register_action("send-sonic")
def send_sonic(agent, **kwargs):
    """Send $S tokens to an address."""
    try:
        to_address = kwargs.get("to_address")
        amount = float(kwargs.get("amount"))
        agent.connection_manager.connections["sonic"].transfer(
            to_address=to_address,
            amount=amount
        )
        return
    except Exception as e:
        logger.error(f"Failed to send $S: {str(e)}")
        return None


@register_action("send-sonic-token")
def send_sonic_token(agent, **kwargs):
    """Send tokens on Sonic chain."""
    try:
        to_address = kwargs.get("to_address")
        token_address = kwargs.get("token_address")
        amount = float(kwargs.get("amount"))
        agent.connection_manager.connections["sonic"].transfer(
            to_address=to_address,
            amount=amount,
            token_address=token_address
        )
        return
    except Exception as e:
        logger.error(f"Failed to send tokens: {str(e)}")
        return None


@register_action("swap-sonic")
def swap_sonic(agent, **kwargs):
    """Swap tokens on Sonic chain."""
    try:
        token_in = kwargs.get("token_in")
        token_out = kwargs.get("token_out")
        amount = float(kwargs.get("amount"))
        slippage = float(kwargs.get("slippage", 0.5))
        agent.connection_manager.connections["sonic"].swap(
            token_in=token_in,
            token_out=token_out,
            amount=amount,
            slippage=slippage
        )
        return
    except Exception as e:
        logger.error(f"Failed to swap tokens: {str(e)}")
        return None


@register_action("calculate-credit-score")
def calculate_credit_score(agent, **kwargs):
    """
    Calculate an AI-based credit score for a given wallet by querying the blockchain.

    Expects:
      --wallet_address (required)
      Optionally, --start_block and --end_block for scanning a specific range.
    """
    try:
        wallet_address = kwargs.get("wallet_address")
        if not wallet_address:
            logger.error("No wallet address provided for credit score calculation.")
            return None
        start_block = kwargs.get("start_block")
        end_block = kwargs.get("end_block")
        wallet_metrics = agent.connection_manager.connections["sonic"].get_wallet_metrics(
            wallet_address, start_block=start_block, end_block=end_block
        )
        if not wallet_metrics:
            logger.error("Failed to retrieve wallet metrics from the blockchain.")
            return None

        # Example
        weights = {
            "num_transactions": 1.0,
            "account_age": 1.25,
            "avg_transaction_size": 0.5,
            "transaction_frequency": 1.0,
            "wallet_size": 1.0,
            "overall_gain_loss": 1.0,
            "rug_involvement": 2.0,
            "is_burner": 0.5
        }
        positive_sum = (
                wallet_metrics["num_transactions"] * weights["num_transactions"] +
                wallet_metrics["account_age"] * weights["account_age"] +
                wallet_metrics["avg_transaction_size"] * weights["avg_transaction_size"] +
                wallet_metrics["transaction_frequency"] * weights["transaction_frequency"] +
                wallet_metrics["wallet_size"] * weights["wallet_size"] +
                wallet_metrics["overall_gain_loss"] * weights["overall_gain_loss"]
        )
        negative_sum = (
                wallet_metrics["rug_involvement"] * weights["rug_involvement"] +
                (weights["is_burner"] if wallet_metrics["is_burner"] else 0)
        )
        raw_score = positive_sum - negative_sum

        # Assume theoretical range: raw_min = -2.5, raw_max = 6.25.
        raw_min = -2.5
        raw_max = 6.25
        normalized = (raw_score - raw_min) / (raw_max - raw_min)
        credit_score = int(300 + normalized * 550)

        logger.info(f"Calculated credit score for wallet {wallet_address}: {credit_score} "
                    f"(raw_score: {raw_score}, normalized: {normalized})")
        return credit_score

    except Exception as e:
        logger.error(f"Failed to calculate credit score for wallet: {str(e)}")
        return None
