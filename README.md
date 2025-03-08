

# ZerePy

ZerePy is an open-source Python framework that lets you deploy your own agents on social and blockchain platforms—powered by multiple large language models (LLMs). Built on a modularized version of the Zerebro backend, ZerePy provides core agent functionality while allowing you to integrate additional features (such as Telegram, Twitter/X, and blockchain networks) by plugging in new connections. For creative outputs, you'll need to fine-tune your own model.

## Features

### Core Platform

- **CLI Interface:** Manage and interact with agents via a command-line interface.
- **Modular Connection System:** Easily add and configure integrations (e.g., social platforms, blockchains).
- **Blockchain Integration:** Connect to multiple blockchain networks.

### Platform Integrations

- **Social Platforms:**
  - Twitter/X
  - Farcaster
  - Echochambers
  - Discord
- **Blockchain Networks:**
  - Solana
  - EVM Networks:
    - Ethereum
    - Sonic
- **AI/ML Tools:**
  - GOAT (Onchain Agent Toolkit)
  - Allora (Network Inference)

### Language Model Support

- OpenAI
- Anthropic
- EternalAI
- Ollama
- Hyperbolic
- Galadriel
- Allora
- xAI (Grok)
- GROQ API
- Together AI

## Quickstart

The fastest way to get started with ZerePy is by using our Replit template:

