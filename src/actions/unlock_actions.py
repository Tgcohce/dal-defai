import logging
from src.action_handler import register_action

logger = logging.getLogger("actions.unlock_actions")

# Define the market cap thresholds (in USD, for example)
UNLOCK_THRESHOLDS = {
    "telegram": 50000,        # Unlock Telegram features at $50K
    "twitter": 100000,        # Unlock Twitter features at $100K
    "wallet_analyzer": 250000,  # Unlock wallet analyzer at $250K
    "airdrops": 500000        # Unlock airdrops at $500K
}


def get_market_cap(agent):
    """
    Helper function to get the current market cap.
    In a real implementation, this would fetch real-time data.
    Here, we simulate it by returning the agent's market_cap attribute,
    or 0 if it's not set.
    """
    return getattr(agent, "market_cap", 0)


def is_feature_unlocked(agent, feature):
    """
    Check if a specific feature is unlocked based on the current market cap.
    """
    current_cap = get_market_cap(agent)
    threshold = UNLOCK_THRESHOLDS.get(feature)
    if threshold is None:
        logger.error(f"No threshold set for feature '{feature}'.")
        return False
    return current_cap >= threshold


@register_action("unlock-status")
def unlock_status(agent, **kwargs):
    """
    Check and report the unlocking status of various features based on market cap.
    Returns a dictionary of feature statuses.
    """
    current_cap = get_market_cap(agent)
    status = {}
    for feature, threshold in UNLOCK_THRESHOLDS.items():
        status[feature] = current_cap >= threshold
    agent.logger.info(f"Market Cap: {current_cap}. Unlock status: {status}")
    return status


@register_action("run-twitter-raid")
def run_twitter_raid(agent, **kwargs):
    """
    Run a Twitter raid automatically if the market cap threshold is met.
    """
    if is_feature_unlocked(agent, "twitter"):
        agent.logger.info("Twitter raid feature is unlocked. Initiating Twitter raid!")
        # Insert actual Twitter raid logic here...
        return True
    else:
        agent.logger.info("Twitter raid feature locked. Increase market cap to unlock (requires $100K).")
        return False


@register_action("send-telegram-announce")
def send_telegram_announce(agent, **kwargs):
    """
    Send a Telegram announcement if the market cap threshold is met.
    """
    if is_feature_unlocked(agent, "telegram"):
        message = kwargs.get("message", "Default announcement message.")
        agent.logger.info("Telegram announcement feature unlocked. Sending announcement...")
        # Use the telegram connection to send a message.
        agent.connection_manager.perform_action(
            connection_name="telegram",
            action_name="send-message",
            params=[message]
        )
        return True
    else:
        agent.logger.info("Telegram announcement feature locked. Increase market cap to unlock (requires $50K).")
        return False


@register_action("run-wallet-analyzer")
def run_wallet_analyzer(agent, **kwargs):
    """
    Run the wallet analyzer if the market cap threshold is met.
    """
    if is_feature_unlocked(agent, "wallet_analyzer"):
        agent.logger.info("Wallet analyzer feature unlocked. Running wallet analysis...")
        # Insert wallet analysis logic here. For now, we simulate the result.
        analysis_result = {"analysis": "Dummy wallet analysis data."}
        return analysis_result
    else:
        agent.logger.info("Wallet analyzer feature locked. Increase market cap to unlock (requires $250K).")
        return None


@register_action("trigger-airdrops")
def trigger_airdrops(agent, **kwargs):
    """
    Trigger airdrops to good holders if the market cap threshold is met.
    """
    if is_feature_unlocked(agent, "airdrops"):
        agent.logger.info("Airdrops feature unlocked. Triggering airdrops to eligible holders!")
        # Insert airdrop logic here...
        return True
    else:
        agent.logger.info("Airdrops feature locked. Increase market cap to unlock (requires $500K).")
        return False
