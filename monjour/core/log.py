# log.py
import logging
import colorama
import monjour.core.globals as mj_globals

# Initialize colorama
colorama.init()

# Define a custom formatter
class ColorFormatter(logging.Formatter):
    # Define colors for each level
    LEVEL_COLORS = {
        'DEBUG': colorama.Fore.GREEN,
        'INFO': colorama.Fore.BLUE,
        'WARNING': colorama.Fore.YELLOW,
        'ERROR': colorama.Fore.RED,
        'CRITICAL': colorama.Back.RED + colorama.Fore.WHITE,
    }

    def format(self, record):
        # Get the original log message
        original_format = super().format(record)

        # Apply color to the levelname only
        level_color = self.LEVEL_COLORS.get(record.levelname, '')
        reset_color = colorama.Style.RESET_ALL
        record.levelname = f"{level_color}{record.levelname}{reset_color}"  # Colorize the levelname

        # Reformat with the modified levelname
        return super().format(record)

# Create logger
logger = logging.getLogger('ColoredLogger')
handler = logging.StreamHandler()

# Apply formatter
COLOR_FORMATTER = ColorFormatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')

CONSOLE_HANDLER = logging.StreamHandler()
CONSOLE_HANDLER.setFormatter(COLOR_FORMATTER)

class MjLogger(logging.Logger):
    def __init__(self, name: str):
        if ':' in name:
            raise ValueError("Logger name cannot contain ':'")
        super().__init__(name)
        self.addHandler(CONSOLE_HANDLER)
        if mj_globals.MONJOUR_DEBUG:
            self.setLevel(logging.DEBUG)
        else:
            self.setLevel(logging.INFO)

DEFAULT_LOGGER = MjLogger('monjour')

# Define helper functions for different logging levels
info = DEFAULT_LOGGER.info
debug = DEFAULT_LOGGER.debug
warning = DEFAULT_LOGGER.warning
error = DEFAULT_LOGGER.error
