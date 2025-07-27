"""Configuration module for the kitchen cabinet system."""

from .constants import *
from .theme import DarkTheme, LightTheme, ThemeManager
from .settings import Settings, SettingsManager
from .paths import PathConfig
from .logging_config import setup_logging, get_logger

__all__ = [
    # Constants
    'APP_NAME',
    'APP_VERSION',
    'WINDOW_TITLE',
    'DEFAULT_WINDOW_SIZE',
    'DEFAULT_SHEET_WIDTH',
    'DEFAULT_SHEET_HEIGHT',
    # Theme
    'DarkTheme',
    'LightTheme',
    'ThemeManager',
    # Settings
    'Settings',
    'SettingsManager',
    # Paths
    'PathConfig',
    # Logging
    'setup_logging',
    'get_logger'
]


