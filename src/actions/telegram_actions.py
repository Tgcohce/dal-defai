from src.action_handler import register_action

@register_action("send-telegram-message")
def send_telegram_message(agent, **kwargs):
    """
    Telegram action to send a message.
    Delegates to the telegram connection's "send-message" action.
    """
    message = kwargs.get("message")
    if not message:
        agent.logger.error("Missing 'message' parameter for send-telegram-message action")
        return
    result = agent.connection_manager.perform_action(
        connection_name="telegram",
        action_name="send-message",
        params=[message]
    )
    return result

@register_action("reply-to-message")
def reply_to_message(agent, **kwargs):
    """
    Telegram action to reply to a message.
    Expects:
      - message_id: ID of the message to reply to (int)
      - reply_text: The reply text (str)
    """
    message_id = kwargs.get("message_id")
    reply_text = kwargs.get("reply_text")
    if message_id is None or not reply_text:
        agent.logger.error("Missing 'message_id' or 'reply_text' for reply-to-message action")
        return
    result = agent.connection_manager.perform_action(
        connection_name="telegram",
        action_name="reply-to-message",
        params=[int(message_id), reply_text]
    )
    return result

@register_action("pin-message")
def pin_message(agent, **kwargs):
    """
    Telegram action to pin a message.
    Expects:
      - message_id: ID of the message to pin (int)
    """
    message_id = kwargs.get("message_id")
    if message_id is None:
        agent.logger.error("Missing 'message_id' parameter for pin-message")
        return
    result = agent.connection_manager.perform_action(
        connection_name="telegram",
        action_name="pin-message",
        params=[int(message_id)]
    )
    return result

@register_action("unpin-message")
def unpin_message(agent, **kwargs):
    """
    Telegram action to unpin a message.
    Expects:
      - message_id: ID of the message to unpin (int)
    """
    message_id = kwargs.get("message_id")
    if message_id is None:
        agent.logger.error("Missing 'message_id' parameter for unpin-message")
        return
    result = agent.connection_manager.perform_action(
        connection_name="telegram",
        action_name="unpin-message",
        params=[int(message_id)]
    )
    return result

@register_action("kick-user")
def kick_user(agent, **kwargs):
    """
    Telegram action to kick a user from the chat.
    Expects:
      - user_id: ID of the user to kick (int)
    """
    user_id = kwargs.get("user_id")
    if user_id is None:
        agent.logger.error("Missing 'user_id' parameter for kick-user")
        return
    result = agent.connection_manager.perform_action(
        connection_name="telegram",
        action_name="kick-user",
        params=[int(user_id)]
    )
    return result
