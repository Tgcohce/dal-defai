import os
import logging
import asyncio
import threading
import tempfile
import subprocess
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
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    else:
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
        # Optionally, load the bot's username from env; default to "@CurtisSonicLoverBot"
        if not os.getenv("TELEGRAM_BOT_USERNAME"):
            os.environ["TELEGRAM_BOT_USERNAME"] = "@CurtisSonicLoverBot"
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
        # Thread and event loop for the bot
        self._stop_event = threading.Event()
        self._bot_loop = None
        self._bot_thread = None

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
        # Register a /start command handler and a catch-all message handler.
        self.app.add_handler(CommandHandler("start", self._start))
        self.app.add_handler(MessageHandler(filters.ALL, self._handle_message))
        self.app.add_handler(CallbackQueryHandler(self._callback_handler))

    async def _start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_chat.id
        await context.bot.send_message(chat_id=chat_id, text="Welcome to the Telegram bot\!")
    
    async def extract_audio_from_video(self, video_path: str, output_path: str) -> bool:
        """
        Extract audio from a video file using ffmpeg.
        
        Args:
            video_path: Path to the input video file
            output_path: Path where to save the extracted audio
            
        Returns:
            True if extraction was successful, False otherwise
        """
        try:
            # First check if ffmpeg is installed and in the PATH
            logger.info(f"Extracting audio from {video_path} to {output_path}")
            
            # Check if ffmpeg-python is available
            try:
                import ffmpeg
                logger.info("Using ffmpeg-python for audio extraction")
                
                # Extract audio using ffmpeg-python
                (
                    ffmpeg
                    .input(video_path)
                    .output(output_path, acodec='pcm_s16le', ac=1, ar='16k')
                    .overwrite_output()
                    .run(quiet=True, capture_stdout=True, capture_stderr=True)
                )
                
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    logger.info(f"Successfully extracted audio to {output_path}")
                    return True
                else:
                    logger.error(f"Audio extraction completed but output file is empty or missing")
                    return False
                    
            except ImportError:
                # Fall back to command line ffmpeg
                logger.warning("ffmpeg-python not available, falling back to subprocess")
                
                # Use subprocess to call ffmpeg directly
                cmd = [
                    "ffmpeg", 
                    "-i", video_path, 
                    "-vn",  # Disable video
                    "-acodec", "pcm_s16le",  # Convert to PCM WAV
                    "-ac", "1",  # Mono
                    "-ar", "16000",  # 16kHz sample rate
                    "-y",  # Overwrite output file
                    output_path
                ]
                
                logger.info(f"Running command: {' '.join(cmd)}")
                
                process = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                if process.returncode != 0:
                    logger.error(f"ffmpeg failed with code {process.returncode}: {process.stderr}")
                    return False
                
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    logger.info(f"Successfully extracted audio to {output_path}")
                    return True
                else:
                    logger.error(f"Audio extraction completed but output file is empty or missing")
                    return False
                
        except Exception as e:
            logger.error(f"Error extracting audio from video: {e}")
            return False
    
    async def transcribe_voice(self, file_path: str) -> str:
        """
        Transcribe a voice message file using OpenAI Whisper.
        
        Args:
            file_path: Path to the downloaded voice file
            
        Returns:
            Transcribed text
        """
        try:
            import whisper
            
            logger.info(f"Transcribing audio file: {file_path}")
            
            # Load the Whisper model - using base model for efficiency
            model = whisper.load_model("base")
            
            # Transcribe the audio file
            result = model.transcribe(file_path)
            
            logger.info(f"Transcription result: {result['text']}")
            
            # Return the transcribed text
            return result["text"]
        except ImportError:
            error_msg = "Whisper not installed. Please install it using: pip install openai-whisper"
            logger.error(error_msg)
            return "I couldn't transcribe your message due to missing dependencies."
        except Exception as e:
            logger.error(f"Error transcribing voice message: {e}")
            return "I had trouble understanding your voice message."

    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = update.effective_chat.id
        
        # Skip if there is no message
        if not update.message:
            logger.warning("Received update without message")
            return
            
        # Get common sender info for any message type
        message_id = update.message.message_id
        user_id = update.message.from_user.id if update.message.from_user else None
        username = update.message.from_user.username if update.message.from_user else None
        sender_name = username or f"User{user_id}"
        
        logger.info(f"Processing message: ID={message_id}, chat={chat_id}, user={sender_name}")
        logger.info(f"Message has voice: {hasattr(update.message, 'voice') and update.message.voice is not None}")
        logger.info(f"Message has video: {hasattr(update.message, 'video') and update.message.video is not None}")
        
        try:
            # Handle voice messages
            if hasattr(update.message, 'voice') and update.message.voice:
                logger.info(f"Processing voice message from {sender_name}")
                try:
                    # First send typing indicator
                    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
                    
                    # Create a temporary file
                    with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_file:
                        voice_path = temp_file.name
                    
                    # Get voice file
                    media_file = await update.message.voice.get_file()
                    logger.info(f"Voice file info: {media_file}")
                    
                    # Download the file
                    await media_file.download_to_drive(voice_path)
                    logger.info(f"Downloaded voice file to {voice_path}")
                    
                    if not os.path.exists(voice_path) or os.path.getsize(voice_path) == 0:
                        raise Exception("Voice file download failed or file is empty")
                    
                    # Transcribe the audio directly
                    transcription = await self.transcribe_voice(voice_path)
                    logger.info(f"Voice transcription result: {transcription}")
                    
                    # Generate a response using LLM
                    try:
                        from src.agent import active_agent
                        if active_agent:
                            # Prepare prompt with transcription
                            prompt = f"{sender_name} says (voice message): {transcription}\n\nHow should Curtis respond to this message?"
                            response = active_agent.prompt_llm(prompt)
                            logger.info(f"Generated response to voice message using agent LLM: {response}")
                        else:
                            # Fallback
                            response = f"I understood your voice message as: '{transcription}'. How can I help you with Sonic Labs today?"
                    except (ImportError, AttributeError) as e:
                        logger.error(f"Could not import agent module: {e}")
                        response = f"I understood your voice message as: '{transcription}'. How can I help you with Sonic Labs today?"
                    
                    # Reply with the response
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=response,
                        reply_to_message_id=message_id
                    )
                    logger.info(f"SUCCESSFULLY responded to voice message in chat {chat_id}")
                    
                    # Clean up the temporary file
                    if os.path.exists(voice_path):
                        os.remove(voice_path)
                except Exception as e:
                    logger.error(f"ERROR: Failed to process voice message: {e}", exc_info=True)
                    try:
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=f"Sorry, I couldn't process your voice message. Please try again or send a text message.",
                            reply_to_message_id=message_id
                        )
                    except Exception as reply_err:
                        logger.error(f"Failed to send error message: {reply_err}")
                        
            # Handle video messages
            elif hasattr(update.message, 'video') and update.message.video:
                logger.info(f"Processing video message from {sender_name}")
                try:
                    # First send typing indicator
                    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
                    
                    # Create temporary files
                    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as video_temp:
                        video_path = video_temp.name
                    
                    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as audio_temp:
                        audio_path = audio_temp.name
                    
                    # Get video file
                    media_file = await update.message.video.get_file()
                    logger.info(f"Video file info: {media_file}")
                    
                    # Download the file
                    await media_file.download_to_drive(video_path)
                    logger.info(f"Downloaded video file to {video_path}, size: {os.path.getsize(video_path)}")
                    
                    if not os.path.exists(video_path) or os.path.getsize(video_path) == 0:
                        raise Exception("Video file download failed or file is empty")
                    
                    # Extract audio from video
                    success = await self.extract_audio_from_video(video_path, audio_path)
                    
                    if not success:
                        raise Exception("Failed to extract audio from video")
                    
                    logger.info(f"Extracted audio to {audio_path}, size: {os.path.getsize(audio_path)}")
                    
                    # Transcribe the extracted audio
                    transcription = await self.transcribe_voice(audio_path)
                    logger.info(f"Video audio transcription result: {transcription}")
                    
                    # Generate a response using LLM
                    try:
                        from src.agent import active_agent
                        if active_agent:
                            # Prepare prompt with transcription
                            prompt = f"{sender_name} says (video message): {transcription}\n\nHow should Curtis respond to this message?"
                            response = active_agent.prompt_llm(prompt)
                            logger.info(f"Generated response to video message using agent LLM: {response}")
                        else:
                            # Fallback
                            response = f"I understood your video message as: '{transcription}'. How can I help you with Sonic Labs today?"
                    except (ImportError, AttributeError) as e:
                        logger.error(f"Could not import agent module: {e}")
                        response = f"I understood your video message as: '{transcription}'. How can I help you with Sonic Labs today?"
                    
                    # Reply with the response
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=response,
                        reply_to_message_id=message_id
                    )
                    logger.info(f"SUCCESSFULLY responded to video message in chat {chat_id}")
                    
                    # Clean up the temporary files
                    if os.path.exists(video_path):
                        os.remove(video_path)
                    if os.path.exists(audio_path):
                        os.remove(audio_path)
                except Exception as e:
                    logger.error(f"ERROR: Failed to process video message: {e}", exc_info=True)
                    try:
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=f"Sorry, I couldn't process your video message. Please try again or send a text message.",
                            reply_to_message_id=message_id
                        )
                    except Exception as reply_err:
                        logger.error(f"Failed to send error message: {reply_err}")
            
            # Handle text messages
            elif hasattr(update.message, "text") and update.message.text:
                text = update.message.text
                
                logger.info(f"Received text message in chat {chat_id} from {sender_name}: {text}")
                
                # Filter to only respond to messages that mention the bot or are direct messages
                bot_username = os.getenv("TELEGRAM_BOT_USERNAME", "@CurtisSonicLoverBot").lower()
                is_direct_message = update.effective_chat.type == "private" 
                is_mentioned = bot_username.lower() in text.lower()
                
                # Check chat ID restriction - only respond in configured chat or direct messages
                chat_id_env = os.getenv("TELEGRAM_CHAT_ID")
                is_allowed_chat = chat_id_env and int(chat_id_env) == chat_id
                
                if is_direct_message or is_mentioned or is_allowed_chat:
                    # Generate a response using LLM
                    try:
                        # First send typing indicator
                        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
                        
                        # Try to import the agent module to get access to the LLM
                        try:
                            from src.agent import active_agent
                            if active_agent:
                                # Prepare prompt
                                prompt = f"{sender_name} says: {text}\n\nHow should Curtis respond to this message?"
                                response = active_agent.prompt_llm(prompt)
                                logger.info(f"Generated response using agent LLM: {response}")
                            else:
                                # Fallback to static response
                                response = f"Hey there\! I am Curtis, the Sonic Labs evangelist\! Thanks for your message about '{text}'. Let me know how I can help you with anything memecoin or Sonic Labs related\!"
                        except (ImportError, AttributeError) as e:
                            logger.error(f"Could not import agent module: {e}")
                            response = f"Hey there\! I am Curtis, the Sonic Labs evangelist\! Thanks for your message about '{text}'. Let me know how I can help you with anything memecoin or Sonic Labs related\!"
                        
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=response,
                            reply_to_message_id=message_id
                        )
                        logger.info(f"SUCCESSFULLY responded to message in chat {chat_id}")
                    except Exception as e:
                        logger.error(f"ERROR: Failed to respond to message: {e}", exc_info=True)
                        # Try to send a fallback message
                        try:
                            await context.bot.send_message(
                                chat_id=chat_id,
                                text="Sorry, I am having trouble responding right now. Please try again later\!",
                                reply_to_message_id=message_id
                            )
                        except:
                            pass
            else:
                # Log other message types
                logger.info(f"Received unsupported message in chat {chat_id}, type: {type(update.message)}")
                logger.info(f"Message attributes: {dir(update.message)}")
                
                try:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text="Hey there\! I received your message, but I can only process text, voice, and video messages right now. How can I help you with Sonic Labs today?"
                    )
                    logger.info(f"SUCCESSFULLY acknowledged non-text message in chat {chat_id}")
                except Exception as e:
                    logger.error(f"ERROR: Failed to acknowledge non-text message: {e}")
        except Exception as e:
            logger.error(f"Uncaught exception in _handle_message: {e}", exc_info=True)

    async def _callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()
        data = query.data
        await query.edit_message_text(text=f"Button clicked: {data}")

    async def _run_telegram_bot(self):
        """Run the Telegram bot polling asynchronously"""
        try:
            await self.app.initialize()
            await self.app.start()
            logger.info("Telegram bot initialized and started successfully")
            
            # Start polling
            await self.app.updater.start_polling(drop_pending_updates=True)
            logger.info("Telegram polling started successfully")
            
            # Keep running until stop event is set
            while not self._stop_event.is_set():
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error in Telegram bot polling: {e}", exc_info=True)
        finally:
            # Clean shutdown
            try:
                await self.app.stop()
                await self.app.shutdown()
                logger.info("Telegram bot stopped and shutdown cleanly")
            except Exception as e:
                logger.error(f"Error during Telegram bot shutdown: {e}")

    def _thread_worker(self):
        """Thread worker function that sets up the event loop and runs the bot"""
        try:
            # Create new event loop for this thread
            self._bot_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._bot_loop)
            
            # Run the async function
            self._bot_loop.run_until_complete(self._run_telegram_bot())
        except Exception as e:
            logger.error(f"Error in Telegram thread worker: {e}", exc_info=True)
        finally:
            # Close the loop
            try:
                self._bot_loop.close()
                logger.info("Telegram event loop closed")
            except Exception as e:
                logger.error(f"Error closing Telegram event loop: {e}")

    def run(self) -> None:
        """Run the Telegram bot polling in a separate thread with its own event loop"""
        logger.info("Starting Telegram bot polling...")
        
        # Reset the stop event
        self._stop_event.clear()
        
        try:
            # Create and start the thread
            self._bot_thread = threading.Thread(
                target=self._thread_worker,
                name="TelegramBot",
                daemon=True
            )
            self._bot_thread.start()
            logger.info(f"Telegram bot thread started with name '{self._bot_thread.name}'")
        except Exception as e:
            logger.error(f"Failed to start Telegram bot thread: {e}", exc_info=True)

    def stop(self) -> None:
        """Stop the Telegram bot polling"""
        if self._bot_thread and self._bot_thread.is_alive():
            logger.info("Stopping Telegram bot...")
            self._stop_event.set()
            self._bot_thread.join(timeout=5.0)
            logger.info("Telegram bot stopped")