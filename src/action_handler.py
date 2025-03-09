import logging
from src.actions.knowledge_actions import (
    get_knowledge, add_knowledge, remove_knowledge, 
    search_knowledge, get_knowledge_summary
)

logger = logging.getLogger("action_handler")

action_registry = {}    

def register_action(action_name):
    def decorator(func):
        action_registry[action_name] = func
        return func
    return decorator

def execute_action(agent, action_name, **kwargs):
    if action_name in action_registry:
       return action_registry[action_name](agent, **kwargs)
    else:
        logger.error(f"Action {action_name} not found")
        return None

# Register knowledge actions
register_action("get_knowledge")(get_knowledge)
register_action("add_knowledge")(add_knowledge)
register_action("remove_knowledge")(remove_knowledge)
register_action("search_knowledge")(search_knowledge)
register_action("get_knowledge_summary")(get_knowledge_summary)
