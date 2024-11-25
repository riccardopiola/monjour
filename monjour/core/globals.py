import os

MONJOUR_VERSION = '0.1'

MONJOUR_DEBUG: str|None = os.environ.get('MONJOUR_DEBUG', None)

MONJOUR_LOG_LEVEL = os.environ.get('MONJOUR_LOG_LEVEL', 'INFO')