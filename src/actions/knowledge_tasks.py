"""Task implementations for knowledge base interactions."""
import logging
from src.action_handler import register_action
import json

logger = logging.getLogger(__name__)

@register_action("get-knowledge")
def get_knowledge_task(agent, **kwargs):
    """Task to retrieve knowledge from the knowledge base."""
    try:
        topic = None
        
        if "timeline_tweets" in agent.state and agent.state["timeline_tweets"]:
            # Extract potential topic from recent tweets
            recent_tweet = agent.state["timeline_tweets"][0]
            
            # Generate a prompt to extract relevant topic from tweet
            prompt = f"""
Based on this tweet, what information from my knowledge base might be relevant?
Just respond with a single topic name or keyword, no explanation.

Tweet: {recent_tweet['text']}
"""
            topic_response = agent.prompt_llm(prompt)
            if topic_response and len(topic_response.strip()) > 0:
                topic = topic_response.strip()
        
        # Get knowledge based on the topic
        result = agent.connection_manager.perform_action(
            connection_name="knowledge",
            action_name="get-knowledge",
            params=[topic] if topic else []
        )
        
        if result and "knowledge" in result and result["knowledge"]:
            knowledge = result["knowledge"]
            
            # Format the knowledge into a readable message
            topic_str = f" about {topic}" if topic else ""
            message = f"I found the following knowledge{topic_str}:\n\n"
            
            for topic, content in knowledge.items():
                message += f"📚 {topic}:\n"
                
                if isinstance(content, str):
                    message += f"{content}\n\n"
                elif isinstance(content, dict):
                    for subtopic, subcontent in content.items():
                        message += f"- {subtopic}: {subcontent}\n"
                    message += "\n"
                elif isinstance(content, list):
                    for item in content:
                        message += f"- {item}\n"
                    message += "\n"
                else:
                    message += f"{content}\n\n"
            
            # Log the retrieved knowledge
            logger.info(f"\n📖 RETRIEVED KNOWLEDGE{topic_str}")
            return True
        else:
            logger.info(f"\n❌ No knowledge found{' about ' + topic if topic else ''}")
            return False
            
    except Exception as e:
        logger.error(f"\n❌ Error retrieving knowledge: {e}")
        return False


@register_action("add-knowledge")
def add_knowledge_task(agent, **kwargs):
    """Task to add knowledge to the knowledge base."""
    try:
        # Check if we have new information to add
        new_info = None
        topic = None
        
        if "timeline_tweets" in agent.state and agent.state["timeline_tweets"]:
            # Extract potential new knowledge from recent tweets
            recent_tweet = agent.state["timeline_tweets"][0]
            
            # Generate a prompt to extract and format knowledge from tweet
            prompt = f"""
Extract useful knowledge from this tweet that should be added to my knowledge base.
Format the response as a JSON object with "topic" and "content" fields.
Only extract factual information, not opinions.
If there's no useful knowledge, respond with an empty JSON object {{}}.

Tweet: {recent_tweet['text']}
"""
            knowledge_response = agent.prompt_llm(prompt)
            
            try:
                extracted = json.loads(knowledge_response)
                if extracted and "topic" in extracted and "content" in extracted:
                    topic = extracted["topic"]
                    new_info = extracted["content"]
            except json.JSONDecodeError:
                logger.error(f"\n❌ Error parsing LLM response as JSON: {knowledge_response}")
                pass
        
        if not topic or not new_info:
            logger.info("\n❌ No new knowledge identified to add")
            return False
            
        # Add the new knowledge
        result = agent.connection_manager.perform_action(
            connection_name="knowledge",
            action_name="add-knowledge",
            params=[topic, new_info]
        )
        
        if result and "success" in result and result["success"]:
            logger.info(f"\n✅ Added new knowledge about '{topic}'")
            return True
        else:
            logger.info(f"\n❌ Failed to add knowledge about '{topic}'")
            return False
            
    except Exception as e:
        logger.error(f"\n❌ Error adding knowledge: {e}")
        return False


@register_action("search-knowledge")
def search_knowledge_task(agent, **kwargs):
    """Task to search the knowledge base for specific information."""
    try:
        query = None
        
        if "timeline_tweets" in agent.state and agent.state["timeline_tweets"]:
            # Extract potential query from recent tweets
            recent_tweet = agent.state["timeline_tweets"][0]
            
            # Generate a prompt to extract search query from tweet
            prompt = f"""
Based on this tweet, what should I search for in my knowledge base?
Just respond with a single search term or phrase, no explanation.

Tweet: {recent_tweet['text']}
"""
            query_response = agent.prompt_llm(prompt)
            if query_response and len(query_response.strip()) > 0:
                query = query_response.strip()
        
        if not query:
            # If no query from tweets, generate a random relevant query
            prompt = "Generate a single search term relevant to Sonic Labs that I could use to query my knowledge base. Just the term, no explanation."
            query_response = agent.prompt_llm(prompt)
            if query_response and len(query_response.strip()) > 0:
                query = query_response.strip()
            else:
                query = "Sonic"  # Fallback query
        
        # Search the knowledge base
        result = agent.connection_manager.perform_action(
            connection_name="knowledge",
            action_name="search-knowledge",
            params=[query]
        )
        
        if result and "results" in result and result["results"]:
            search_results = result["results"]
            
            # Format the search results into a readable message
            message = f"🔍 Search results for '{query}':\n\n"
            
            for topic, content in search_results.items():
                message += f"📚 {topic}:\n"
                
                if isinstance(content, str):
                    message += f"{content}\n\n"
                elif isinstance(content, dict):
                    for subtopic, subcontent in content.items():
                        message += f"- {subtopic}: {subcontent}\n"
                    message += "\n"
                elif isinstance(content, list):
                    for item in content:
                        message += f"- {item}\n"
                    message += "\n"
                else:
                    message += f"{content}\n\n"
            
            # Log the search results
            logger.info(f"\n🔍 SEARCHED KNOWLEDGE BASE FOR '{query}'")
            return True
        else:
            logger.info(f"\n❌ No results found for search query '{query}'")
            return False
            
    except Exception as e:
        logger.error(f"\n❌ Error searching knowledge: {e}")
        return False