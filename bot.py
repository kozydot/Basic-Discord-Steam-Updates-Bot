import os
import discord
import aiohttp
from discord.ext import commands, tasks
from steam_api import SteamAPI
from config import Config
from utils import setup_logging, log_command
from tracker import GameTracker
import logging
from datetime import datetime

# Set up logging
logger = setup_logging()

# Set up required intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True

class CustomHelpCommand(commands.HelpCommand):
    """Custom help command with detailed information"""
    async def send_bot_help(self, mapping):
        user_info = f"{self.context.author} (ID: {self.context.author.id})"
        log_command(logger, logging.INFO, "Help command executed", user=user_info, command="!help")
        
        embed = discord.Embed(
            title="🎮 Steam Bot Commands",
            description="Monitor and get notified about Steam game releases!",
            color=discord.Color.blue()
        )
        
        commands = [c for c in self.context.bot.commands]
        for cmd in sorted(commands, key=lambda x: x.name):
            embed.add_field(
                name=f"`{self.context.clean_prefix}{cmd.name}`",
                value=cmd.help or "No description available",
                inline=False
            )
        
        await self.get_destination().send(embed=embed)

class SteamBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=Config.PREFIX,
            intents=intents,
            help_command=CustomHelpCommand()
        )
        self.steam = SteamAPI()
        self.tracker = GameTracker()
        
    async def setup_hook(self):
        """Initialize bot and start background tasks"""
        log_command(logger, logging.INFO, "Initializing bot and connecting to Steam API")
        await self.steam.start()
        self.check_tracked_games.start()
        log_command(logger, logging.INFO, "Bot is ready and connected to Steam API")
        
    @tasks.loop(minutes=30)
    async def check_tracked_games(self):
        """Check for updates to tracked games"""
        try:
            log_command(logger, logging.INFO, "Checking tracked games for updates")
            games = self.tracker.get_tracked_games()
            
            for game in games:
                # Get latest game data from Steam
                store_url = f"https://store.steampowered.com/api/appdetails?appids={game['id']}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(store_url) as response:
                        if response.status == 200:
                            data = await response.json()
                            game_data = data.get(str(game['id']), {}).get('data', {})
                            
                            if game_data:
                                # Update tracker with new data
                                notifications = self.tracker.update_game_data(
                                    game['id'],
                                    price=game_data.get('price_overview', {}).get('final_formatted'),
                                    release_date=game_data.get('release_date', {}).get('date'),
                                    preorder_status=game_data.get('release_date', {}).get('coming_soon', False),
                                    last_update=datetime.now().isoformat()
                                )
                                
                                # Send notifications if there are changes
                                if notifications:
                                    channels = self.tracker.get_notification_channels(game['id'])
                                    for channel_data in channels:
                                        channel = self.get_channel(channel_data['channel_id'])
                                        if channel:
                                            for notif in notifications:
                                                users_mention = " ".join(f"<@{user_id}>" for user_id in channel_data['users'])
                                                embed = discord.Embed(
                                                    title=f"Game Update: {game['name']}",
                                                    description=notif['message'],
                                                    color=discord.Color.blue(),
                                                    timestamp=datetime.now()
                                                )
                                                await channel.send(users_mention, embed=embed)
                
        except Exception as e:
            log_command(logger, logging.ERROR, f"Error checking tracked games: {str(e)}")

bot = SteamBot()

