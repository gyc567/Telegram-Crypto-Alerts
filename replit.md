# Telegram Crypto Alerts Bot

## Overview
This is a Telegram bot that provides cryptocurrency price alerts and technical indicator monitoring. The bot uses the Telegram API to send alerts on price movements and technical indicators for cryptocurrency trading pairs.

**Purpose**: Monitor cryptocurrency prices from Binance and send alerts via Telegram when specified conditions are met.

**Current State**: Fully configured and running on Replit. The bot is actively monitoring cryptocurrency markets and ready to receive commands via Telegram.

## Project Architecture

### Technology Stack
- **Language**: Python 3.11
- **Main Framework**: pyTelegramBotAPI
- **Data Sources**: 
  - Binance API (price data)
  - Taapi.io (technical indicators - optional)
- **Database Options**: 
  - Local JSON files (default)
  - MongoDB (optional, configured via `USE_MONGO_DB` in `src/config.py`)

### Project Structure
```
src/
├── __main__.py              # Entry point, starts bot and monitoring processes
├── telegram.py              # Telegram bot command handlers
├── config.py                # Configuration settings
├── models.py                # Data models for alerts
├── indicators.py            # Technical indicator processing
├── user_configuration.py    # User and whitelist management
├── setup.py                 # Initial bot setup
├── utils.py                 # Utility functions
├── logger.py                # Logging configuration
├── alert_processes/         # Alert processing logic
│   ├── base.py
│   ├── cex.py              # CEX price alert processor
│   └── technical.py        # Technical indicator alert processor
├── monitor/                 # Monitoring modules
│   └── large_orders/       # Large order detection system
└── resources/              # Static resources (commands, help text, defaults)
```

### Key Features
1. **Price Alerts**: Monitor crypto pair prices with conditions like ABOVE, BELOW, % change, and 24-hour % change
2. **Technical Indicators**: Support for RSI, MACD, Bollinger Bands, MA, SMA, EMA (requires Taapi.io API key)
3. **Large Order Monitoring**: Real-time detection of large orders on Binance
4. **Multi-user Support**: Whitelist system with admin controls
5. **Configurable Alerts**: Cooldown periods, custom thresholds, and multiple notification channels

## Environment Configuration

### Required Environment Variables
- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token from BotFather
- `TELEGRAM_USER_ID`: Your Telegram user ID (initial admin)
- `LOCATION`: Either "us" or "global" (Binance market location)

### Optional Environment Variables
- `TAAPIIO_APIKEY`: Taapi.io API key for technical indicators
- `TAAPIIO_TIER`: Subscription tier (free, basic, pro, expert) - defaults to "free"
- `MONGODB_CONNECTION_STRING`: MongoDB URI (if using MongoDB)
- `MONGODB_DATABASE`: MongoDB database name
- `MONGODB_COLLECTION`: MongoDB collection name

## How to Use

### Starting the Bot
The bot runs automatically via the configured workflow. It will:
1. Initialize user configuration
2. Start the Telegram bot listener
3. Begin monitoring for price alerts
4. Start the large order monitor (if enabled)

### Telegram Commands
Key commands available in your Telegram chat:
- `/view_alerts` - View all active alerts
- `/new_alert` - Create a new price or technical alert
- `/cancel_alert` - Cancel an existing alert
- `/get_price <PAIR>` - Get current price for a trading pair
- `/get_indicator` - Get current technical indicator values
- `/view_config` - View bot configuration
- `/set_config` - Modify configuration settings

See the README.md for complete command documentation.

## Recent Changes
- **[2025-11-09]** Initial Replit setup completed
  - Installed Python 3.11 and all required dependencies
  - Fixed import issues in the large order monitoring module
  - Configured workflow to run the bot automatically
  - Bot successfully started and monitoring cryptocurrency markets

## Development Notes

### Running Locally
The bot runs via: `python3 -m src`

### Configuration
- Main config file: `src/config.py`
- Default alerts: `src/resources/default_alerts.json`
- Default config: `src/resources/default_config.json`

### Database
By default, uses local JSON files stored in `src/whitelist/` directory.
To enable MongoDB, set `USE_MONGO_DB = True` in `src/config.py` and provide MongoDB credentials.

### Large Order Monitor
Enabled by default. Configuration in `src/config.py`:
- `LARGE_ORDER_MONITOR_ENABLED`: Enable/disable feature
- `LARGE_ORDER_THRESHOLD_USDT`: Minimum order size to alert (default: $2M)
- `LARGE_ORDER_TIME_WINDOW_MINUTES`: Time window for aggregation (default: 5 min)
- `LARGE_ORDER_MONITORED_SYMBOLS`: Trading pairs to monitor

## Troubleshooting

### Bot Not Responding
1. Check workflow logs for errors
2. Verify all required environment variables are set
3. Ensure Telegram bot token is valid

### Technical Indicators Not Working
- Technical indicators require a valid `TAAPIIO_APIKEY`
- Free tier has rate limits - consider upgrading for more alerts

### Alert Not Triggering
- Verify alert parameters with `/view_alerts`
- Check if cooldown period is active
- Ensure you're in the whitelist (`/whitelist VIEW`)

## Additional Resources
- Full documentation: See README.md
- Deployment guides: See docs/ directory
- Changelog: docs/CHANGELOG.md
- Contributing: See CONTRIBUTING section in README.md
