import os
import aiohttp
import asyncio
import json
from config import Config
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from utils import setup_logging, log_command
import logging

# Set up logging
logger = setup_logging()

class SteamAPIError(Exception):
    """Base exception for Steam API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code

class SteamAPI:
    def __init__(self):
        self.base_url = "https://api.steampowered.com"
        self.session = None
        self.rate_limit_remaining = 10
        self.retry_delay = 5.0
        
    async def start(self):
        """Initialize the client session"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
            log_command(logger, logging.INFO, "Steam API client session initialized", command="start")
            
    async def close(self):
        """Clean up resources"""
        if self.session is not None:
            await self.session.close()
            self.session = None
            log_command(logger, logging.INFO, "Steam API client session closed", command="close")
    
    async def get_top_games(self, limit: int = 10) -> List[Dict]:
        """Get top games by current player count"""
        log_command(logger, logging.INFO, f"Fetching top {limit} games by player count", command="get_top_games")
        try:
            # Most popular Steam games
            popular_games = [
                730,    # CS2
                570,    # Dota 2
                440,    # Team Fortress 2
                578080, # PUBG
                252490, # Rust
                1172470,# Apex Legends
                1938090,# Counter-Strike 2
                346110, # ARK
                271590, # GTA V
                1599340,# Lost Ark
                1172620,# Baldur's Gate 3
                359550, # Rainbow Six Siege
                230410, # Warframe
                548430, # Deep Rock Galactic
                1949440 # Palworld
            ]

            results = []
            for appid in popular_games:
                try:
                    # Get game details from Steam Store API
                    store_url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
                    log_command(logger, logging.INFO, f"Fetching game details for {appid}", command="get_top_games")
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(store_url) as response:
                            if response.status == 200:
                                details = await response.json()
                                game_data = details.get(str(appid), {}).get('data', {})
                                
                                if game_data:
                                    # Get current players
                                    player_data = await self._make_request(
                                        "ISteamUserStats/GetNumberOfCurrentPlayers/v1",
                                        {'appid': appid}
                                    )
                                    
                                    player_count = player_data.get('player_count', 0)
                                    if player_count > 0:
                                        results.append({
                                            'appid': appid,
                                            'name': game_data.get('name', f'Game {appid}'),
                                            'player_count': player_count,
                                            'peak_today': player_count,  # Steam API limitation
                                            'header_image': game_data.get('header_image', ''),
                                            'genres': [g.get('description', '') for g in game_data.get('genres', [])]
                                        })
                                        log_command(logger, logging.INFO, 
                                                  f"Found {player_count:,} players for {game_data.get('name')}", 
                                                  command="get_top_games")
                
                except Exception as e:
                    log_command(logger, logging.ERROR, 
                              f"Error fetching data for game {appid}: {str(e)}", 
                              command="get_top_games")
                    continue
            
            # Sort by player count and return top N
            results.sort(key=lambda x: x['player_count'], reverse=True)
            log_command(logger, logging.INFO, 
                       f"Successfully fetched {len(results)} games", 
                       command="get_top_games")
            return results[:limit]
            
        except Exception as e:
            log_command(logger, logging.ERROR, 
                       f"Failed to get top games: {str(e)}", 
                       command="get_top_games")
            return []

    async def _make_request(self, endpoint: str, params: Dict) -> Dict:
        """Make API request with retries and error handling"""
        if self.session is None:
            log_command(logger, logging.ERROR, 
                       "API client not initialized", 
                       command="_make_request")
            raise SteamAPIError("API client not initialized. Call start() first.")
            
        params['key'] = Config.STEAM_API_KEY
        url = f"{self.base_url}/{endpoint}"
        
        for attempt in range(3):
            try:
                log_command(logger, logging.INFO, 
                          f"Making request to {endpoint} (Attempt {attempt + 1}/3)", 
                          command="_make_request")
                          
                async with self.session.get(url, params=params) as response:
                    if response.status == 429:
                        self.retry_delay *= 2
                        log_command(logger, logging.WARNING, 
                                  f"Rate limited. Retrying in {self.retry_delay}s", 
                                  command="_make_request")
                        await asyncio.sleep(self.retry_delay)
                        continue
                        
                    data = await response.json()
                    if response.status != 200:
                        log_command(logger, logging.ERROR, 
                                  f"API request failed: {response.status}", 
                                  command="_make_request")
                        raise SteamAPIError(f"API request failed: {response.status}")
                        
                    log_command(logger, logging.INFO, 
                              "Request successful", 
                              command="_make_request")
                    return data.get('response', {})
                    
            except aiohttp.ClientError as e:
                if attempt == 2:
                    log_command(logger, logging.ERROR, 
                              f"Network error: {str(e)}", 
                              command="_make_request")
                    raise SteamAPIError(f"Network error: {str(e)}")
                await asyncio.sleep(self.retry_delay)
                continue
                
    async def search_games(self, query: str, limit: int = 5) -> List[Dict]:
        """Search for games by name"""
        if not query:
            return []
            
        try:
            log_command(logger, logging.INFO, f"Searching for game: {query}", command="search_games")
            # Use Steam Store API for search
            search_url = f"https://store.steampowered.com/api/storesearch?term={query}&l=english&cc=US"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('total', 0) > 0:
                            results = []
                            for item in data.get('items', [])[:limit]:
                                results.append({
                                    'appid': item.get('id'),
                                    'name': item.get('name'),
                                    'type': item.get('type')
                                })
                            log_command(logger, logging.INFO, 
                                      f"Found {len(results)} games matching '{query}'", 
                                      command="search_games")
                            return results
            
            log_command(logger, logging.WARNING, 
                       f"No games found matching '{query}'", 
                       command="search_games")
            return []
            
        except Exception as e:
            log_command(logger, logging.ERROR, 
                       f"Search error: {str(e)}", 
                       command="search_games")
            return []

    async def get_player_count(self, appid: int) -> Dict:
        """Get current player count for a game"""
        log_command(logger, logging.INFO, 
                   f"Fetching player count for game {appid}", 
                   command="get_player_count")
        try:
            data = await self._make_request("ISteamUserStats/GetNumberOfCurrentPlayers/v1", {'appid': appid})
            count = data.get('player_count', 0)
            log_command(logger, logging.INFO, 
                       f"Found {count:,} players for game {appid}", 
                       command="get_player_count")
            return {'player_count': count}
        except Exception as e:
            log_command(logger, logging.ERROR, 
                       f"Failed to get player count: {str(e)}", 
                       command="get_player_count")
            return {'player_count': 0}