@bot.command()
async def track(ctx, *, game_name: str = None):
    """🎮 Track a game for updates
    
    Usage: !track <game name>
    Example: !track Starfield
    
    You'll be notified about:
    📅 Release date changes
    💰 Price updates
    🎮 Pre-order availability
    📢 Major updates and announcements"""
    
    user_info = f"{ctx.author} (ID: {ctx.author.id})"
    cmd_info = f"!track {game_name if game_name else ''}"
    
    if not game_name:
        # Show currently tracked games
        tracked = bot.tracker.get_tracked_games(channel_id=ctx.channel.id, user_id=ctx.author.id)
        
        embed = discord.Embed(
            title="🎮 Your Tracked Games",
            color=discord.Color.blue()
        )
        
        if tracked:
            for game in tracked:
                current_data = game['current_data']
                value = []
                if current_data['price']:
                    value.append(f"💰 Price: {current_data['price']}")
                if current_data['release_date']:
                    value.append(f"📅 Release: {current_data['release_date']}")
                if current_data['preorder_status']:
                    value.append("🎮 Pre-order available")
                    
                embed.add_field(
                    name=game['name'],
                    value="\n".join(value) or "No current data",
                    inline=False
                )
        else:
            embed.description = "You're not tracking any games in this channel.\nUse `!track <game name>` to start tracking!"
            
        return await ctx.send(embed=embed)
    
    async with ctx.typing():
        try:
            log_command(logger, logging.INFO, f"Searching for game to track: {game_name}", user=user_info, command=cmd_info)
            
            # Search for the game
            games = await bot.steam.search_games(game_name)
            
            if not games:
                embed = discord.Embed(
                    title="❌ Game Not Found",
                    description=f"Could not find any games matching: **{game_name}**\n"
                              f"Please check the spelling and try again.",
                    color=discord.Color.red()
                )
                return await ctx.send(embed=embed)
            
            # Get details for the first match
            game = games[0]
            success = bot.tracker.track_game(
                game_id=int(game['appid']),
                game_name=game['name'],
                channel_id=ctx.channel.id,
                user_id=ctx.author.id
            )
            
            if success:
                embed = discord.Embed(
                    title="✅ Game Tracked",
                    description=f"Now tracking **{game['name']}**!\n\n"
                              f"You'll be notified in this channel about:\n"
                              f"📅 Release date changes\n"
                              f"💰 Price updates\n"
                              f"🎮 Pre-order availability\n"
                              f"📢 Major updates",
                    color=discord.Color.green()
                )
                log_command(logger, logging.INFO, 
                          f"Successfully tracking {game['name']}", 
                          user=user_info, 
                          command=cmd_info)
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description="Failed to start tracking the game. Please try again later.",
                    color=discord.Color.red()
                )
                log_command(logger, logging.ERROR, 
                          f"Failed to track {game['name']}", 
                          user=user_info, 
                          command=cmd_info)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            log_command(logger, logging.ERROR, f"Track command failed: {str(e)}", user=user_info, command=cmd_info)
            embed = discord.Embed(
                title="❌ Error",
                description="An error occurred while trying to track the game. Please try again later.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

@bot.command()
async def playercount(ctx, *, query: str = None):
    """👥 Show current player counts for games
    
    Usage: 
    • !playercount - Show top 10 most played games
    • !playercount <game name> - Search for a specific game
    
    Examples:
    • !playercount
    • !playercount Counter-Strike 2
    • !playercount Dota 2"""
    
    user_info = f"{ctx.author} (ID: {ctx.author.id})"
    cmd_info = f"!playercount {query if query else ''}"
    
    async with ctx.typing():
        try:
            if query is None:
                # Show top 10 games
                log_command(logger, logging.INFO, "Fetching top 10 games", user=user_info, command=cmd_info)
                games = await bot.steam.get_top_games(limit=10)
                
                if not games:
                    embed = discord.Embed(
                        title="❌ Error",
                        description="Failed to fetch top games. Please try again later.",
                        color=discord.Color.red()
                    )
                    return await ctx.send(embed=embed)
                
                embed = discord.Embed(
                    title="🎮 Top Steam Games",
                    description="Current most played games on Steam",
                    color=discord.Color.blue(),
                    timestamp=ctx.message.created_at
                )
                
                for i, game in enumerate(games, 1):
                    player_count = f"{game['player_count']:,}"
                    peak_today = f"{game['peak_today']:,}"
                    embed.add_field(
                        name=f"{i}. {game['name']}",
                        value=f"Current Players: **{player_count}**\n"
                              f"Peak Today: **{peak_today}**",
                        inline=False
                    )
                
                embed.set_footer(text="Data from Steam • Updated in real-time")
                log_command(logger, logging.INFO, 
                          f"Successfully fetched top games (found {len(games)})", 
                          user=user_info, 
                          command=cmd_info)
            else:
                # Search for specific game
                log_command(logger, logging.INFO, f"Searching for game: {query}", user=user_info, command=cmd_info)
                games = await bot.steam.search_games(query)
                
                if not games:
                    embed = discord.Embed(
                        title="❌ Game Not Found",
                        description=f"No games found matching: **{query}**",
                        color=discord.Color.red()
                    )
                    return await ctx.send(embed=embed)
                
                # Get player counts for found games
                embed = discord.Embed(
                    title=f"🎮 Game Player Counts",
                    color=discord.Color.blue(),
                    timestamp=ctx.message.created_at
                )
                
                for game in games[:5]:
                    try:
                        stats = await bot.steam.get_player_count(game['appid'])
                        player_count = f"{stats['player_count']:,}"
                        embed.add_field(
                            name=game['name'],
                            value=f"Current Players: **{player_count}**",
                            inline=False
                        )
                    except Exception as e:
                        embed.add_field(
                            name=game['name'],
                            value="Unable to fetch player count",
                            inline=False
                        )
                
                embed.set_footer(text="Data from Steam • Updated in real-time")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            log_command(logger, logging.ERROR, f"Command failed: {str(e)}", user=user_info, command=cmd_info)
            embed = discord.Embed(
                title="❌ Error",
                description="An error occurred while fetching player counts. Please try again later.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

if __name__ == "__main__":
    log_command(logger, logging.INFO, "Starting Steam Bot...")
    bot.run(Config.DISCORD_TOKEN)