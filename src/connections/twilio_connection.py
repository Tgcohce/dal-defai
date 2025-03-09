import os
import logging
from typing import Dict, Any
from twilio.rest import Client
from src.connections.base_connection import BaseConnection, Action, ActionParameter

logger = logging.getLogger("connections.twilio_connection")
logging.basicConfig(level=logging.INFO)

# Custom exceptions
class TwilioConnectionError(Exception):
    pass

class TwilioConfigurationError(TwilioConnectionError):
    pass

class TwilioAPIError(TwilioConnectionError):
    pass

class TwilioConnection(BaseConnection):
    # This name is used to identify the connection in the CLI.
    name = "twilio"

    @property
    def is_llm_provider(self) -> bool:
        return False

    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return config

    def configure(self, **kwargs) -> bool:
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        if not account_sid or not auth_token:
            raise TwilioConfigurationError("Missing TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN in environment.")
        logger.info("✅ SUCCESSFULLY CONFIGURED CONNECTION: twilio")
        return True

    def is_configured(self, verbose: bool = False) -> bool:
        return bool(os.getenv("TWILIO_ACCOUNT_SID") and os.getenv("TWILIO_AUTH_TOKEN"))

    def register_actions(self) -> None:
        self.actions["send-sms"] = Action(
            name="send-sms",
            parameters=[
                ActionParameter("to", True, str, "Recipient phone number"),
                ActionParameter("message", True, str, "SMS text message")
            ],
            description="Send an SMS message via Twilio"
        )
        self.actions["make-call"] = Action(
            name="make-call",
            parameters=[
                ActionParameter("to", True, str, "Recipient phone number"),
                ActionParameter("message", True, str, "Message to speak during the call")
            ],
            description="Make a voice call via Twilio and speak a message"
        )

    def __init__(self, config: Dict[str, Any]):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        if not self.account_sid or not self.auth_token:
            raise TwilioConfigurationError("Missing TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN in environment.")
        self.client = Client(self.account_sid, self.auth_token)
        super().__init__(config)
        self.register_actions()

    def perform_action(self, action_name: str, kwargs: Dict[str, Any]):
        if action_name not in self.actions:
            raise KeyError(f"Unknown action: {action_name}")
        errors = self.actions[action_name].validate_params(kwargs)
        if errors:
            raise ValueError(f"Invalid parameters: {', '.join(errors)}")

        if action_name == "send-sms":
            to = kwargs.get("to")
            message = kwargs.get("message")
            return self.send_sms(to, message)
        elif action_name == "make-call":
            to = kwargs.get("to")
            message = kwargs.get("message")
            return self.make_call(to, message)
        else:
            raise NotImplementedError(f"Action '{action_name}' not implemented.")

    def send_sms(self, to: str, message: str):
        try:
            from_number = os.getenv("TWILIO_PHONE_NUMBER")
            if not from_number:
                raise TwilioConfigurationError("Missing TWILIO_PHONE_NUMBER in environment.")
            msg = self.client.messages.create(
                body=message,
                from_=from_number,
                to=to
            )
            logger.info(f"SMS sent to {to}, SID: {msg.sid}")
            return msg.sid
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            raise TwilioAPIError(f"Failed to send SMS: {e}")

    def make_call(self, to: str, message: str):
        try:
            from_number = os.getenv("TWILIO_PHONE_NUMBER")
            if not from_number:
                raise TwilioConfigurationError("Missing TWILIO_PHONE_NUMBER in environment.")
            # Build a simple TwiML that speaks the message.
            from twilio.twiml.voice_response import VoiceResponse, Say
            response = VoiceResponse()
            response.say(message, voice="Polly.Emma")
            # Twimlets echo service can be used to host the TwiML for simplicity.
            twiml_url = "http://twimlets.com/echo?Twiml=" + response.to_xml()
            call = self.client.calls.create(
                to=to,
                from_=from_number,
                url=twiml_url
            )
            logger.info(f"Call initiated to {to}, SID: {call.sid}")
            return call.sid
        except Exception as e:
            logger.error(f"Failed to make call: {e}")
            raise TwilioAPIError(f"Failed to make call: {e}")
