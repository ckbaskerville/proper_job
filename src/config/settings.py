"""Application settings management."""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime

from .constants import (
    SETTINGS_FILE,
    DEFAULT_SHEET_WIDTH,
    DEFAULT_SHEET_HEIGHT,
    DEFAULT_LABOR_RATE,
    DEFAULT_MARKUP_PERCENTAGE
)


@dataclass
class Settings:
    """Application settings."""

    # Display preferences
    theme: str = 'dark'
    font_size: int = 10
    show_tooltips: bool = True
    show_grid: bool = True

    # Units and formatting
    units: str = 'metric'  # 'metric' or 'imperial'
    currency_symbol: str = '£'
    decimal_places: int = 2

    # Default values
    default_sheet_width: float = DEFAULT_SHEET_WIDTH
    default_sheet_height: float = DEFAULT_SHEET_HEIGHT
    default_labor_rate: float = DEFAULT_LABOR_RATE
    default_markup: float = DEFAULT_MARKUP_PERCENTAGE
    default_material: str = 'Laminate'
    default_thickness: float = 18.0

    # Behavior
    autosave_enabled: bool = True
    autosave_interval: int = 300  # seconds
    confirm_delete: bool = True
    check_updates: bool = True

    # Window state
    window_maximized: bool = False
    window_width: int = 1200
    window_height: int = 800
    window_x: Optional[int] = None
    window_y: Optional[int] = None

    # Recent files
    recent_files: List[str] = field(default_factory=list)
    max_recent_files: int = 10

    # Advanced
    enable_optimization_cache: bool = True
    max_undo_levels: int = 50
    export_quality: str = 'high'  # 'low', 'medium', 'high'

    # User preferences
    last_save_directory: Optional[str] = None
    last_export_directory: Optional[str] = None
    preferred_export_format: str = 'pdf'

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            # Display
            'theme': self.theme,
            'font_size': self.font_size,
            'show_tooltips': self.show_tooltips,
            'show_grid': self.show_grid,

            # Units
            'units': self.units,
            'currency_symbol': self.currency_symbol,
            'decimal_places': self.decimal_places,

            # Defaults
            'default_sheet_width': self.default_sheet_width,
            'default_sheet_height': self.default_sheet_height,
            'default_labor_rate': self.default_labor_rate,
            'default_markup': self.default_markup,
            'default_material': self.default_material,
            'default_thickness': self.default_thickness,

            # Behavior
            'autosave_enabled': self.autosave_enabled,
            'autosave_interval': self.autosave_interval,
            'confirm_delete': self.confirm_delete,
            'check_updates': self.check_updates,

            # Window
            'window_maximized': self.window_maximized,
            'window_width': self.window_width,
            'window_height': self.window_height,
            'window_x': self.window_x,
            'window_y': self.window_y,

            # Recent files
            'recent_files': self.recent_files,
            'max_recent_files': self.max_recent_files,

            # Advanced
            'enable_optimization_cache': self.enable_optimization_cache,
            'max_undo_levels': self.max_undo_levels,
            'export_quality': self.export_quality,

            # User preferences
            'last_save_directory': self.last_save_directory,
            'last_export_directory': self.last_export_directory,
            'preferred_export_format': self.preferred_export_format
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Settings':
        """Create settings from dictionary."""
        return cls(**{
            k: v for k, v in data.items()
            if k in cls.__dataclass_fields__
        })

    def add_recent_file(self, filepath: str) -> None:
        """Add a file to recent files list."""
        # Remove if already exists
        if filepath in self.recent_files:
            self.recent_files.remove(filepath)

        # Add to beginning
        self.recent_files.insert(0, filepath)

        # Trim to max length
        self.recent_files = self.recent_files[:self.max_recent_files]

    def clear_recent_files(self) -> None:
        """Clear recent files list."""
        self.recent_files.clear()

    def update_window_state(
            self,
            maximized: bool,
            width: int,
            height: int,
            x: Optional[int] = None,
            y: Optional[int] = None
    ) -> None:
        """Update window state."""
        self.window_maximized = maximized
        if not maximized:
            self.window_width = width
            self.window_height = height
            self.window_x = x
            self.window_y = y


class SettingsManager:
    """Manages application settings persistence."""

    def __init__(self, settings_file: Optional[Path] = None):
        """Initialize settings manager.

        Args:
            settings_file: Custom settings file path
        """
        self.settings_file = settings_file or SETTINGS_FILE
        self.settings = self._load_settings()
        self._observers = []

    def _load_settings(self) -> Settings:
        """Load settings from file."""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return Settings.from_dict(data)
            except Exception as e:
                print(f"Error loading settings: {e}")

        return Settings()

    def save_settings(self) -> None:
        """Save settings to file."""
        # Ensure directory exists
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings.to_dict(), f, indent=2)
            self._notify_observers('settings_saved')
        except Exception as e:
            print(f"Error saving settings: {e}")

    def reset_to_defaults(self) -> None:
        """Reset all settings to defaults."""
        self.settings = Settings()
        self.save_settings()
        self._notify_observers('settings_reset')

    def update_setting(self, key: str, value: Any) -> None:
        """Update a single setting."""
        if hasattr(self.settings, key):
            setattr(self.settings, key, value)
            self.save_settings()
            self._notify_observers('setting_changed', key=key, value=value)

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return getattr(self.settings, key, default)

    def add_observer(self, callback) -> None:
        """Add a settings change observer."""
        self._observers.append(callback)

    def remove_observer(self, callback) -> None:
        """Remove a settings change observer."""
        if callback in self._observers:
            self._observers.remove(callback)

    def _notify_observers(self, event: str, **kwargs) -> None:
        """Notify observers of settings changes."""
        for observer in self._observers:
            try:
                observer(event, **kwargs)
            except Exception as e:
                print(f"Error notifying observer: {e}")

    def export_settings(self, filepath: Path) -> None:
        """Export settings to file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.settings.to_dict(), f, indent=2)

    def import_settings(self, filepath: Path) -> None:
        """Import settings from file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.settings = Settings.from_dict(data)
            self.save_settings()
            self._notify_observers('settings_imported')
        except Exception as e:
            raise ValueError(f"Failed to import settings: {e}")