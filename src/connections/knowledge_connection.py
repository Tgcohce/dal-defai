"""Connection for managing knowledge base access."""
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

from ..connections.base_connection import BaseConnection


class KnowledgeConnection(BaseConnection):
    """Connection for accessing a knowledge base of documents."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the knowledge base connection.
        
        Args:
            config: Configuration dictionary containing:
                - kb_path: Path to the knowledge base directory or file
                - format: Format of the knowledge base (json, txt, directory)
        """
        super().__init__(config)
        self.kb_path = config.get("kb_path", "./knowledge")
        self.format = config.get("format", "json")
        self.knowledge_data = self._load_knowledge()
        
        # Register actions
        self.register_actions()
    
    def validate_config(self, config) -> Dict[str, Any]:
        """Validate the configuration provided for this connection.
        
        Args:
            config: Configuration dictionary
        
        Returns:
            The validated configuration
        """
        # Simple validation - just check if kb_path is present
        if "kb_path" not in config:
            config["kb_path"] = "./knowledge"
        return config
        
    def register_actions(self) -> None:
        """Register actions for this connection."""
        from typing import NamedTuple, Callable, List
        
        class Parameter(NamedTuple):
            name: str
            description: str
            required: bool = True
        
        class Action(NamedTuple):
            description: str
            function: Callable
            parameters: List[Parameter]
        
        # Register actions for knowledge operations
        from dataclasses import dataclass
        from typing import Callable, List
        
        @dataclass
        class ActionParameter:
            name: str
            required: bool
            type: type
            description: str
        
        @dataclass
        class Action:
            name: str
            parameters: List[ActionParameter]
            description: str
            function: Callable
        
        # Register actions using the proper action format
        self.actions = {
            "get-knowledge": self.get_knowledge,
            "add-knowledge": self.add_knowledge,
            "remove-knowledge": self.remove_knowledge,
            "search-knowledge": self.search_knowledge,
            "get-knowledge-summary": self.get_knowledge_summary
        }
        
    @property
    def is_llm_provider(self) -> bool:
        """Check if this connection is an LLM provider.
        
        Returns:
            False since knowledge base is not an LLM provider
        """
        return False
        
    def _load_knowledge(self) -> Dict[str, Any]:
        """Load knowledge from the specified source."""
        if not os.path.exists(self.kb_path):
            print(f"Warning: Knowledge base path {self.kb_path} does not exist. Creating empty knowledge base.")
            os.makedirs(os.path.dirname(self.kb_path), exist_ok=True)
            if self.format == "json":
                with open(self.kb_path, "w") as f:
                    json.dump({}, f)
            return {}
            
        if self.format == "json":
            try:
                with open(self.kb_path, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Knowledge base file {self.kb_path} is not valid JSON. Creating empty knowledge base.")
                return {}
        
        elif self.format == "directory":
            knowledge = {}
            for file_path in Path(self.kb_path).glob("**/*"):
                if file_path.is_file():
                    try:
                        with open(file_path, "r") as f:
                            relative_path = file_path.relative_to(self.kb_path)
                            knowledge[str(relative_path)] = f.read()
                    except Exception as e:
                        print(f"Warning: Failed to read {file_path}: {e}")
            return knowledge
            
        else:
            print(f"Warning: Unsupported knowledge base format {self.format}. Using empty knowledge base.")
            return {}
    
    def get_knowledge(self, topic: Optional[str] = None) -> Dict[str, Any]:
        """Get knowledge from the knowledge base.
        
        Args:
            topic: Optional topic to filter knowledge by
            
        Returns:
            Dictionary containing knowledge
        """
        if topic is None:
            return self.knowledge_data
        
        if topic in self.knowledge_data:
            return {topic: self.knowledge_data[topic]}
            
        # Search for topic in values if it's not a direct key
        filtered_knowledge = {}
        for key, value in self.knowledge_data.items():
            if isinstance(value, str) and topic.lower() in value.lower():
                filtered_knowledge[key] = value
            elif isinstance(value, dict) and any(topic.lower() in str(v).lower() for v in value.values()):
                filtered_knowledge[key] = value
                
        return filtered_knowledge
    
    def add_knowledge(self, topic: str, content: Any) -> bool:
        """Add knowledge to the knowledge base.
        
        Args:
            topic: Topic identifier for the knowledge
            content: Content to store
            
        Returns:
            Success status
        """
        self.knowledge_data[topic] = content
        return self._save_knowledge()
    
    def remove_knowledge(self, topic: str) -> bool:
        """Remove knowledge from the knowledge base.
        
        Args:
            topic: Topic identifier to remove
            
        Returns:
            Success status
        """
        if topic in self.knowledge_data:
            del self.knowledge_data[topic]
            return self._save_knowledge()
        return False
    
    def _save_knowledge(self) -> bool:
        """Save knowledge to the storage."""
        try:
            if self.format == "json":
                with open(self.kb_path, "w") as f:
                    json.dump(self.knowledge_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving knowledge base: {e}")
            return False
    
    def search_knowledge(self, query: str) -> Dict[str, Any]:
        """Search the knowledge base for relevant information.
        
        Args:
            query: Search query string
            
        Returns:
            Dictionary of relevant knowledge items
        """
        results = {}
        query = query.lower()
        
        for key, value in self.knowledge_data.items():
            if query in key.lower():
                results[key] = value
                continue
                
            if isinstance(value, str):
                if query in value.lower():
                    results[key] = value
            elif isinstance(value, dict):
                matching_items = {}
                for k, v in value.items():
                    if (query in k.lower() or 
                       (isinstance(v, str) and query in v.lower())):
                        matching_items[k] = v
                if matching_items:
                    results[key] = matching_items
                    
        return results
        
    def is_configured(self, verbose: bool = False) -> bool:
        """Check if the knowledge connection is configured.
        
        Args:
            verbose: Whether to print verbose information
            
        Returns:
            Whether the connection is configured
        """
        # Knowledge connection is always considered configured
        # since we create an empty knowledge base if none exists
        return True
        
    def configure(self) -> bool:
        """Configure the knowledge connection.
        
        Returns:
            Success status
        """
        # Just make sure the knowledge file exists
        self._load_knowledge()
        return True
        
    def get_knowledge_summary(self) -> Dict[str, Any]:
        """Get a summary of available knowledge topics.
        
        Returns:
            Dictionary with knowledge summary
        """
        topics = list(self.knowledge_data.keys())
        
        return {
            "topics": topics,
            "topic_count": len(topics)
        }
        
    def perform_action(self, action_name: str, params: Dict[str, Any]) -> Any:
        """Perform an action on the knowledge base.
        
        Args:
            action_name: Name of the action to perform
            params: Parameters for the action
            
        Returns:
            Result of the action
        """
        if action_name not in self.actions:
            raise ValueError(f"Unknown action: {action_name}")
            
        action = self.actions[action_name]
        return action.function(**params)