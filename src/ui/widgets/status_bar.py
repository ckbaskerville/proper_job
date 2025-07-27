"""Status bar widget."""

import tkinter as tk
from tkinter import ttk
from datetime import datetime

from src.config import DarkTheme


class StatusBar(ttk.Frame):
    """Application status bar."""

    def __init__(self, parent: tk.Widget):
        """Initialize status bar.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        self._create_widgets()
        self._update_time()

    def _create_widgets(self) -> None:
        """Create status bar widgets."""
        # Configure style
        self.configure(relief=tk.SUNKEN, borderwidth=1)

        # Status message
        self.status_label = ttk.Label(
            self,
            text="Ready",
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Separator
        ttk.Separator(self, orient=tk.VERTICAL).pack(
            side=tk.LEFT, fill=tk.Y, padx=5
        )

        # Project info
        self.project_label = ttk.Label(
            self,
            text="0 units",
            anchor=tk.W
        )
        self.project_label.pack(side=tk.LEFT, padx=5)

        # Modified indicator
        self.modified_label = ttk.Label(
            self,
            text="",
            foreground=DarkTheme.WARNING_COLOR
        )
        self.modified_label.pack(side=tk.LEFT, padx=5)

        # Separator
        ttk.Separator(self, orient=tk.VERTICAL).pack(
            side=tk.LEFT, fill=tk.Y, padx=5
        )

        # Time
        self.time_label = ttk.Label(
            self,
            text="",
            anchor=tk.E
        )
        self.time_label.pack(side=tk.RIGHT, padx=5)

    def _update_time(self) -> None:
        """Update time display."""
        current_time = datetime.now().strftime("%H:%M")
        self.time_label.config(text=current_time)

        # Schedule next update
        self.after(60000, self._update_time)  # Update every minute

    def set_status(self, message: str) -> None:
        """Set status message.

        Args:
            message: Status message
        """
        self.status_label.config(text=message)

    def set_project_info(self, units: int, modified: bool = False) -> None:
        """Set project information.

        Args:
            units: Number of units
            modified: Whether project is modified
        """
        self.project_label.config(text=f"{units} units")
        self.modified_label.config(text="Modified" if modified else "")