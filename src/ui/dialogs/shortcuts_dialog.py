"""Keyboard shortcuts dialog."""

import tkinter as tk
from tkinter import ttk

from ..base import BaseDialog


class ShortcutsDialog(BaseDialog):
    """Dialog displaying keyboard shortcuts."""

    def __init__(self, parent: tk.Widget):
        """Initialize shortcuts dialog.

        Args:
            parent: Parent widget
        """
        super().__init__(parent, "Keyboard Shortcuts", width=600, height=500)

    def _create_body(self, parent: ttk.Frame) -> None:
        """Create dialog body."""
        # Create scrollable text widget
        text_frame = ttk.Frame(parent)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=('Consolas', 10),
            height=20,
            width=60
        )
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(text_frame, command=self.text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text.configure(yscrollcommand=scrollbar.set)

        # Add shortcuts
        self._add_shortcuts()

        # Make text read-only
        self.text.configure(state='disabled')

    def _add_shortcuts(self) -> None:
        """Add shortcut information to text widget."""
        shortcuts = [
            ("FILE OPERATIONS", [
                ("Ctrl+N", "New Project"),
                ("Ctrl+O", "Open Project"),
                ("Ctrl+S", "Save Project"),
                ("Ctrl+Shift+S", "Save Project As"),
                ("Ctrl+E", "Export"),
                ("Alt+F4", "Exit Application")
            ]),

            ("CABINET OPERATIONS", [
                ("Ctrl+A", "Add Cabinet"),
                ("F2", "Edit Selected Cabinet"),
                ("Ctrl+D", "Duplicate Cabinet"),
                ("Delete", "Remove Cabinet"),
                ("Enter", "Edit Cabinet (when selected)")
            ]),

            ("VIEW OPERATIONS", [
                ("F5", "Show Cut List"),
                ("F6", "Show Unit Breakdown"),
                ("F7", "Show Visualization"),
                ("F9", "Calculate Quote")
            ]),

            ("NAVIGATION", [
                ("Tab", "Next Field"),
                ("Shift+Tab", "Previous Field"),
                ("↑/↓", "Navigate Table Rows"),
                ("Space", "Toggle Checkbox"),
                ("Esc", "Cancel Dialog")
            ]),

            ("HELP", [
                ("F1", "Show Help"),
                ("Ctrl+?", "Show Shortcuts")
            ])
        ]

        for category, items in shortcuts:
            # Category header
            self.text.insert(tk.END, f"\n{category}\n", 'category')
            self.text.insert(tk.END, "-" * 40 + "\n", 'separator')

            # Shortcuts
            for key, description in items:
                self.text.insert(tk.END, f"  {key:<20} {description}\n", 'shortcut')

        # Configure tags
        self.text.tag_configure('category', font=('Consolas', 12, 'bold'))
        self.text.tag_configure('separator', foreground='gray')
        self.text.tag_configure('shortcut', font=('Consolas', 10))

    def _create_buttons(self, parent: ttk.Frame) -> None:
        """Create dialog buttons."""
        ttk.Button(
            parent,
            text="Close",
            command=self.dialog.destroy,
            width=15
        ).pack()