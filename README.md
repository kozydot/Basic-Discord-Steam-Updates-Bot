# Basic Discord Steam Updates Bot

A Discord bot that monitors Steam games for updates, tracks player counts, and sends notifications about game changes, prices, and releases.

## Features

🎮 **Game Tracking**
- Monitor specific games for updates
- Get notified about price changes
- Track release dates and pre-orders
- Follow game announcements and patches

📊 **Player Statistics**
- View current player counts
- See top played games
- Track peak player numbers
- Search game statistics

🔔 **Smart Notifications**
- Price drop alerts
- Release date changes
- Pre-order availability
- Major game updates

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Discord Bot Token (from [Discord Developer Portal](https://discord.com/developers/applications))
- Steam Web API Key (from [Steam Dev](https://steamcommunity.com/dev/apikey))

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/steam-discord-bot.git
cd steam-discord-bot
```

2. **Create virtual environment (recommended)**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up configuration**
```bash
# Copy example config
cp config.example.py config.py

# Edit config.py with your tokens
# OR use environment variables (recommended)
```

5. **Configure environment variables**
```bash
# Windows (Command Prompt)
set DISCORD_TOKEN=your_discord_token_here
set STEAM_API_KEY=your_steam_api_key_here

# Windows (PowerShell)
$env:DISCORD_TOKEN="your_discord_token_here"
$env:STEAM_API_KEY="your_steam_api_key_here"

# Linux/Mac
export DISCORD_TOKEN="your_discord_token_here"
export STEAM_API_KEY="your_steam_api_key_here"
```

### Running the Bot

1. **Start the bot**
```bash
python bot.py
```

2. **Invite bot to your server**
- Go to [Discord Developer Portal](https://discord.com/developers/applications)
- Select your application
- Go to OAuth2 → URL Generator
- Select bot scope and required permissions
- Use generated URL to invite bot

## Bot Commands

### Game Tracking
- `!track <game>` - Track a game for updates
  ```
  Example: !track Starfield
  ```
- `!track` - View your tracked games

### Player Statistics
- `!playercount` - Show top 10 most played games
- `!playercount <game>` - Check players for specific game
  ```
  Example: !playercount Counter-Strike 2
  ```

### Help & Info
- `!help` - Show all commands and usage

## Features in Detail

### Game Tracking
The bot checks tracked games every 30 minutes for:
- Price changes (increases/decreases)
- Release date updates
- Pre-order availability
- Major announcements
- Patches and DLC releases

### Player Count Statistics
Real-time statistics include:
- Current player count
- 24-hour peak
- All-time peak
- Player trends

### Notifications
The bot sends notifications in your specified channel when:
- Tracked game prices change
- Release dates are updated
- Pre-orders become available
- Major updates are released

## Configuration Options

### Discord Settings
- Custom command prefix (default: !)
- Notification channel selection
- Role-based command permissions

### Steam Settings
- Region for prices and availability
- Update check frequency
- Notification preferences

## Project Structure

```
steam-discord-bot/
├── bot.py              # Main bot implementation
├── steam_api.py        # Steam API integration
├── tracker.py          # Game tracking system
├── utils.py           # Utility functions
├── config.example.py  # Configuration template
├── requirements.txt   # Python dependencies
└── logs/             # Log files directory
```

## Troubleshooting

### Common Issues

1. **Bot won't start**
   - Check if tokens are correctly set
   - Verify Python version (3.8+ required)
   - Ensure all dependencies are installed

2. **Command not working**
   - Verify bot has required permissions
   - Check command syntax
   - Look for errors in logs/

3. **No notifications**
   - Confirm bot has channel permissions
   - Check if game is being tracked
   - Verify notification settings

### Getting Help

If you encounter issues:
1. Check the logs in `logs/` directory
2. Enable debug logging in config
3. Create an issue on GitHub

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to your branch
5. Create a Pull Request

## Security

- Never commit sensitive data
- Use environment variables for tokens
- Keep .env and config.py private
- Check .gitignore before committing

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- discord.py for Discord API wrapper
- Steam Web API for game data
- Contributors and testers

## Support

Need help? Create an issue or join our Discord server for support.
