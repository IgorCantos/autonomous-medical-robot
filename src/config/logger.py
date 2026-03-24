import logging
import sys
from pathlib import Path

# Create logs directory
logs_dir = Path(__file__).parent.parent.parent / 'logs'
logs_dir.mkdir(parents=True, exist_ok=True)

# Configure logger
logger = logging.getLogger('medical-assistant')
logger.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_format = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(console_format)

# File handler
file_handler = logging.FileHandler(logs_dir / 'app.log')
file_handler.setLevel(logging.INFO)
file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_format)

# Add handlers
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Convenience methods
def info(msg, extra=None):
    logger.info(msg, extra=extra)

def error(msg, extra=None):
    logger.error(msg, extra=extra)

def warn(msg, extra=None):
    logger.warning(msg, extra=extra)

def debug(msg, extra=None):
    logger.debug(msg, extra=extra)
