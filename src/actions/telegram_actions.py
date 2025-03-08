import os
import asyncio
import threading
import logging
from telegram import Update
from telegram.ext import MessageHandler, filters, ContextTypes
from src.connections.telegram_connection import TelegramConnection, TelegramConfigurationError

logger = logging.getLogger("connections.telegram_connection")

# Global variables to hold the persistent background event loop and its thread
_loop = None
_loop_thread = None


def start_background_loop(loop: asyncio.AbstractEventLoop):
    """Run the provided event loop forever in a background thread."""
    asyncio.set_event_loop(loop)
    loop.run_forever()


def get_background_loop() -> asyncio.AbstractEventLoop:
    """
    Returns a persistent background event loop.
    If no loop exists or the existing one is closed, creates a new one.
    """
    global _loop, _loop_thread
    if _loop is None or _loop.is_closed():
        _loop = asyncio.new_event_loop()
        _loop_thread = threading.Thread(target=start_background_loop, args=(_loop,), daemon=True)
        _loop_thread.start()
        # Wait briefly until the loop is running
        while not _loop.is_running():
            pass
    return _loop


# Global list to store received messages from the chat.
received_messages = []


def store_received_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stores received messages in a global list."""
    global received_messages
    if update.message:
        message_data = {
            "message_id": update.message.message_id,
            "text": update.message.text,
            "from": update.effective_user.username if update.effective_user else None,
            "date": update.message.date.isoformat() if update.message.date else None,
        }
        received_messages.append(message_data)
        logger.info(f"Stored received message: {message_data}")


def register_telegram_actions(telegram_conn: TelegramConnection):
    """
    Registers Telegram actions with the provided connection.
    Call this function from your TelegramConnection.register_actions() method.
    """
    telegram_conn.actions["send-message"] = _handle_send_message_action(telegram_conn)
    telegram_conn.actions["reply"] = _handle_reply_action(telegram_conn)
    telegram_conn.actions["pin-message"] = _handle_pin_message_action(telegram_conn)
    telegram_conn.actions["kick"] = _handle_kick_action(telegram_conn)
    telegram_conn.actions["read-messages"] = _handle_read_messages_action(telegram_conn)
    telegram_conn.actions["clear-messages"] = _handle_clear_messages_action(telegram_conn)

    # Add an extra message handler to store received messages
    telegram_conn.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, store_received_message))


def _handle_send_message_action(conn: TelegramConnection):
    def action(**kwargs):
        message = kwargs.get("message")
        if not message:
            raise ValueError("Missing required parameter: message")
        chat_id_env = os.getenv("TELEGRAM_CHAT_ID")
        if not chat_id_env:
            raise TelegramConfigurationError("Missing TELEGRAM_CHAT_ID in environment.")
        chat_id = int(chat_id_env)
        loop = get_background_loop()
        future = asyncio.run_coroutine_threadsafe(conn.send_message(chat_id, message), loop)
        return future.result()

    return action


def _handle_reply_action(conn: TelegramConnection):
    def action(**kwargs):
        message = kwargs.get("message")
        message_id = kwargs.get("message_id")
        if not message or not message_id:
            raise ValueError("Missing required parameters: message and message_id")
        chat_id_env = os.getenv("TELEGRAM_CHAT_ID")
        if not chat_id_env:
            raise TelegramConfigurationError("Missing TELEGRAM_CHAT_ID in environment.")
        chat_id = int(chat_id_env)

        async def reply():
            await conn.app.bot.send_message(
                chat_id=chat_id,
                text=message,
                reply_to_message_id=message_id
            )
            logger.info(f"Replied to message {message_id} in chat {chat_id}")

        loop = get_background_loop()
        future = asyncio.run_coroutine_threadsafe(reply(), loop)
        return future.result()

    return action


def _handle_pin_message_action(conn: TelegramConnection):
    def action(**kwargs):
        message_id = kwargs.get("message_id")
        if not message_id:
            raise ValueError("Missing required parameter: message_id")
        chat_id_env = os.getenv("TELEGRAM_CHAT_ID")
        if not chat_id_env:
            raise TelegramConfigurationError("Missing TELEGRAM_CHAT_ID in environment.")
        chat_id = int(chat_id_env)

        async def pin():
            await conn.app.bot.pin_chat_message(chat_id=chat_id, message_id=message_id)
            logger.info(f"Pinned message {message_id} in chat {chat_id}")

        loop = get_background_loop()
        future = asyncio.run_coroutine_threadsafe(pin(), loop)
        return future.result()

    return action


def _handle_kick_action(conn: TelegramConnection):
    def action(**kwargs):
        user_id = kwargs.get("user_id")
        if not user_id:
            raise ValueError("Missing required parameter: user_id")
        chat_id_env = os.getenv("TELEGRAM_CHAT_ID")
        if not chat_id_env:
            raise TelegramConfigurationError("Missing TELEGRAM_CHAT_ID in environment.")
        chat_id = int(chat_id_env)

        async def kick():
            await conn.app.bot.kick_chat_member(chat_id=chat_id, user_id=user_id)
            logger.info(f"Kicked user {user_id} from chat {chat_id}")

        loop = get_background_loop()
        future = asyncio.run_coroutine_threadsafe(kick(), loop)
        return future.result()

    return action


def _handle_read_messages_action(conn: TelegramConnection):
    def action(**kwargs):
        global received_messages
        # Return a copy of the stored messages
        return received_messages.copy()

    return action


def _handle_clear_messages_action(conn: TelegramConnection):
    def action(**kwargs):
        global received_messages
        received_messages.clear()
        logger.info("Cleared received messages")
        return "Cleared received messages"

    return action
