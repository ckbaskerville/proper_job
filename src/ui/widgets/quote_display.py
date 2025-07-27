"""Quote display widget."""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional

from src.config import DarkTheme


class QuoteDisplayWidget(ttk.Frame):
    """Widget for displaying quote summary."""

    def __init__(self, parent: tk.Widget):
        """Initialize quote display widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create the widget layout."""
        # Main frame with border
        self.configure(relief=tk.RIDGE, borderwidth=1)

        # Title
        title_label = ttk.Label(
            self,
            text="Quote Summary",
            font=('Arial', 12, 'bold')
        )
        title_label.grid(row=0, column=0, columnspan=4, pady=5)

        # Summary fields
        self._create_field("Units:", 1, 0)
        self.units_label = self._create_value("--", 1, 1)

        self._create_field("Sheets Required:", 1, 2)
        self.sheets_label = self._create_value("--", 1, 3)

        self._create_field("Material Cost:", 2, 0)
        self.material_cost_label = self._create_value("--", 2, 1)

        self._create_field("Labor Hours:", 2, 2)
        self.labor_hours_label = self._create_value("--", 2, 3)

        self._create_field("Labor Cost:", 3, 0)
        self.labor_cost_label = self._create_value("--", 3, 1)

        self._create_field("Subtotal:", 3, 2)
        self.subtotal_label = self._create_value("--", 3, 3)

        self._create_field("Markup:", 4, 0)
        self.markup_label = self._create_value("--", 4, 1)

        # Total (larger font)
        total_field = ttk.Label(
            self,
            text="TOTAL:",
            font=('Arial', 11, 'bold')
        )
        total_field.grid(row=4, column=2, sticky="e", padx=5, pady=5)

        self.total_label = ttk.Label(
            self,
            text="--",
            font=('Arial', 11, 'bold'),
            foreground=DarkTheme.ACCENT_COLOR
        )
        self.total_label.grid(row=4, column=3, sticky="w", padx=5, pady=5)

        # Configure grid weights
        for i in range(4):
            self.columnconfigure(i, weight=1)

    def _create_field(self, text: str, row: int, col: int) -> ttk.Label:
        """Create a field label.

        Args:
            text: Field text
            row: Grid row
            col: Grid column

        Returns:
            Created label
        """
        label = ttk.Label(self, text=text)
        label.grid(row=row, column=col, sticky="e", padx=5, pady=2)
        return label

    def _create_value(self, text: str, row: int, col: int) -> ttk.Label:
        """Create a value label.

        Args:
            text: Value text
            row: Grid row
            col: Grid column

        Returns:
            Created label
        """
        label = ttk.Label(self, text=text, font=('Arial', 10, 'bold'))
        label.grid(row=row, column=col, sticky="w", padx=5, pady=2)
        return label

    def display_quote(
            self,
            quote: Dict[str, Any],
            markup_percentage: float,
            currency_symbol: str = "£"
    ) -> None:
        """Display quote information.

        Args:
            quote: Quote data
            markup_percentage: Markup percentage
            currency_symbol: Currency symbol
        """

        # Format currency
        def format_currency(value: float) -> str:
            return f"{currency_symbol}{value:,.2f}"

        # Update labels
        self.units_label.config(text=str(quote['units']))
        self.sheets_label.config(text=str(quote['total_sheets_required']))
        self.material_cost_label.config(
            text=format_currency(quote['material_cost'])
        )
        self.labor_hours_label.config(
            text=f"{quote['labor_hours']:.1f} hrs"
        )
        self.labor_cost_label.config(
            text=format_currency(quote['labor_cost'])
        )
        self.subtotal_label.config(
            text=format_currency(quote['subtotal'])
        )
        self.markup_label.config(
            text=f"{format_currency(quote['markup'])} ({markup_percentage:.0f}%)"
        )
        self.total_label.config(
            text=format_currency(quote['total'])
        )

    def clear(self) -> None:
        """Clear the quote display."""
        self.units_label.config(text="--")
        self.sheets_label.config(text="--")
        self.material_cost_label.config(text="--")
        self.labor_hours_label.config(text="--")
        self.labor_cost_label.config(text="--")
        self.subtotal_label.config(text="--")
        self.markup_label.config(text="--")
        self.total_label.config(text="--")
