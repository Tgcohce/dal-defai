import argparse
import time
import logging
import os
from dotenv import load_dotenv
from src.cli import ZerePyCLI
from src.connections.telegram_connection import TelegramConnection

logger = logging.getLogger("main")

def run_telegram_bot_only():
    """Run only the Telegram bot for testing purposes"""
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,  # Use DEBUG for more detailed logs
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    logger.info("Starting Telegram bot in standalone test mode...")
    load_dotenv()
    
    if not os.getenv("TELEGRAM_BOT_TOKEN"):
        logger.error("No TELEGRAM_BOT_TOKEN found in environment! Please set this value.")
        exit(1)
    
    if not os.getenv("TELEGRAM_CHAT_ID"):
        logger.error("No TELEGRAM_CHAT_ID found in environment! Please set this value.")
        exit(1)
    
    # Set bot username if not set
    if not os.getenv("TELEGRAM_BOT_USERNAME"):
        bot_username = "@CurtisSonicLoverBot"
        os.environ["TELEGRAM_BOT_USERNAME"] = bot_username
        logger.info(f"TELEGRAM_BOT_USERNAME not set, using default: {bot_username}")
    
    # Print environment variables for debugging
    logger.info(f"Using Telegram bot token: {os.getenv('TELEGRAM_BOT_TOKEN')[:5]}...")
    logger.info(f"Using Telegram chat ID: {os.getenv('TELEGRAM_CHAT_ID')}")
    logger.info(f"Using Telegram bot username: {os.getenv('TELEGRAM_BOT_USERNAME')}")
        
    # Create just the Telegram connection
    try:
        logger.info("Creating Telegram connection...")
        telegram_conn = TelegramConnection({})
        logger.info("Telegram connection created successfully!")
        logger.info("Bot will respond to ALL messages for testing")
        logger.info("Press Ctrl+C to stop")
        
        # Run in main thread since this is a standalone mode
        telegram_conn.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.error(f"Error running Telegram bot: {e}", exc_info=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='ZerePy - AI Agent Framework')
    parser.add_argument('--server', action='store_true', help='Run in server mode')
    parser.add_argument('--host', default='0.0.0.0', help='Server host (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8000, help='Server port (default: 8000)')
    parser.add_argument('--telegram-only', action='store_true', help='Run only the Telegram bot for testing')
    args = parser.parse_args()

    if args.telegram_only:
        # Run only the Telegram bot for debugging
        run_telegram_bot_only()
    elif args.server:
        try:
            from src.server import start_server
            start_server(host=args.host, port=args.port)
        except ImportError:
            print("Server dependencies not installed. Run: poetry install --extras server")
            exit(1)
    else:
        cli = ZerePyCLI()
        cli.main_loop()