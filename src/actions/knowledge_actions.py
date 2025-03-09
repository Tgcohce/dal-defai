"""Actions for interacting with the knowledge base."""
from typing import Dict, Any, Optional, List

from ..connections.knowledge_connection import KnowledgeConnection


def get_knowledge(agent, topic: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """Get knowledge from the knowledge base.
    
    Args:
        agent: The ZerePyAgent instance
        topic: Optional topic to filter knowledge by
        
    Returns:
        Dictionary containing knowledge
    """
    knowledge_connection = agent.connection_manager.get_connection("knowledge")
    if not knowledge_connection:
        return {"error": "Knowledge base connection not configured"}
    
    knowledge = knowledge_connection.get_knowledge(topic)
    return {"knowledge": knowledge}


def add_knowledge(agent, topic: str, content: Any, **kwargs) -> Dict[str, Any]:
    """Add knowledge to the knowledge base.
    
    Args:
        agent: The ZerePyAgent instance
        topic: Topic identifier for the knowledge
        content: Content to store
        
    Returns:
        Status dictionary
    """
    knowledge_connection = agent.connection_manager.get_connection("knowledge")
    if not knowledge_connection:
        return {"error": "Knowledge base connection not configured"}
    
    success = knowledge_connection.add_knowledge(topic, content)
    return {"success": success, "topic": topic}


def remove_knowledge(agent, topic: str, **kwargs) -> Dict[str, Any]:
    """Remove knowledge from the knowledge base.
    
    Args:
        agent: The ZerePyAgent instance
        topic: Topic identifier to remove
        
    Returns:
        Status dictionary
    """
    knowledge_connection = agent.connection_manager.get_connection("knowledge")
    if not knowledge_connection:
        return {"error": "Knowledge base connection not configured"}
    
    success = knowledge_connection.remove_knowledge(topic)
    return {"success": success, "topic": topic}


def search_knowledge(agent, query: str, **kwargs) -> Dict[str, Any]:
    """Search the knowledge base for relevant information.
    
    Args:
        agent: The ZerePyAgent instance
        query: Search query string
        
    Returns:
        Dictionary of relevant knowledge items
    """
    knowledge_connection = agent.connection_manager.get_connection("knowledge")
    if not knowledge_connection:
        return {"error": "Knowledge base connection not configured"}
    
    results = knowledge_connection.search_knowledge(query)
    return {"results": results, "query": query}


def get_knowledge_summary(agent, **kwargs) -> Dict[str, Any]:
    """Get a summary of available knowledge topics.
    
    Args:
        agent: The ZerePyAgent instance
        
    Returns:
        Dictionary with knowledge summary
    """
    knowledge_connection = agent.connection_manager.get_connection("knowledge")
    if not knowledge_connection:
        return {"error": "Knowledge base connection not configured"}
    
    knowledge = knowledge_connection.get_knowledge()
    topics = list(knowledge.keys())
    
    return {
        "topics": topics,
        "topic_count": len(topics)
    }