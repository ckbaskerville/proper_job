"""Application toolbar."""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable

from src.config import DarkTheme


class ToolBar(ttk.Frame):
    """Main application toolbar."""

    def __init__(
            self,
            parent: tk.Widget,
            on_new: Optional[Callable[[], None]] = None,
            on_open: Optional[Callable[[], None]] = None,
            on_save: Optional[Callable[[], bool]] = None,
            on_add_unit: Optional[Callable[[], None]] = None,
            on_edit_unit: Optional[Callable[[], None]] = None,
            on_duplicate_unit: Optional[Callable[[], None]] = None,
            on_remove_unit: Optional[Callable[[], None]] = None,
            on_settings: Optional[Callable[[], None]] = None,
            on_materials_settings: Optional[Callable[[], None]] = None,
            on_runners_settings: Optional[Callable[[], None]] = None,
            on_labor_settings: Optional[Callable[[], None]] = None
    ):
        """Initialize toolbar.

        Args:
            parent: Parent widget
            on_new: New project callback
            on_open: Open project callback
            on_save: Save project callback
            on_add_unit: Add unit callback
            on_calculate: Calculate quote callback
            on_settings: Settings callback
        """
        super().__init__(parent)

        self.on_new = on_new
        self.on_open = on_open
        self.on_save = on_save
        self.on_add_unit = on_add_unit
        self.on_edit_unit = on_edit_unit
        self.on_duplicate_unit = on_duplicate_unit
        self.on_remove_unit = on_remove_unit
        self.on_settings = on_settings
        self.on_materials_settings = on_materials_settings
        self.on_runners_settings = on_runners_settings
        self.on_labor_settings = on_labor_settings

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create toolbar widgets."""
        # File section
        file_frame = ttk.Frame(self, padding=5)
        file_frame.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            file_frame,
            text="New",
            command=self.on_new,
            width=8
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            file_frame,
            text="Open",
            command=self.on_open,
            width=8
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            file_frame,
            text="Save",
            command=self.on_save,
            width=8
        ).pack(side=tk.LEFT, padx=2)

        # # Edit section
        # edit_frame = ttk.Frame(self, padding=5)
        # edit_frame.pack(side=tk.LEFT, padx=5)
        #
        # ttk.Button(
        #     edit_frame,
        #     text="Add Cabinet",
        #     command=self.on_add_unit,
        #     width=12
        # ).pack(side=tk.LEFT, padx=2)
        #
        # ttk.Button(
        #     edit_frame,
        #     text="Edit",
        #     command=self.on_edit_unit,
        #     width=12
        # ).pack(side=tk.LEFT, padx=2)
        #
        # ttk.Button(
        #     edit_frame,
        #     text="Duplicate",
        #     command=self.on_duplicate_unit,
        #     width=12
        # ).pack(side=tk.LEFT, padx=2)
        #
        # ttk.Button(
        #     edit_frame,
        #     text="Remove",
        #     command=self.on_remove_unit,
        #     width=12
        # ).pack(side=tk.LEFT, padx=2)

        # # Tools section
        # tools_frame = ttk.LabelFrame(self, text="Tools", padding=5)
        # tools_frame.pack(side=tk.LEFT, padx=5)
        #
        # ttk.Button(
        #     tools_frame,
        #     text="Calculate Quote",
        #     command=self.on_calculate,
        #     width=15
        # ).pack(side=tk.LEFT, padx=2)

        # Settings button (right side)
        ttk.Button(
            self,
            text="Materials",
            command=self.on_materials_settings,
            width=10
        ).pack(side=tk.RIGHT, padx=5)
        ttk.Button(
            self,
            text="Drawer Runners",
            command=self.on_runners_settings,
            width=15
        ).pack(side=tk.RIGHT, padx=5)
        ttk.Button(
            self,
            text="Labour Settings",
            command=self.on_labor_settings,
            width=17
        ).pack(side=tk.RIGHT, padx=5)

    def set_edit_enabled(self, enabled: bool) -> None:
        """Enable/disable edit buttons.

        Args:
            enabled: Whether to enable edit buttons
        """
        # This would enable/disable edit-related buttons
        # For now, we don't have direct references to them
        pass