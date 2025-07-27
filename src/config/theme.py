"""UI theme configuration."""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from tkinter import ttk
import json
from pathlib import Path


@dataclass
class ColorScheme:
    """Color scheme definition."""
    # Base colors
    bg_color: str
    fg_color: str
    accent_color: str

    # Component colors
    frame_bg: str
    button_bg: str
    button_active: str
    button_disabled: str

    # Table colors
    table_bg: str
    table_selected: str
    table_header: str
    table_alternate: str

    # Entry colors
    entry_bg: str
    entry_disabled: str
    entry_focus: str

    # Status colors
    error_color: str
    success_color: str
    warning_color: str
    info_color: str

    # Border colors
    border_color: str
    border_focus: str

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return {
            k: v for k, v in self.__dict__.items()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'ColorScheme':
        """Create from dictionary."""
        return cls(**data)


class DarkTheme:
    """Dark theme constants for the application UI."""

    # Base colors
    BG_COLOR = "#1E1E1E"
    FRAME_BG = "#2D2D2D"
    TEXT_COLOR = "#E0E0E0"
    ACCENT_COLOR = "#0E7FFF"

    # Component colors
    BUTTON_BG = "#3C3C3C"
    BUTTON_HOVER = "#4A4A4A"
    BUTTON_ACTIVE = "#525252"
    BUTTON_DISABLED = "#2A2A2A"

    # Table colors
    TABLE_BG = "#252525"
    TABLE_SELECTED = "#0E7FFF"
    TABLE_HEADER = "#333333"
    TABLE_ALTERNATE = "#2A2A2A"
    TABLE_HOVER = "#303030"

    # Entry colors
    ENTRY_BG = "#2D2D2D"
    ENTRY_DISABLED = "#252525"
    ENTRY_FOCUS = "#0E7FFF"

    # Status colors
    ERROR_COLOR = "#FF5252"
    SUCCESS_COLOR = "#4CAF50"
    WARNING_COLOR = "#FFC107"
    INFO_COLOR = "#2196F3"

    # Border colors
    BORDER_COLOR = "#3C3C3C"
    BORDER_FOCUS = "#0E7FFF"
    BORDER_ERROR = "#FF5252"

    # Special colors
    SHADOW_COLOR = "#000000"
    HIGHLIGHT_COLOR = "#FFFFFF"
    SELECTION_COLOR = "#0E7FFF33"  # 20% opacity

    @classmethod
    def get_color_scheme(cls) -> ColorScheme:
        """Get ColorScheme object."""
        return ColorScheme(
            bg_color=cls.BG_COLOR,
            fg_color=cls.TEXT_COLOR,
            accent_color=cls.ACCENT_COLOR,
            frame_bg=cls.FRAME_BG,
            button_bg=cls.BUTTON_BG,
            button_active=cls.BUTTON_ACTIVE,
            button_disabled=cls.BUTTON_DISABLED,
            table_bg=cls.TABLE_BG,
            table_selected=cls.TABLE_SELECTED,
            table_header=cls.TABLE_HEADER,
            table_alternate=cls.TABLE_ALTERNATE,
            entry_bg=cls.ENTRY_BG,
            entry_disabled=cls.ENTRY_DISABLED,
            entry_focus=cls.ENTRY_FOCUS,
            error_color=cls.ERROR_COLOR,
            success_color=cls.SUCCESS_COLOR,
            warning_color=cls.WARNING_COLOR,
            info_color=cls.INFO_COLOR,
            border_color=cls.BORDER_COLOR,
            border_focus=cls.BORDER_FOCUS
        )

    @classmethod
    def get_ttk_styles(cls) -> Dict[str, Any]:
        """Get TTK style configuration."""
        return {
            # Frame styles
            'TFrame': {
                'configure': {
                    'background': cls.FRAME_BG,
                    'borderwidth': 0
                }
            },

            # Label styles
            'TLabel': {
                'configure': {
                    'background': cls.FRAME_BG,
                    'foreground': cls.TEXT_COLOR
                }
            },
            'Title.TLabel': {
                'configure': {
                    'font': ('Segoe UI', 14, 'bold'),
                    'foreground': cls.TEXT_COLOR
                }
            },
            'Heading.TLabel': {
                'configure': {
                    'font': ('Segoe UI', 12, 'bold'),
                    'foreground': cls.ACCENT_COLOR
                }
            },
            'Error.TLabel': {
                'configure': {
                    'foreground': cls.ERROR_COLOR
                }
            },

            # Button styles
            'TButton': {
                'configure': {
                    'background': cls.BUTTON_BG,
                    'foreground': cls.TEXT_COLOR,
                    'borderwidth': 0,
                    'focuscolor': 'none',
                    'relief': 'flat',
                    'padding': (10, 5)
                },
                'map': {
                    'background': [
                        ('active', cls.BUTTON_ACTIVE),
                        ('pressed', cls.BUTTON_HOVER),
                        ('disabled', cls.BUTTON_DISABLED)
                    ],
                    'foreground': [
                        ('disabled', '#808080')
                    ]
                }
            },
            'Accent.TButton': {
                'configure': {
                    'background': cls.ACCENT_COLOR,
                    'foreground': '#FFFFFF'
                },
                'map': {
                    'background': [
                        ('active', '#1E88E5'),
                        ('pressed', '#1976D2'),
                        ('disabled', cls.BUTTON_DISABLED)
                    ]
                }
            },

            # Entry styles
            'TEntry': {
                'configure': {
                    'fieldbackground': cls.ENTRY_BG,
                    'foreground': cls.TEXT_COLOR,
                    'borderwidth': 1,
                    'relief': 'solid',
                    'insertcolor': cls.TEXT_COLOR
                },
                'map': {
                    'fieldbackground': [
                        ('disabled', cls.ENTRY_DISABLED),
                        ('focus', cls.ENTRY_BG)
                    ],
                    'bordercolor': [
                        ('focus', cls.BORDER_FOCUS)
                    ]
                }
            },

            # Combobox styles
            'TCombobox': {
                'configure': {
                    'fieldbackground': cls.ENTRY_BG,
                    'foreground': cls.TEXT_COLOR,
                    'background': cls.BUTTON_BG,
                    'borderwidth': 1,
                    'arrowcolor': cls.TEXT_COLOR
                },
                'map': {
                    'fieldbackground': [
                        ('readonly', cls.ENTRY_BG),
                        ('disabled', cls.ENTRY_DISABLED)
                    ],
                    'foreground': [
                        ('readonly', cls.TEXT_COLOR),
                        ('disabled', '#808080')
                    ],
                    'bordercolor': [
                        ('focus', cls.BORDER_FOCUS)
                    ]
                }
            },

            # Treeview styles
            'Treeview': {
                'configure': {
                    'background': cls.TABLE_BG,
                    'foreground': cls.TEXT_COLOR,
                    'fieldbackground': cls.TABLE_BG,
                    'borderwidth': 0,
                    'rowheight': 25
                },
                'map': {
                    'background': [
                        ('selected', cls.TABLE_SELECTED)
                    ],
                    'foreground': [
                        ('selected', '#FFFFFF')
                    ]
                }
            },
            'Treeview.Heading': {
                'configure': {
                    'background': cls.TABLE_HEADER,
                    'foreground': cls.TEXT_COLOR,
                    'borderwidth': 0,
                    'relief': 'flat'
                },
                'map': {
                    'background': [
                        ('active', cls.TABLE_SELECTED)
                    ]
                }
            },

            # Notebook styles
            'TNotebook': {
                'configure': {
                    'background': cls.FRAME_BG,
                    'borderwidth': 0,
                    'tabmargins': [0, 0, 0, 0]
                }
            },
            'TNotebook.Tab': {
                'configure': {
                    'background': cls.BUTTON_BG,
                    'foreground': cls.TEXT_COLOR,
                    'padding': [20, 10],
                    'borderwidth': 0
                },
                'map': {
                    'background': [
                        ('selected', cls.FRAME_BG),
                        ('active', cls.BUTTON_HOVER)
                    ],
                    'foreground': [
                        ('selected', cls.ACCENT_COLOR)
                    ]
                }
            },

            # Scrollbar styles
            'TScrollbar': {
                'configure': {
                    'background': cls.FRAME_BG,
                    'borderwidth': 0,
                    'arrowcolor': cls.TEXT_COLOR,
                    'troughcolor': cls.BG_COLOR,
                    'width': 12
                },
                'map': {
                    'background': [
                        ('active', cls.BUTTON_HOVER),
                        ('pressed', cls.BUTTON_ACTIVE)
                    ]
                }
            },

            # Progressbar styles
            'TProgressbar': {
                'configure': {
                    'background': cls.ACCENT_COLOR,
                    'troughcolor': cls.ENTRY_BG,
                    'borderwidth': 0,
                    'lightcolor': cls.ACCENT_COLOR,
                    'darkcolor': cls.ACCENT_COLOR
                }
            },

            # Checkbutton styles
            'TCheckbutton': {
                'configure': {
                    'background': cls.FRAME_BG,
                    'foreground': cls.TEXT_COLOR,
                    'focuscolor': 'none'
                },
                'map': {
                    'background': [
                        ('active', cls.FRAME_BG)
                    ]
                }
            },

            # Radiobutton styles
            'TRadiobutton': {
                'configure': {
                    'background': cls.FRAME_BG,
                    'foreground': cls.TEXT_COLOR,
                    'focuscolor': 'none'
                },
                'map': {
                    'background': [
                        ('active', cls.FRAME_BG)
                    ]
                }
            },

            # LabelFrame styles
            'TLabelframe': {
                'configure': {
                    'background': cls.FRAME_BG,
                    'foreground': cls.ACCENT_COLOR,
                    'borderwidth': 1,
                    'relief': 'solid'
                }
            },
            'TLabelframe.Label': {
                'configure': {
                    'background': cls.FRAME_BG,
                    'foreground': cls.ACCENT_COLOR,
                    'font': ('Segoe UI', 10, 'bold')
                }
            },

            # Separator styles
            'TSeparator': {
                'configure': {
                    'background': cls.BORDER_COLOR
                }
            },

            # PanedWindow styles
            'TPanedwindow': {
                'configure': {
                    'background': cls.FRAME_BG
                }
            },
            'Sash': {
                'configure': {
                    'sashthickness': 4,
                    'sashrelief': 'flat',
                    'background': cls.BORDER_COLOR
                }
            }
        }

    @classmethod
    def apply_theme(cls, style: ttk.Style) -> None:
        """Apply the dark theme to a ttk.Style object."""
        style.theme_use('clam')  # Base theme

        styles = cls.get_ttk_styles()
        for widget_class, config in styles.items():
            if 'configure' in config:
                style.configure(widget_class, **config['configure'])
            if 'map' in config:
                style.map(widget_class, **config['map'])

        # Configure specific layouts
        style.layout('Treeview', [
            ('Treeview.treearea', {'sticky': 'nswe'})
        ])


class LightTheme:
    """Light theme constants (alternative theme)."""

    # Base colors
    BG_COLOR = "#FFFFFF"
    FRAME_BG = "#F5F5F5"
    TEXT_COLOR = "#212121"
    ACCENT_COLOR = "#1976D2"

    # Component colors
    BUTTON_BG = "#E0E0E0"
    BUTTON_HOVER = "#D5D5D5"
    BUTTON_ACTIVE = "#CCCCCC"
    BUTTON_DISABLED = "#F0F0F0"

    # Table colors
    TABLE_BG = "#FFFFFF"
    TABLE_SELECTED = "#1976D2"
    TABLE_HEADER = "#EEEEEE"
    TABLE_ALTERNATE = "#FAFAFA"
    TABLE_HOVER = "#F5F5F5"

    # Entry colors
    ENTRY_BG = "#FFFFFF"
    ENTRY_DISABLED = "#F5F5F5"
    ENTRY_FOCUS = "#1976D2"

    # Status colors
    ERROR_COLOR = "#D32F2F"
    SUCCESS_COLOR = "#388E3C"
    WARNING_COLOR = "#F57C00"
    INFO_COLOR = "#1976D2"

    # Border colors
    BORDER_COLOR = "#E0E0E0"
    BORDER_FOCUS = "#1976D2"
    BORDER_ERROR = "#D32F2F"

    @classmethod
    def get_color_scheme(cls) -> ColorScheme:
        """Get ColorScheme object."""
        return ColorScheme(
            bg_color=cls.BG_COLOR,
            fg_color=cls.TEXT_COLOR,
            accent_color=cls.ACCENT_COLOR,
            frame_bg=cls.FRAME_BG,
            button_bg=cls.BUTTON_BG,
            button_active=cls.BUTTON_ACTIVE,
            button_disabled=cls.BUTTON_DISABLED,
            table_bg=cls.TABLE_BG,
            table_selected=cls.TABLE_SELECTED,
            table_header=cls.TABLE_HEADER,
            table_alternate=cls.TABLE_ALTERNATE,
            entry_bg=cls.ENTRY_BG,
            entry_disabled=cls.ENTRY_DISABLED,
            entry_focus=cls.ENTRY_FOCUS,
            error_color=cls.ERROR_COLOR,
            success_color=cls.SUCCESS_COLOR,
            warning_color=cls.WARNING_COLOR,
            info_color=cls.INFO_COLOR,
            border_color=cls.BORDER_COLOR,
            border_focus=cls.BORDER_FOCUS
        )

    @classmethod
    def apply_theme(cls, style: ttk.Style) -> None:
        """Apply the light theme."""
        # Similar to DarkTheme but with light colors
        pass


class ThemeManager:
    """Manages application themes."""

    THEMES = {
        'dark': DarkTheme,
        'light': LightTheme
    }

    CUSTOM_THEMES_FILE = Path.home() / ".proper_job" / "custom_themes.json"

    def __init__(self):
        """Initialize theme manager."""
        self.current_theme = 'dark'
        self.custom_themes: Dict[str, ColorScheme] = {}
        self._load_custom_themes()

    def _load_custom_themes(self) -> None:
        """Load custom themes from file."""
        if self.CUSTOM_THEMES_FILE.exists():
            try:
                with open(self.CUSTOM_THEMES_FILE, 'r') as f:
                    data = json.load(f)
                    for name, theme_data in data.items():
                        self.custom_themes[name] = ColorScheme.from_dict(theme_data)
            except Exception:
                pass

    def save_custom_themes(self) -> None:
        """Save custom themes to file."""
        self.CUSTOM_THEMES_FILE.parent.mkdir(parents=True, exist_ok=True)

        data = {
            name: theme.to_dict()
            for name, theme in self.custom_themes.items()
        }

        with open(self.CUSTOM_THEMES_FILE, 'w') as f:
            json.dump(data, f, indent=2)

    def get_theme(self, theme_name: str) -> type:
        """Get a theme class by name."""
        if theme_name in self.custom_themes:
            return self._create_theme_class(self.custom_themes[theme_name])
        return self.THEMES.get(theme_name, DarkTheme)

    def _create_theme_class(self, color_scheme: ColorScheme) -> type:
        """Create a theme class from a color scheme."""

        # Dynamic class creation for custom themes
        class CustomTheme:
            pass

        # Set all color attributes
        for key, value in color_scheme.to_dict().items():
            setattr(CustomTheme, key.upper(), value)

        return CustomTheme

    def apply_theme(
            self,
            style: ttk.Style,
            theme_name: Optional[str] = None
    ) -> None:
        """Apply a theme to the application."""
        if theme_name:
            self.current_theme = theme_name

        theme = self.get_theme(self.current_theme)
        if hasattr(theme, 'apply_theme'):
            theme.apply_theme(style)

    def get_available_themes(self) -> List[str]:
        """Get list of available theme names."""
        return list(self.THEMES.keys()) + list(self.custom_themes.keys())

    def add_custom_theme(self, name: str, color_scheme: ColorScheme) -> None:
        """Add a custom theme."""
        self.custom_themes[name] = color_scheme
        self.save_custom_themes()

    def remove_custom_theme(self, name: str) -> bool:
        """Remove a custom theme."""
        if name in self.custom_themes:
            del self.custom_themes[name]
            self.save_custom_themes()
            return True
        return False
