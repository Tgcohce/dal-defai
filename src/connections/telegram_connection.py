import os
import logging
from typing import Dict, Any
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from src.connections.base_connection import BaseConnection, Action, ActionParameter

# Configure logging
logger = logging.getLogger("connections.telegram_connection")
logging.basicConfig(level=logging.INFO)


# Custom exceptions
class TelegramConnectionError(Exception):
    """Base exception for Telegram connection errors"""
    pass


class TelegramConfigurationError(TelegramConnectionError):
    """Raised when there are configuration/credential issues"""
    pass


class TelegramAPIError(TelegramConnectionError):
    """Raised when Telegram API requests fail"""
    pass


# Define a callable Action that wraps a handler function.
class CallableAction(Action):
    def __init__(self, name, parameters, description, handler):
        super().__init__(name=name, parameters=parameters, description=description)
        self.handler = handler

    def __call__(self, **kwargs):
        return self.handler(**kwargs)


class TelegramConnection(BaseConnection):
    # This name is used to identify the connection (e.g., by the connection manager/CLI).
    name = "telegram"

    @property
    def is_llm_provider(self) -> bool:
        """This connection is not an LLM provider."""
        return False

    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and return the configuration.
        Extend this to check for additional keys if needed.
        """
        return config

    def configure(self, **kwargs) -> bool:
        """
        Optionally update the connection configuration.
        Here we verify that the required environment variables exist.
        """
        if not os.getenv("TELEGRAM_BOT_TOKEN"):
            raise TelegramConfigurationError("Missing TELEGRAM_BOT_TOKEN in environment.")
        if not os.getenv("TELEGRAM_CHAT_ID"):
            raise TelegramConfigurationError("Missing TELEGRAM_CHAT_ID in environment.")
        logger.info("✅ SUCCESSFULLY CONFIGURED CONNECTION: telegram")
        return True

    def is_configured(self, verbose: bool = False) -> bool:
        """
        Check if the connection is properly configured.
        """
        return bool(self.bot_token)

    def register_actions(self) -> None:
        """
        Register available Telegram actions.
        We register the "send-message" action as a CallableAction instance.
        Since the chat ID is read from the environment, only the "message" parameter is required.
        """
        self.actions["send-message"] = CallableAction(
            name="send-message",
            parameters=[
                ActionParameter("message", True, str, "Message text to send"),
            ],
            description="Send a text message to a Telegram chat",
            handler=self._handle_send_message_action
        )

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Telegram connection.
        The Telegram Application (self.app) is set up before calling the BaseConnection
        __init__ so that register_actions (invoked by the base class) can safely use self.app.
        """
        load_dotenv()
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.bot_token:
            raise TelegramConfigurationError("Missing TELEGRAM_BOT_TOKEN in environment.")
        # Create the Telegram bot Application.
        self.app = Application.builder().token(self.bot_token).build()
        # Now call the BaseConnection __init__.
        super().__init__(config)
        # Register command and message handlers.
        self._register_handlers()

    def perform_action(self, *args, **kwargs):
        """
        Override perform_action to support CLI calls that pass extra positional arguments.

        The CLI calls it like:
            perform_action(connection, action, params=...)
        Since the connection is already this instance, we ignore the extra connection argument.
        """
        if len(args) >= 2:
            # Assume args[0] is the connection name and args[1] is the action name.
            action_name = args[1]
        elif len(args) == 1:
            action_name = args[0]
        else:
            raise ValueError("No action specified")
        return super().perform_action(action_name, **kwargs)

    def _handle_send_message_action(self, **kwargs):
        """
        Handler for the "send-message" action.
        It validates parameters, reads the chat ID from the environment, and schedules the asynchronous send.
        """
        message = kwargs.get("message")
        chat_id_env = os.getenv("TELEGRAM_CHAT_ID")
        if not chat_id_env:
            raise TelegramConfigurationError("Missing TELEGRAM_CHAT_ID in environment.")
        chat_id = int(chat_id_env)
        # run_async schedules the coroutine for execution.
        return self.app.run_async(self.send_message(chat_id, message))

    async def send_message(self, chat_id: int, message: str) -> None:
        """
        Asynchronously send a text message to a Telegram chat.
        """
        try:
            await self.app.bot.send_message(chat_id=chat_id, text=message)
            logger.info(f"Message sent to chat {chat_id}")
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise TelegramAPIError(f"Failed to send message: {e}")

    def _register_handlers(self) -> None:
        """
        Register Telegram update handlers (commands, messages, callbacks).
        Here we use polling mode; for production you might prefer webhooks.
        """
        self.app.add_handler(CommandHandler("start", self._start))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._echo))
        self.app.add_handler(CallbackQueryHandler(self._callback_handler))

    async def _start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle the /start command.
        """
        chat_id = update.effective_chat.id
        await context.bot.send_message(chat_id=chat_id, text="Welcome to the Telegram bot!")

    async def _echo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Echo the received text message.
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
        await query.edit_message_text(text=f"Button clicked: {data}")

    def run(self) -> None:
        """
        Start the Telegram bot in polling mode.
        """
        logger.info("Starting Telegram bot polling...")
        self.app.run_polling()
