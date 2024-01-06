# Cryptocurrency Trading Bot

## Overview

This project is a Python-based cryptocurrency trading bot designed to automate cryptocurrency trading. The bot focuses on two primary features: exchange-to-exchange arbitrage and early-stage price fluctuation trading for newly listed coins.

### Features

1. **Exchange-to-Exchange Arbitrage:**
   - Capitalize on price differences by buying coins on one exchange at a lower price and selling them on another exchange at a higher price.

   **Flow Process:**

   - Select a coin-pair from predefined pairs.
   - Obtain the current coin price from various exchanges.
   - Compare the exchange with the highest and lowest price.
   - Calculate potential profit after considering fees.
   - Compare potential profit with the set minimum profitability threshold.
   - Execute or withdraw from the trade accordingly.

2. **Newly Listed Coin Trading:**
   - Purchase newly listed coins on selected exchanges and sell them when their price rises in the early stages of their market presence.

   **Flow Process:**

   - Gather basic coin information before listing.
   - Buy the coin on its initial listing.
   - Monitor price fluctuations.
   - Set flags to trigger selling when price targets are met.

## Table of Contents

1. [Setup and Configuration](#setup-and-configuration)
2. [Usage](#usage)
3. [Development](#development)

## Setup and Configuration

### Prerequisites

- Python 3.x
- Pip (Python package installer)
- ccxt (Cryptocurrency exchange library)
- // Additional requirements (to be specified as the project progresses)

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/Dennisco12/trading_bot.git
   ```

2. Navigate to the project directory:

   ```bash
   cd trading_bot
   ```

3. Install the required Python packages:

   ```bash
   pip install -r requirements.txt
   ```

4. Obtain API keys for the selected exchanges and configure them in the bot.

## Usage

### Running the Bot

1. Configure the bot:
   - Set up API keys for the chosen exchanges in the configuration file.

2. Execute the bot:

   ```bash
   python trading_bot.py
   ```

3. Use Telegram Bot to get data from Trading bot. [Link](https://t.me/ask_bloky_bot)

### Available Commands

- `python trading_bot.py` - Run the trading bot with the specified strategies.
- // Additional commands (to be specified as the project progresses)

## Development

### Structure

- `config/`: Configuration files for the trading bot.
- `strategies/`: Implementation of trading strategies.
- `utils/`: Utility functions and helper modules.
- `trading_bot.py`: Main script to execute the trading bot.
- // Additional project structure details (to be specified as the project progresses)

### GitHub Issues

For detailed tasks and project progress, please refer to the [GitHub Issues](https://github.com/Dennisco12/trading_bot/issues) section.
