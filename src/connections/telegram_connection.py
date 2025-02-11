import os
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv, set_key
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from src.connections.base_connection import BaseConnection, Action, ActionParameter

logger = logging.getLogger("connections.telegram_connection")


class TelegramConnectionError(Exception):
    """Base exception for Telegram connection errors"""
    pass


class TelegramConfigurationError(TelegramConnectionError):
    """Raised when there are configuration/credential issues"""
    pass


class TelegramAPIError(TelegramConnectionError):
    """Raised when Telegram API requests fail"""
    pass


class TelegramConnection(BaseConnection):
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Telegram connection using the python-telegram-bot Application.
        Expects that the following environment variables are set:
          - TELEGRAM_BOT_TOKEN: The bot token provided by BotFather.
        """
        super().__init__(config)
        load_dotenv()
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.bot_token:
            raise TelegramConfigurationError("Missing TELEGRAM_BOT_TOKEN in environment.")

        self.app = Application.builder().token(self.bot_token).build()
        self.register_actions()
        self._register_handlers()

    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the configuration.
        For Telegram, you may need to supply additional settings such as webhook URL,
        polling interval, etc. For now, we require no additional keys.
        """
        # You can expand this as needed.
        return config

    def register_actions(self) -> None:
        """
        Register available Telegram actions.
        Here we define a few basic actions; you can extend these as needed.
        """
        self.actions = {
            "send-message": Action(
                name="send-message",
                parameters=[
                    ActionParameter("chat_id", True, int, "ID of the target chat"),
                    ActionParameter("message", True, str, "Message text to send")
                ],
                description="Send a text message to a Telegram chat"
            ),
            # You can register additional actions as needed.
        }

    async def send_message(self, chat_id: int, message: str) -> None:
        """
        Send a text message to a Telegram chat.
        """
        try:
            await self.app.bot.send_message(chat_id=chat_id, text=message)
            logger.info(f"Message sent to chat {chat_id}")
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise TelegramAPIError(f"Failed to send message: {e}")

    def _register_handlers(self) -> None:
        """
        Register command and message handlers for incoming updates.
        For production, you might use webhooks. Here we demonstrate using polling.
        """
        # Basic start command handler
        self.app.add_handler(CommandHandler("start", self._start))
        # Example echo handler for any text message
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._echo))
        # Handler for inline button callbacks, if needed
        self.app.add_handler(CallbackQueryHandler(self._callback_handler))

    async def _start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle the /start command.
        """
        chat_id = update.effective_chat.id
        await context.bot.send_message(chat_id=chat_id, text="Welcome to the Telegram bot!")

    async def _echo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Echo the received message.
        """
        chat_id = update.effective_chat.id
        text = update.message.text
        await context.bot.send_message(chat_id=chat_id, text=f"You said: {text}")

    async def _callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle button callback queries.
        """
        query = update.callback_query
        await query.answer()
        data = query.data
        # Example: simple navigation based on callback data
        await query.edit_message_text(text=f"Button clicked: {data}")

    def run(self) -> None:
        """
        Run the bot in polling mode.
        For production, you might set up a webhook instead.
        """
        logger.info("Starting Telegram bot polling...")
        self.app.run_polling()

    def perform_action(self, action_name: str, kwargs: Dict[str, Any]) -> Any:
        """
        Execute a Telegram action based on the registered actions.
        For example, 'send-message' calls self.send_message().
        """
        if action_name not in self.actions:
            raise KeyError(f"Unknown action: {action_name}")
        action = self.actions[action_name]
        errors = action.validate_params(kwargs)
        if errors:
            raise ValueError(f"Invalid parameters: {', '.join(errors)}")

        if action_name == "send-message":
            chat_id = kwargs.get("chat_id")
            message = kwargs.get("message")
            # Since send_message is async, we need to run it in the event loop.
            return self.app.run_async(self.send_message(chat_id, message))
        else:
            raise NotImplementedError(f"Action '{action_name}' not implemented.")
