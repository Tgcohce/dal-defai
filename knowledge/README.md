# ZerePy Knowledge Base

This directory contains knowledge base files used by ZerePy agents. The knowledge base allows agents to store, retrieve, and search information that can be used in their interactions.

## Setting Up a Knowledge Base

1. **Create a JSON file** to store your agent's knowledge. By convention, name it `[agent_name]_knowledge.json`.

2. **Add the knowledge connection** to your agent's configuration in the agent JSON file:

```json
{
  "name": "knowledge",
  "kb_path": "./knowledge/your_agent_knowledge.json",
  "format": "json"
}
```

3. **Add knowledge-related tasks** to your agent's tasks list:

```json
{ "name": "get-knowledge", "weight": 1 },
{ "name": "add-knowledge", "weight": 1 },
{ "name": "search-knowledge", "weight": 1 }
```

## Knowledge Base Structure

The knowledge base is a JSON file structured as a dictionary of topics and their content:

```json
{
  "Topic 1": "This is information about topic 1",
  "Topic 2": {
    "Subtopic 1": "Information about subtopic 1",
    "Subtopic 2": "Information about subtopic 2"
  },
  "Topic 3": ["Item 1", "Item 2", "Item 3"]
}
```

## Knowledge Base Actions

The agent can perform the following actions with the knowledge base:

- `get_knowledge(topic)`: Retrieve knowledge for a specific topic or all knowledge if no topic is specified
- `add_knowledge(topic, content)`: Add new knowledge to the knowledge base
- `remove_knowledge(topic)`: Remove a topic from the knowledge base
- `search_knowledge(query)`: Search the knowledge base for content containing the query

## Knowledge Base Integration

The knowledge base is automatically integrated with the agent's system prompt. When the agent is initialized, all knowledge in the knowledge base is included in the system prompt, allowing the agent to use this information in its responses.

## Example Usage

1. Create a knowledge base file with information relevant to your agent's domain
2. Configure your agent to use the knowledge base
3. The agent will automatically use this knowledge when responding to queries
4. The agent can also update the knowledge base with new information it learns during interactions

## Knowledge Base Tasks

The agent can perform the following tasks with the knowledge base:

- `get-knowledge`: Retrieve and display knowledge from the knowledge base
- `add-knowledge`: Add new knowledge to the knowledge base from recent interactions
- `search-knowledge`: Search the knowledge base for specific information

These tasks can be automated as part of the agent's loop with appropriate weights in the agent configuration.