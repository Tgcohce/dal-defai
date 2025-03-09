import json
from pathlib import Path

def check_knowledge_base():
    kb_path = Path("knowledge/curtis_knowledge.json")
    if kb_path.exists():
        with open(kb_path, "r") as f:
            knowledge = json.load(f)
            
        print("\n📚 KNOWLEDGE BASE CONTENTS:")
        print("=" * 50)
        for topic, content in knowledge.items():
            print(f"\n{topic}:")
            
            if isinstance(content, str):
                print(content)
            elif isinstance(content, dict):
                for subtopic, subcontent in content.items():
                    print(f"  - {subtopic}: {subcontent}")
            elif isinstance(content, list):
                for item in content:
                    print(f"  - {item}")
            else:
                print(f"{content}")

if __name__ == "__main__":
    check_knowledge_base()
