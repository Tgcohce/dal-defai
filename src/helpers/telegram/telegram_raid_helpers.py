import logging
import os
import requests
import asyncio
from dotenv import load_dotenv
from src.action_handler import register_action

logger = logging.getLogger("helpers.telegram_raid_helpers")
load_dotenv()  # Ensure environment variables are loaded


def get_token_marketcap(token_symbol: str) -> float:
    """
    Retrieve the market cap for a given token using the Etherscan API.
    Requires the following environment variables:
      - TOKEN_CONTRACT_ADDRESS: The token's contract address.
      - ETHERSCAN_API_KEY: Your Etherscan API key.
      - TOKEN_PRICE_USD: The current token price in USD.
    Returns the market cap in USD or 0.0 if not available.
    """
    contract_address = os.getenv("TOKEN_CONTRACT_ADDRESS")
    etherscan_api_key = os.getenv("ETHERSCAN_API_KEY")
    token_price = os.getenv("TOKEN_PRICE_USD")
    if not contract_address or not etherscan_api_key or not token_price:
        logger.error("Missing TOKEN_CONTRACT_ADDRESS, ETHERSCAN_API_KEY, or TOKEN_PRICE_USD in environment.")
        return 0.0
    try:
        url = (
            f"https://api.etherscan.io/api?"
            f"module=stats&action=tokensupply&contractaddress={contract_address}&apikey={etherscan_api_key}"
        )
        response = requests.get(url)
        if response.status_code != 200:
            logger.error(f"Failed to fetch token supply: HTTP {response.status_code}")
            return 0.0
        data = response.json()
        if data.get("status") != "1":
            logger.error(f"Etherscan API error: {data.get('message')}")
            return 0.0
        supply_str = data.get("result")
        token_supply = float(supply_str)
        token_price_float = float(token_price)
        market_cap = token_supply * token_price_float
        logger.info(f"Market cap for {token_symbol}: {market_cap} USD")
        return market_cap
    except Exception as e:
        logger.error(f"Error fetching market cap for {token_symbol}: {e}")
        return 0.0


def get_unlocked_features(market_cap: float) -> list:
    """
    Determine unlocked features based on market cap thresholds (in USD):
      - 50k: Telegram raids unlocked
      - 100k: Twitter raids unlocked
      - 250k: Wallet Analyzer unlocked
      - 500k: Airdrops unlocked
    Returns a list of feature names.
    """
    features = []
    if market_cap >= 50000:
        features.append("Telegram raids")
    if market_cap >= 100000:
        features.append("Twitter raids")
    if market_cap >= 250000:
        features.append("Wallet Analyzer")
    if market_cap >= 500000:
        features.append("Airdrops")
    return features


def send_raid_command(telegram_bot, group_chat_id: int, raid_command: str) -> None:
    """
    Send a raid command message to a specified Telegram group chat.
    """
    try:
        telegram_bot.send_message(chat_id=group_chat_id, text=raid_command)
        logger.info(f"Raid command '{raid_command}' sent to group chat {group_chat_id}")
    except Exception as e:
        logger.error(f"Failed to send raid command to group chat {group_chat_id}: {e}")


@register_action("start-twitter-raid")
def start_twitter_raid(agent, **kwargs):
    """
    Action to start a Twitter raid via Telegram.

    Expects:
      - group_chat_id (int): Telegram group chat ID where the raid command will be sent.
      - raid_command (str): The command message to send (e.g., "/raid start").
    """
    try:
        group_chat_id = kwargs.get("group_chat_id")
        raid_command = kwargs.get("raid_command")
        if not group_chat_id or not raid_command:
            agent.logger.error("Missing parameters: 'group_chat_id' and 'raid_command' are required.")
            return None

        telegram_connection = agent.connection_manager.connections.get("telegram")
        if not telegram_connection:
            agent.logger.error("Telegram connection not configured.")
            return None

        telegram_bot = telegram_connection.app.bot
        send_raid_command(telegram_bot, int(group_chat_id), raid_command)
        agent.logger.info("Twitter raid initiated via Telegram.")
        return True
    except Exception as e:
        agent.logger.error(f"Failed to start Twitter raid on Telegram: {e}")
        return None