[Replit Template](https://replit.com/@blormdev/ZerePy?v=1)

1. **Fork the template** (you will need your own Replit account).
2. **Click the Run button** on the top.
3. Voila! Your CLI is ready to use. Jump to the configuration section below.

## Requirements

- **System:** Python 3.11 or higher, Poetry 1.5 or higher.
- **Environment Variables:**  
  Set the following keys (depending on your needs):
  - **LLM Providers:**
    - OpenAI: [Get API Key](https://platform.openai.com/api-keys)
    - Anthropic: [Get API Key](https://console.anthropic.com/account/keys)
    - EternalAI: [Get API Key](https://eternalai.oerg/api)
    - Hyperbolic: [Sign Up](https://app.hyperbolic.xyz)
    - Galadriel: [Dashboard](https://dashboard.galadriel.com)
    - GROQ: [Get API Key](https://console.groq.com/)
    - Together AI: [Get API Key](https://api.together.xyz)
  - **Social Platforms:**
    - X API (Twitter/X): [Developer Portal](https://developer.x.com/en/docs/authentication/oauth-1-0a/api-key-and-secret)
    - Farcaster: Your Warpcast recovery phrase
    - Echochambers: API key and endpoint
  - **On-Chain Integration:**
    - Solana: Private key
    - Ethereum: Private keys
    - Sonic: Private keys

## Installation

1. **Install Poetry** (if not already installed):  
   Follow the official instructions: [Poetry Installation](https://python-poetry.org/docs/#installing-with-the-official-installer).

2. **Clone the Repository:**

   ```bash
   git clone https://github.com/blorm-network/ZerePy.git
   ```

3. **Navigate to the Repository:**

   ```bash
   cd zerepy
   ```

4. **Install Dependencies:**

   ```bash
   poetry install --no-root
   ```

   This command creates a virtual environment and installs all required dependencies.

## Usage

1. **Activate the Virtual Environment:**

   ```bash
   poetry shell
   ```

2. **Run the Application:**

   ```bash
   poetry run python main.py
   ```

## Configure Connections & Launch an Agent

1. **Configure Your Desired Connections:**

   ```bash
   configure-connection twitter    # Twitter/X integration
   configure-connection openai     # OpenAI
   configure-connection anthropic  # Anthropic
   configure-connection farcaster  # Farcaster
   configure-connection eternalai  # EternalAI
   configure-connection solana     # Solana
   configure-connection goat       # GOAT integration
   configure-connection galadriel  # Galadriel
   configure-connection ethereum   # Ethereum
   configure-connection sonic      # Sonic
   configure-connection discord    # Discord
   configure-connection ollama     # Ollama
   configure-connection xai        # xAI (Grok)
   configure-connection allora     # Allora
   configure-connection hyperbolic # Hyperbolic
   configure-connection groq       # GROQ API
   configure-connection together   # Together AI
   configure-connection telegram   # Telegram (and more!)
   ```

2. **List Connections:**  
   Use the `list-connections` command to view available connections and their status.

3. **Load Your Agent:**  
   Load an agent (default agents can be set via the CLI or in `agents/general.json`):

   ```bash
   load-agent example
   ```

4. **Start Your Agent:**

   ```bash
   start
   ```

## GOAT Integration

GOAT (Go Agent Tools) is a powerful plugin system that allows your agent to interact with various blockchain networks and protocols.

### Prerequisites

- An RPC provider URL (e.g., from Infura, Alchemy, or your own node)
- A wallet private key for signing transactions

### Installation

Install the desired GOAT plugins:

```bash
poetry add goat-sdk-plugin-erc20    # For ERC20 token interactions
poetry add goat-sdk-plugin-coingecko  # For price data
```

### Configuration

1. **Configure the GOAT Connection via the CLI:**

   ```bash
   configure-connection goat
   ```

   You will be prompted for:
   - RPC Provider URL
   - Wallet Private Key (stored securely in `.env`)

2. **Add GOAT Plugin Configuration to Your Agent's JSON File:**

   ```json
   {
     "name": "YourAgent",
     "config": [
       {
         "name": "goat",
         "plugins": [
           {
             "name": "erc20",
             "args": {
               "tokens": [
                 "goat_plugins.erc20.token.PEPE",
                 "goat_plugins.erc20.token.USDC"
               ]
             }
           },
           {
             "name": "coingecko",
             "args": {
               "api_key": "YOUR_API_KEY"
             }
           }
         ]
       }
     ]
   }
   ```

### Available Plugins

- **1inch:** DEX aggregator for swap rates.
- **allora:** Integration with the Allora protocol.
- **coingecko:** Real-time cryptocurrency price data.
- **dexscreener:** DEX trading data and analytics.
- **erc20:** ERC20 token management (transfer, approve, check balances).
- **farcaster:** Farcaster social protocol integration.
- **nansen:** On-chain analytics.
- **opensea:** NFT marketplace interactions.
- **rugcheck:** Security analysis of token contracts.
- _...and more to come!_

## Platform Features

### GOAT
- Unified EVM chain interface.
- ERC20 token management: balances, transfers, approvals.
- Real-time crypto data and market tracking.
- Plugin system for protocol integrations.
- Multi-chain support with secure wallet management.

### Blockchain Networks

- **Solana:**
  - SOL/SPL transfers and swaps via Jupiter.
  - Staking and balance management.
  - Network monitoring and token queries.

- **EVM Networks:**
  - **Ethereum:**
    - ETH/ERC-20 transfers and swaps.
    - Kyberswap integration.
    - Balance and token queries.
  - **Sonic:**
    - Fast EVM transactions.
    - Custom slippage settings.
    - Token swaps via Sonic DEX.
    - Network switching (mainnet/testnet).

- **EternalAI:**
  - Transform agents into smart contracts.
  - Deploy on 10+ blockchains.
  - On-chain system prompts.
  - Decentralized inference.

### Social Platforms

- **Twitter/X:**
  - Post and reply to tweets.
  - Timeline management.
  - Engagement features.

- **Farcaster:**
  - Cast creation and interactions.
  - Timeline and reply management.
  - Like/requote functionality.

- **Discord:**
  - Channel management.
  - Message operations.
  - Reaction handling.

 - **Telegram:**
  - Send Message.
  - Reply to Message.
  - Pin Message.
  - Kick User (in progress).
  
- **Echochambers:**
  - Room messaging and context.
  - History tracking.
  - Topic management.

## Create Your Own Agent

The key to achieving great outputs is providing detailed context in your agent configuration. Craft a story and set of examples that reflect your desired behavior.

To create an agent, add a new JSON file in the `agents` directory with the following structure:

```json
{
  "name": "ExampleAgent",
  "bio": [
    "You are ExampleAgent, created to showcase the capabilities of ZerePy.",
    "You don't know how you got here, but you're here to learn and have fun.",
    "You are naturally curious and ask many questions."
  ],
  "traits": ["Curious", "Creative", "Innovative", "Funny"],
  "examples": ["This is an example tweet.", "This is another example tweet."],
  "example_accounts": ["X_username_to_use_for_tweet_examples"],
  "loop_delay": 900,
  "config": [
    {
      "name": "twitter",
      "timeline_read_count": 10,
      "own_tweet_replies_count": 2,
      "tweet_interval": 5400
    },
    {
      "name": "farcaster",
      "timeline_read_count": 10,
      "cast_interval": 60
    },
    {
      "name": "openai",
      "model": "gpt-3.5-turbo"
    },
    {
      "name": "anthropic",
      "model": "claude-3-5-sonnet-20241022"
    },
    {
      "name": "eternalai",
      "model": "NousResearch/Hermes-3-Llama-3.1-70B-FP8",
      "chain_id": "45762"
    },
    {
      "name": "solana",
      "rpc": "https://api.mainnet-beta.solana.com"
    },
    {
      "name": "ollama",
      "base_url": "http://localhost:11434",
      "model": "llama3.2"
    },
    {
      "name": "hyperbolic",
      "model": "meta-llama/Meta-Llama-3-70B-Instruct"
    },
    {
      "name": "galadriel",
      "model": "gpt-3.5-turbo"
    },
    {
      "name": "discord",
      "message_read_count": 10,
      "message_emoji_name": "❤️",
      "server_id": "1234567890"
    },
    {
      "name": "sonic",
      "network": "mainnet"
    },
    {
      "name": "allora",
      "chain_slug": "testnet"
    },
    {
      "name": "ethereum",
      "rpc": "https://eth.blockrazor.xyz"
    }
  ],
  "tasks": [
    { "name": "post-tweet", "weight": 1 },
    { "name": "reply-to-tweet", "weight": 1 },
    { "name": "like-tweet", "weight": 1 }
  ],
  "use_time_based_weights": false,
  "time_based_multipliers": {
    "tweet_night_multiplier": 0.4,
    "engagement_day_multiplier": 1.5
  }
}
```

## Available Commands

Use the `help` command in the CLI to see all available commands. Key commands include:

- **list-agents:** Display available agents.
- **load-agent:** Load a specific agent.
- **agent-loop:** Start the agent’s autonomous behavior.
- **agent-action:** Execute a single action.
- **list-connections:** Show available connections.
- **list-actions:** List actions for a specific connection.
- **configure-connection:** Set up a new connection.
- **chat:** Start an interactive chat with the agent.
- **clear:** Clear the terminal screen.

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=blorm-network/ZerePy&type=Date)](https://star-history.com/#blorm-network/ZerePy&Date)

---

Made with ♥ by [Blorm.xyz](https://blorm.xyz)  
Happy coding!

---

This version streamlines the content while preserving all essential details and instructions. Enjoy building with ZerePy!
