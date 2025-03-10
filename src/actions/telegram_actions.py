import os
import asyncio
import threading
import logging
import tempfile
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
        # Base message data
        message_data = {
            "message_id": update.message.message_id,
            "from": update.effective_user.username if update.effective_user else None,
            "date": update.message.date.isoformat() if update.message.date else None,
        }
        
        # Add text, voice or video info
        if update.message.text:
            message_data["type"] = "text"
            message_data["text"] = update.message.text
        elif update.message.voice:
            message_data["type"] = "voice"
            message_data["voice_duration"] = update.message.voice.duration
            message_data["voice_file_id"] = update.message.voice.file_id
            message_data["text"] = "[Voice Message]"
        elif update.message.video:
            message_data["type"] = "video"
            message_data["video_duration"] = update.message.video.duration
            message_data["video_file_id"] = update.message.video.file_id
            message_data["text"] = "[Video Message]"
        else:
            message_data["type"] = "other"
            message_data["text"] = "[Unsupported Message Type]"
            
        received_messages.append(message_data)
        logger.info(f"Stored received message: {message_data}")


def download_media_with_retries(file, file_path, max_retries=3):
    """
    Helper function to download media with retries
    """
    async def _download_with_retries():
        retries = 0
        while retries < max_retries:
            try:
                await file.download_to_drive(file_path)
                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    logger.info(f"Successfully downloaded file to {file_path}")
                    return True
                else:
                    logger.error(f"File downloaded but is empty or missing: {file_path}")
                    retries += 1
            except Exception as e:
                logger.error(f"Download attempt {retries+1} failed: {e}")
                retries += 1
                await asyncio.sleep(1)  # Wait a bit before retrying
        
        return False
    
    loop = get_background_loop()
    return asyncio.run_coroutine_threadsafe(_download_with_retries(), loop).result()


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
    telegram_conn.actions["transcribe-voice"] = _handle_transcribe_voice_action(telegram_conn)
    telegram_conn.actions["transcribe-video"] = _handle_transcribe_video_action(telegram_conn)

    # Add message handlers to store received messages (text, voice and video)
    telegram_conn.app.add_handler(
        MessageHandler(
            (filters.TEXT | filters.VOICE | filters.VIDEO | filters.Document.ALL) & ~filters.COMMAND, 
            store_received_message
        )
    )


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


def _handle_transcribe_voice_action(conn: TelegramConnection):
    def action(**kwargs):
        voice_file_id = kwargs.get("voice_file_id")
        if not voice_file_id:
            raise ValueError("Missing required parameter: voice_file_id")
            
        chat_id_env = os.getenv("TELEGRAM_CHAT_ID")
        if not chat_id_env:
            raise TelegramConfigurationError("Missing TELEGRAM_CHAT_ID in environment.")
            
        # We need to download the voice file and transcribe it
        async def transcribe_voice():
            try:
                # Create a temporary file
                with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_file:
                    voice_path = temp_file.name
                
                # Get the voice file from Telegram
                file = await conn.app.bot.get_file(voice_file_id)
                logger.info(f"Got voice file info: {file}")
                
                # Download the file
                await file.download_to_drive(voice_path)
                logger.info(f"Downloaded voice file to {voice_path}")
                
                if not os.path.exists(voice_path) or os.path.getsize(voice_path) == 0:
                    raise Exception("Voice file download failed or file is empty")
                
                # Transcribe using the connection's method
                transcription = await conn.transcribe_voice(voice_path)
                logger.info(f"Transcription result: {transcription}")
                
                # Clean up
                if os.path.exists(voice_path):
                    os.remove(voice_path)
                    
                return transcription
            except Exception as e:
                logger.error(f"Error transcribing voice message: {e}", exc_info=True)
                if 'voice_path' in locals() and os.path.exists(voice_path):
                    os.remove(voice_path)
                raise
                
        loop = get_background_loop()
        future = asyncio.run_coroutine_threadsafe(transcribe_voice(), loop)
        return future.result()

    return action


def _handle_transcribe_video_action(conn: TelegramConnection):
    def action(**kwargs):
        video_file_id = kwargs.get("video_file_id")
        if not video_file_id:
            raise ValueError("Missing required parameter: video_file_id")
            
        chat_id_env = os.getenv("TELEGRAM_CHAT_ID")
        if not chat_id_env:
            raise TelegramConfigurationError("Missing TELEGRAM_CHAT_ID in environment.")
            
        # We need to download the video file, extract audio, and transcribe it
        async def transcribe_video():
            try:
                # Create temporary files
                with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as video_temp:
                    video_path = video_temp.name
                
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as audio_temp:
                    audio_path = audio_temp.name
                
                # Get the video file from Telegram
                file = await conn.app.bot.get_file(video_file_id)
                logger.info(f"Got video file info: {file}")
                
                # Download the file
                await file.download_to_drive(video_path)
                logger.info(f"Downloaded video file to {video_path}")
                
                if not os.path.exists(video_path) or os.path.getsize(video_path) == 0:
                    raise Exception("Video file download failed or file is empty")
                
                # Extract audio from video
                success = await conn.extract_audio_from_video(video_path, audio_path)
                
                if not success:
                    raise Exception("Failed to extract audio from video")
                
                # Transcribe using the connection's method
                transcription = await conn.transcribe_voice(audio_path)
                logger.info(f"Video transcription result: {transcription}")
                
                # Clean up
                if os.path.exists(video_path):
                    os.remove(video_path)
                if os.path.exists(audio_path):
                    os.remove(audio_path)
                    
                return transcription
            except Exception as e:
                logger.error(f"Error transcribing video message: {e}", exc_info=True)
                # Clean up on error
                if 'video_path' in locals() and os.path.exists(video_path):
                    os.remove(video_path)
                if 'audio_path' in locals() and os.path.exists(audio_path):
                    os.remove(audio_path)
                raise
                
        loop = get_background_loop()
        future = asyncio.run_coroutine_threadsafe(transcribe_video(), loop)
        return future.result()

    return action