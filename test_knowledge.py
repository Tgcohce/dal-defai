import json
import os
from pathlib import Path
import logging

from src.connections.knowledge_connection import KnowledgeConnection

logging.basicConfig(level=logging.INFO, format='%(message)s')

def test_knowledge_base():
    # Ensure knowledge directory exists
    os.makedirs("./knowledge", exist_ok=True)
    
    # Create test knowledge file
    knowledge_path = "./knowledge/test_knowledge.json"
    test_knowledge = {
        "Test Topic": "This is test knowledge content",
        "Airdrop Information": "The next airdrop is scheduled for March 2024",
        "FAQ": {
            "What is the next airdrop date?": "March 2024",
            "How much will be airdropped?": "10,000 tokens will be airdropped"
        }
    }
    
    with open(knowledge_path, "w") as f:
        json.dump(test_knowledge, f, indent=2)
    
    # Create test connection config
    config = {
        "name": "knowledge",
        "kb_path": knowledge_path,
        "format": "json"
    }
    
    # Create and test the knowledge connection
    knowledge_connection = KnowledgeConnection(config)
    print("Knowledge loaded:", knowledge_connection.get_knowledge())
    
    # Create a prompt with the knowledge to test if it works
    prompt_parts = ["Test system prompt"]
    knowledge = knowledge_connection.get_knowledge()
    
    if knowledge:
        prompt_parts.append("\nHere is your knowledge base:")
        for topic, content in knowledge.items():
            if isinstance(content, str):
                prompt_parts.append(f"\n{topic}:")
                prompt_parts.append(content)
                print(f"Added knowledge topic: {topic}")
            elif isinstance(content, dict):
                prompt_parts.append(f"\n{topic}:")
                print(f"Added knowledge topic: {topic} with {len(content)} subtopics")
                for subtopic, subcontent in content.items():
                    prompt_parts.append(f"- {subtopic}: {subcontent}")
                    print(f"  - Subtopic: {subtopic}")
            else:
                prompt_parts.append(f"\n{topic}: {content}")
                print(f"Added knowledge topic: {topic}")
    
    system_prompt = "\n".join(prompt_parts)
    print("\nFINAL SYSTEM PROMPT:")
    print("-" * 50)
    print(system_prompt)
    print("-" * 50)

if __name__ == "__main__":
    test_knowledge_base()
