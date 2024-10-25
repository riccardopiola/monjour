# log.py
import logging

# Create a logger object
logger = logging.getLogger(__name__)

# Set the default log level (INFO)
logger.setLevel(logging.INFO)

# Create a console handler
console_handler = logging.StreamHandler()

# Create a formatter and set it for the handler
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(console_handler)

# Define helper functions for different logging levels
def info(message):
    logger.info(message)

def debug(message):
    logger.debug(message)

def warning(message):
    logger.warning(message)

def error(message):
    logger.error(message)

def critical(message):
    logger.critical(message)
