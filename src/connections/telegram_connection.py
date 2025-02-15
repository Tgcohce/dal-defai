import os
import logging
import asyncio
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


# Helper function to run async tasks safely
def run_async_task(coro):
    try:
        # Try to get the current running loop
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop, so create a new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    else:
        # Use run_coroutine_threadsafe to run the coroutine in the running loop
        # This will block until the coroutine is complete and return the result
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future.result()


# A simple callable action that wraps a handler function.
class CallableAction(Action):
    def __init__(self, name, parameters, description, handler):
        super().__init__(name=name, parameters=parameters, description=description)
        self.handler = handler

    def __call__(self, **kwargs):
        return self.handler(**kwargs)


class TelegramConnection(BaseConnection):
    # This name is used to identify the connection in the CLI.
    name = "telegram"

    @property
    def is_llm_provider(self) -> bool:
        """This connection is not an LLM provider."""
        return False

    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and return the configuration."""
        return config

    def configure(self, **kwargs) -> bool:
        """
        Optionally update the connection configuration.
        Here we simply verify that the required environment variables exist.
        """
        if not os.getenv("TELEGRAM_BOT_TOKEN"):
            raise TelegramConfigurationError("Missing TELEGRAM_BOT_TOKEN in environment.")
        if not os.getenv("TELEGRAM_CHAT_ID"):
            raise TelegramConfigurationError("Missing TELEGRAM_CHAT_ID in environment.")
        logger.info("✅ SUCCESSFULLY CONFIGURED CONNECTION: telegram")
        return True

    def is_configured(self, verbose: bool = False) -> bool:
        """Check if the connection is properly configured."""
        return bool(self.bot_token)

    def register_actions(self) -> None:
        """
        Register available Telegram actions.
        We register our actions as CallableAction instances.
        """
        self.actions["send-message"] = CallableAction(
            name="send-message",
            parameters=[
                ActionParameter("message", True, str, "Message text to send"),
            ],
            description="Send a text message to a Telegram chat",
            handler=self._handle_send_message_action
        )
        self.actions["reply-to-message"] = CallableAction(
            name="reply-to-message",
            parameters=[
                ActionParameter("message_id", True, int, "ID of the message to reply to"),
                ActionParameter("reply_text", True, str, "Reply text")
            ],
            description="Reply to a specific message in the chat",
            handler=self._handle_reply_to_message_action
        )
        self.actions["pin-message"] = CallableAction(
            name="pin-message",
            parameters=[
                ActionParameter("message_id", True, int, "ID of the message to pin")
            ],
            description="Pin a message in the chat",
            handler=self._handle_pin_message_action
        )
        self.actions["unpin-message"] = CallableAction(
            name="unpin-message",
            parameters=[
                ActionParameter("message_id", True, int, "ID of the message to unpin")
            ],
            description="Unpin a message in the chat",
            handler=self._handle_unpin_message_action
        )
        self.actions["kick-user"] = CallableAction(
            name="kick-user",
            parameters=[
                ActionParameter("user_id", True, int, "ID of the user to kick")
            ],
            description="Kick a user from the chat",
            handler=self._handle_kick_user_action
        )

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Telegram connection.
        We set up the Telegram Application (self.app) before calling the BaseConnection __init__
        so that register_actions (invoked by the base class) can safely use self.app.
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
        Override perform_action to support CLI calls that might pass parameters either as
        positional arguments or as a dictionary.
        """
        kwargs.pop("connection", None)
        if args:
            action_name = args[0]
            if len(args) > 1 and isinstance(args[1], dict):
                kwargs.update(args[1])
        else:
            action_name = kwargs.pop("action", None)
        if not action_name:
            raise ValueError("Missing action parameter")
        return super().perform_action(action_name, **kwargs)

    def _handle_send_message_action(self, **kwargs):
        message = kwargs.get("message")
        if not message:
            raise ValueError("Missing 'message' parameter")
        chat_id_env = os.getenv("TELEGRAM_CHAT_ID")
        if not chat_id_env:
            raise TelegramConfigurationError("Missing TELEGRAM_CHAT_ID in environment.")
        chat_id = int(chat_id_env)
        return run_async_task(self.send_message(chat_id, message))

    async def send_message(self, chat_id: int, message: str) -> None:
        try:
            await self.app.bot.send_message(chat_id=chat_id, text=message)
            logger.info(f"Message sent to chat {chat_id}")
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise TelegramAPIError(f"Failed to send message: {e}")

    def _handle_reply_to_message_action(self, **kwargs):
        message_id = kwargs.get("message_id")
        reply_text = kwargs.get("reply_text")
        if message_id is None or not reply_text:
            raise ValueError("Missing required parameters for reply-to-message action")
        chat_id_env = os.getenv("TELEGRAM_CHAT_ID")
        if not chat_id_env:
            raise TelegramConfigurationError("Missing TELEGRAM_CHAT_ID in environment.")
        chat_id = int(chat_id_env)
        return run_async_task(self.reply_to_message(chat_id, message_id, reply_text))

    async def reply_to_message(self, chat_id: int, message_id: int, reply_text: str) -> None:
        try:
            await self.app.bot.send_message(
                chat_id=chat_id,
                text=reply_text,
                reply_to_message_id=message_id
            )
            logger.info(f"Replied to message {message_id} in chat {chat_id}")
        except Exception as e:
            logger.error(f"Failed to reply to message: {e}")
            raise TelegramAPIError(f"Failed to reply to message: {e}")

    def _handle_pin_message_action(self, **kwargs):
        message_id = kwargs.get("message_id")
        if message_id is None:
            raise ValueError("Missing 'message_id' parameter for pin-message action")
        chat_id_env = os.getenv("TELEGRAM_CHAT_ID")
        if not chat_id_env:
            raise TelegramConfigurationError("Missing TELEGRAM_CHAT_ID in environment.")
        chat_id = int(chat_id_env)
        return run_async_task(self.pin_message(chat_id, message_id))

    async def pin_message(self, chat_id: int, message_id: int) -> None:
        try:
            await self.app.bot.pin_chat_message(chat_id=chat_id, message_id=message_id)
            logger.info(f"Pinned message {message_id} in chat {chat_id}")
        except Exception as e:
            logger.error(f"Failed to pin message: {e}")
            raise TelegramAPIError(f"Failed to pin message: {e}")

    def _handle_unpin_message_action(self, **kwargs):
        message_id = kwargs.get("message_id")
        if message_id is None:
            raise ValueError("Missing 'message_id' parameter for unpin-message action")
        chat_id_env = os.getenv("TELEGRAM_CHAT_ID")
        if not chat_id_env:
            raise TelegramConfigurationError("Missing TELEGRAM_CHAT_ID in environment.")
        chat_id = int(chat_id_env)
        return run_async_task(self.unpin_message(chat_id, message_id))

    async def unpin_message(self, chat_id: int, message_id: int) -> None:
        try:
            await self.app.bot.unpin_chat_message(chat_id=chat_id, message_id=message_id)
            logger.info(f"Unpinned message {message_id} in chat {chat_id}")
        except Exception as e:
            logger.error(f"Failed to unpin message: {e}")
            raise TelegramAPIError(f"Failed to unpin message: {e}")

    def _handle_kick_user_action(self, **kwargs):
        user_id = kwargs.get("user_id")
        if user_id is None:
            raise ValueError("Missing 'user_id' parameter for kick-user action")
        chat_id_env = os.getenv("TELEGRAM_CHAT_ID")
        if not chat_id_env:
            raise TelegramConfigurationError("Missing TELEGRAM_CHAT_ID in environment.")
        chat_id = int(chat_id_env)
        return run_async_task(self.kick_user(chat_id, user_id))

    async def kick_user(self, chat_id: int, user_id: int) -> None:
        try:
            await self.app.bot.kick_chat_member(chat_id=chat_id, user_id=user_id)
            logger.info(f"Kicked user {user_id} from chat {chat_id}")
        except Exception as e:
            logger.error(f"Failed to kick user: {e}")
            raise TelegramAPIError(f"Failed to kick user: {e}")

    def _register_handlers(self) -> None:
        self.app.add_handler(CommandHandler("start", self._start))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._echo))
        self.app.add_handler(CallbackQueryHandler(self._callback_handler))

    async def _start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_chat.id
        await context.bot.send_message(chat_id=chat_id, text="Welcome to the Telegram bot!")

    async def _echo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_chat.id
        text = update.message.text
        await context.bot.send_message(chat_id=chat_id, text=f"You said: {text}")

    async def _callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()
        data = query.data
        await query.edit_message_text(text=f"Button clicked: {data}")

    def run(self) -> None:
        logger.info("Starting Telegram bot polling...")
        self.app.run_polling()
