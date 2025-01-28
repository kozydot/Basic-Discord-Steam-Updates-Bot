import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from utils import setup_logging, log_command
import logging

logger = setup_logging()

class GameTracker:
    def __init__(self):
        self.tracked_games = {}
        self.data_file = "game_tracking.json"
        self._load_tracking_data()

    def _load_tracking_data(self):
        """Load tracking data from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    self.tracked_games = json.load(f)
                log_command(logger, logging.INFO, 
                          f"Loaded {len(self.tracked_games)} tracked games", 
                          command="load_tracking_data")
        except Exception as e:
            log_command(logger, logging.ERROR, 
                       f"Failed to load tracking data: {str(e)}", 
                       command="load_tracking_data")

    def _save_tracking_data(self):
        """Save tracking data to file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.tracked_games, f, indent=2)
            log_command(logger, logging.INFO, 
                       "Saved tracking data", 
                       command="save_tracking_data")
        except Exception as e:
            log_command(logger, logging.ERROR, 
                       f"Failed to save tracking data: {str(e)}", 
                       command="save_tracking_data")

    def track_game(self, game_id: int, game_name: str, channel_id: int, user_id: int) -> bool:
        """Start tracking a game"""
        try:
            game_key = str(game_id)
            if game_key not in self.tracked_games:
                self.tracked_games[game_key] = {
                    'id': game_id,
                    'name': game_name,
                    'watchers': {},
                    'last_check': None,
                    'current_data': {
                        'price': None,
                        'release_date': None,
                        'preorder_status': False,
                        'last_update': None
                    }
                }
            
            # Add channel and user to watchers
            if str(channel_id) not in self.tracked_games[game_key]['watchers']:
                self.tracked_games[game_key]['watchers'][str(channel_id)] = []
            
            if user_id not in self.tracked_games[game_key]['watchers'][str(channel_id)]:
                self.tracked_games[game_key]['watchers'][str(channel_id)].append(user_id)
            
            self._save_tracking_data()
            log_command(logger, logging.INFO,
                       f"Started tracking {game_name} (ID: {game_id}) for user {user_id} in channel {channel_id}",
                       command="track_game")
            return True
        except Exception as e:
            log_command(logger, logging.ERROR,
                       f"Failed to track game {game_name}: {str(e)}",
                       command="track_game")
            return False

    def untrack_game(self, game_id: int, channel_id: int, user_id: int) -> bool:
        """Stop tracking a game for a user in a channel"""
        try:
            game_key = str(game_id)
            if game_key in self.tracked_games:
                channel_key = str(channel_id)
                if channel_key in self.tracked_games[game_key]['watchers']:
                    if user_id in self.tracked_games[game_key]['watchers'][channel_key]:
                        self.tracked_games[game_key]['watchers'][channel_key].remove(user_id)
                        
                        # Clean up if no watchers left
                        if not self.tracked_games[game_key]['watchers'][channel_key]:
                            del self.tracked_games[game_key]['watchers'][channel_key]
                        if not self.tracked_games[game_key]['watchers']:
                            del self.tracked_games[game_key]
                        
                        self._save_tracking_data()
                        log_command(logger, logging.INFO,
                                  f"Stopped tracking game {game_id} for user {user_id} in channel {channel_id}",
                                  command="untrack_game")
                        return True
            return False
        except Exception as e:
            log_command(logger, logging.ERROR,
                       f"Failed to untrack game {game_id}: {str(e)}",
                       command="untrack_game")
            return False

    def get_tracked_games(self, channel_id: Optional[int] = None, user_id: Optional[int] = None) -> List[Dict]:
        """Get list of tracked games, optionally filtered by channel and/or user"""
        try:
            results = []
            for game_id, game_data in self.tracked_games.items():
                if channel_id is not None:
                    channel_key = str(channel_id)
                    if channel_key not in game_data['watchers']:
                        continue
                    if user_id is not None and user_id not in game_data['watchers'][channel_key]:
                        continue
                results.append({
                    'id': game_data['id'],
                    'name': game_data['name'],
                    'current_data': game_data['current_data']
                })
            return results
        except Exception as e:
            log_command(logger, logging.ERROR,
                       f"Failed to get tracked games: {str(e)}",
                       command="get_tracked_games")
            return []

    def update_game_data(self, game_id: int, price: Optional[str] = None, 
                        release_date: Optional[str] = None, preorder_status: Optional[bool] = None,
                        last_update: Optional[str] = None) -> List[Dict]:
        """Update game data and return notifications if there are changes"""
        try:
            game_key = str(game_id)
            if game_key not in self.tracked_games:
                return []

            notifications = []
            current = self.tracked_games[game_key]['current_data']
            game_name = self.tracked_games[game_key]['name']

            # Check for changes and create notifications
            if price is not None and price != current['price']:
                if current['price'] is not None:
                    notifications.append({
                        'type': 'price',
                        'message': f"💰 Price Update: {game_name}\n"
                                 f"Previous: {current['price']}\n"
                                 f"New: {price}"
                    })
                current['price'] = price

            if release_date is not None and release_date != current['release_date']:
                if current['release_date'] is not None:
                    notifications.append({
                        'type': 'release_date',
                        'message': f"📅 Release Date Changed: {game_name}\n"
                                 f"Previous: {current['release_date']}\n"
                                 f"New: {release_date}"
                    })
                current['release_date'] = release_date

            if preorder_status is not None and preorder_status != current['preorder_status']:
                notifications.append({
                    'type': 'preorder',
                    'message': f"🎮 Pre-order Status Update: {game_name}\n"
                             f"Now {'available' if preorder_status else 'unavailable'} for pre-order!"
                })
                current['preorder_status'] = preorder_status

            if last_update is not None:
                current['last_update'] = last_update

            self.tracked_games[game_key]['last_check'] = datetime.now().isoformat()
            self._save_tracking_data()

            return notifications

        except Exception as e:
            log_command(logger, logging.ERROR,
                       f"Failed to update game data for {game_id}: {str(e)}",
                       command="update_game_data")
            return []

    def get_notification_channels(self, game_id: int) -> List[Dict]:
        """Get channels and users to notify for a game"""
        try:
            game_key = str(game_id)
            if game_key not in self.tracked_games:
                return []

            channels = []
            for channel_id, users in self.tracked_games[game_key]['watchers'].items():
                channels.append({
                    'channel_id': int(channel_id),
                    'users': users
                })
            return channels
        except Exception as e:
            log_command(logger, logging.ERROR,
                       f"Failed to get notification channels for {game_id}: {str(e)}",
                       command="get_notification_channels")
            return []