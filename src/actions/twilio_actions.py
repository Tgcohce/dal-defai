from src.action_handler import register_action
import logging

logger = logging.getLogger("actions.twilio_actions")

@register_action("send-sms")
def send_sms(agent, **kwargs):
    """
    Action to send an SMS via the Twilio connection.
    Expects parameters: 'to' (phone number) and 'message' (text).
    """
    try:
        result = agent.connection_manager.perform_action("twilio", "send-sms", [kwargs.get("to"), kwargs.get("message")])
        logger.info(f"SMS action result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in send-sms action: {e}")
        return None

@register_action("make-call")
def make_call(agent, **kwargs):
    """
    Action to make a voice call via the Twilio connection.
    Expects parameters: 'to' (phone number) and 'message' (text to speak).
    """
    try:
        result = agent.connection_manager.perform_action("twilio", "make-call", [kwargs.get("to"), kwargs.get("message")])
        logger.info(f"Call action result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in make-call action: {e}")
        return None
