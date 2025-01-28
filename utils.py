import logging
import os
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama for Windows support
init()

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors and detailed information"""
    
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT
    }
    
    def format(self, record):
        # Add colors to level names in console output
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{Style.RESET_ALL}"
            
        # Add user and command info if available
        if hasattr(record, 'user'):
            record.user_info = f" | User: {record.user}"
        else:
            record.user_info = ""
            
        if hasattr(record, 'command'):
            record.command_info = f" | Command: {record.command}"
        else:
            record.command_info = ""
            
        return super().format(record)

def setup_logging():
    """Set up logging with both file and console output"""
    
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
        
    # Create logger
    logger = logging.getLogger('steam_bot')
    logger.setLevel(logging.DEBUG)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler with colors
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = ColoredFormatter(
        '%(asctime)s | %(levelname)s%(user_info)s%(command_info)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    
    # File handler with detailed information
    today = datetime.now().strftime('%Y-%m-%d')
    file_handler = logging.FileHandler(f'logs/steam_bot_{today}.log')
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | User: %(user)s | Command: %(command)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# Create a function to add context to log records
def log_command(logger, level, message, user=None, command=None):
    """Log with additional context for Discord commands"""
    extra = {
        'user': user if user else 'System',
        'command': command if command else 'None'
    }
    logger.log(level, message, extra=extra)