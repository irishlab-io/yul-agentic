# Config module
# This makes src/config a proper Python package
# Re-export everything from config.py for backward compatibility

from .config import *  # noqa: F401, F403
