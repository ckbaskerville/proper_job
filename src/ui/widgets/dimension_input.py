"""Dimension input widget."""

import tkinter as tk
from tkinter import ttk
from typing import Optional

from src.config.constants import MIN_DIMENSION, MAX_DIMENSION
from src.utils.validators import Validator, ValidationError


class DimensionInput(ttk.Frame):
    """Widget for entering dimensions with validation."""

    def __init__(
            self,
            parent: tk.Widget,
            label: str = "",
            default_value: float = 0.0,
            min_value: float = MIN_DIMENSION,
            max_value: float = MAX_DIMENSION
    ):
        """Initialize dimension input.

        Args:
            parent: Parent widget
            label: Label text
            default_value: Default value
            min_value: Minimum allowed value
            max_value: Maximum allowed value
        """
        super().__init__(parent)

        self.min_value = min_value
        self.max_value = max_value

        self._create_widgets(label, default_value)

    def _create_widgets(self, label: str, default_value: float) -> None:
        """Create input widgets."""
        if label:
            ttk.Label(self, text=label).pack(side=tk.LEFT, padx=(0, 2))

        # Create validated entry
        self.var = tk.DoubleVar(value=default_value)

        vcmd = (self.register(self._validate), '%P')
        self.entry = ttk.Entry(
            self,
            textvariable=self.var,
            width=8,
            validate='focusout',
            validatecommand=vcmd,
            state='normal'
        )
        self.entry.pack(side=tk.LEFT)

    def _validate(self, value: str) -> bool:
        """Validate input value."""
        if value == "":
            return True

        try:
            num = float(value)
            return self.min_value <= num <= self.max_value
        except ValueError:
            return False

    def get(self) -> float:
        """Get the dimension value.

        Returns:
            Dimension value

        Raises:
            ValidationError: If value is invalid
        """
        try:
            value = self.var.get()
            if not self.min_value <= value <= self.max_value:
                raise ValidationError(
                    f"Value must be between {self.min_value} and {self.max_value}"
                )
            return value
        except tk.TclError:
            raise ValidationError("Invalid dimension value")

    def set(self, value: float) -> None:
        """Set the dimension value.

        Args:
            value: Value to set
        """
        self.var.set(value)

    def focus(self) -> None:
        """Set focus to entry."""
        self.entry.focus_set()