@register_action("stop-twitter-raid")
def stop_twitter_raid(agent, **kwargs):
    """
    Action to stop a Twitter raid via Telegram.

    Expects:
      - group_chat_id (int): Telegram group chat ID where the stop command will be sent.
      - raid_command (str): The command message to send (e.g., "/raid stop").
    """
    try:
        group_chat_id = kwargs.get("group_chat_id")
        raid_command = kwargs.get("raid_command")
        if not group_chat_id or not raid_command:
            agent.logger.error("Missing parameters: 'group_chat_id' and 'raid_command' are required.")
            return None

        telegram_connection = agent.connection_manager.connections.get("telegram")
        if not telegram_connection:
            agent.logger.error("Telegram connection not configured.")
            return None

        telegram_bot = telegram_connection.app.bot
        send_raid_command(telegram_bot, int(group_chat_id), raid_command)
        agent.logger.info("Twitter raid stopped via Telegram.")
        return True
    except Exception as e:
        agent.logger.error(f"Failed to stop Twitter raid on Telegram: {e}")
        return None


@register_action("get-unlocked-features")
def get_unlocked_features_action(agent, **kwargs):
    """
    Action to get the unlocked features based on the current token market cap.

    Expects:
      - token_symbol (str): The token symbol.
    Returns a list of unlocked feature names.
    """
    try:
        token_symbol = kwargs.get("token_symbol")
        if not token_symbol:
            agent.logger.error("Missing parameter: 'token_symbol' is required.")
            return None

        market_cap = get_token_marketcap(token_symbol)
        features = get_unlocked_features(market_cap)
        agent.logger.info(f"Unlocked features for {token_symbol}: {features}")
        return features
    except Exception as e:
        agent.logger.error(f"Failed to get unlocked features: {e}")
        return None


@register_action("announce-raid")
def announce_raid(agent, **kwargs):
    """
    Action to announce a raid in a Telegram group chat.

    Expects:
      - group_chat_id (int): Telegram group chat ID.
      - announcement (str): The announcement message to send.
    """
    try:
        group_chat_id = kwargs.get("group_chat_id")
        announcement = kwargs.get("announcement")
        if not group_chat_id or not announcement:
            agent.logger.error("Missing parameters: 'group_chat_id' and 'announcement' are required.")
            return None

        telegram_connection = agent.connection_manager.connections.get("telegram")
        if not telegram_connection:
            agent.logger.error("Telegram connection not configured.")
            return None

        telegram_bot = telegram_connection.app.bot
        telegram_bot.send_message(chat_id=int(group_chat_id), text=announcement)
        agent.logger.info(f"Raid announcement sent to group chat {group_chat_id}: {announcement}")
        return True
    except Exception as e:
        agent.logger.error(f"Failed to announce raid: {e}")
        return None


@register_action("get-marketcap")
def get_marketcap_action(agent, **kwargs):
    """
    Action to retrieve the market cap of a token.

    Expects:
      - token_symbol (str): The token symbol.
    Returns the market cap in USD.
    """
    try:
        token_symbol = kwargs.get("token_symbol")
        if not token_symbol:
            agent.logger.error("Missing parameter: 'token_symbol' is required.")
            return None

        market_cap = get_token_marketcap(token_symbol)
        agent.logger.info(f"Market cap for {token_symbol}: {market_cap} USD")
        return market_cap
    except Exception as e:
        agent.logger.error(f"Failed to retrieve market cap: {e}")
        return None


@register_action("schedule-raid")
def schedule_raid(agent, **kwargs):
    """
    Action to schedule a raid command to be executed after a specified delay.

    Expects:
      - group_chat_id (int): Telegram group chat ID.
      - raid_command (str): The command message to send.
      - delay_seconds (int): Delay in seconds before executing the raid command.
    """
    try:
        group_chat_id = kwargs.get("group_chat_id")
        raid_command = kwargs.get("raid_command")
        delay_seconds = int(kwargs.get("delay_seconds", 0))
        if not group_chat_id or not raid_command:
            agent.logger.error("Missing parameters: 'group_chat_id' and 'raid_command' are required.")
            return None

        async def delayed_raid():
            agent.logger.info(f"Raid scheduled in {delay_seconds} seconds...")
            await asyncio.sleep(delay_seconds)
            telegram_connection = agent.connection_manager.connections.get("telegram")
            if not telegram_connection:
                agent.logger.error("Telegram connection not configured.")
                return None
            telegram_bot = telegram_connection.app.bot
            send_raid_command(telegram_bot, int(group_chat_id), raid_command)
            agent.logger.info("Scheduled raid executed.")
            return True

        return asyncio.create_task(delayed_raid())
    except Exception as e:
        agent.logger.error(f"Failed to schedule raid: {e}")
        return None
