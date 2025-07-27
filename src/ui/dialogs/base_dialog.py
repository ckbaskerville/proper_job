"""Base dialog class for consistent dialog behavior."""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Any

from src.config.theme import DarkTheme


class BaseDialog:
    """Base class for application dialogs."""

    def __init__(
            self,
            parent: tk.Widget,
            title: str,
            width: int = 600,
            height: int = 400
    ):
        """Initialize the base dialog.

        Args:
            parent: Parent widget
            title: Dialog window title
            width: Dialog width in pixels
            height: Dialog height in pixels
        """
        self.parent = parent
        self.result: Optional[Any] = None

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry(f"{width}x{height}")
        self.dialog.configure(bg=DarkTheme.BG_COLOR)

        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Handle window close
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # Center dialog on parent
        self._center_on_parent()

        # Create main content
        self._create_content()

    def _center_on_parent(self) -> None:
        """Center the dialog on its parent window."""
        self.dialog.update_idletasks()

        # Get parent position and size
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        # Get dialog size
        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()

        # Calculate center position
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2

        # Set position
        self.dialog.geometry(f"+{x}+{y}")

    def _create_content(self) -> None:
        """Create the dialog content. Override in subclasses."""
        # Main container
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Content area
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        self._create_body(content_frame)

        # Button bar
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        self._create_buttons(button_frame)

    def _create_body(self, parent: ttk.Frame) -> None:
        """Create the main body of the dialog. Override in subclasses."""
        pass

    def _create_buttons(self, parent: ttk.Frame) -> None:
        """Create the dialog buttons."""
        # Cancel button
        ttk.Button(
            parent,
            text="Cancel",
            command=self._on_cancel
        ).pack(side=tk.RIGHT, padx=(5, 0))

        # OK button
        ttk.Button(
            parent,
            text="OK",
            command=self._on_ok
        ).pack(side=tk.RIGHT)

    def _on_ok(self) -> None:
        """Handle OK button click. Override to add validation."""
        self.result = self._get_result()
        self.dialog.destroy()

    def _on_cancel(self) -> None:
        """Handle Cancel button click."""
        self.result = None
        self.dialog.destroy()

    def _get_result(self) -> Any:
        """Get the dialog result. Override in subclasses."""
        return None

    def show(self) -> Any:
        """Show the dialog and wait for result.

        Returns:
            The dialog result or None if cancelled
        """
        self.dialog.wait_window()
        return self.result


class ValidationMixin:
    """Mixin for dialogs that need input validation."""

    def _validate_required(
            self,
            value: str,
            field_name: str
    ) -> Optional[str]:
        """Validate that a field is not empty.

        Args:
            value: Field value to validate
            field_name: Name of field for error message

        Returns:
            Error message if invalid, None if valid
        """
        if not value or not value.strip():
            return f"{field_name} is required"
        return None

    def _validate_positive_number(
            self,
            value: Any,
            field_name: str
    ) -> Optional[str]:
        """Validate that a value is a positive number.

        Args:
            value: Value to validate
            field_name: Name of field for error message

        Returns:
            Error message if invalid, None if valid
        """
        try:
            num = float(value)
            if num <= 0:
                return f"{field_name} must be greater than 0"
        except (ValueError, TypeError):
            return f"{field_name} must be a valid number"
        return None

    def _validate_non_negative_number(
            self,
            value: Any,
            field_name: str
    ) -> Optional[str]:
        """Validate that a value is a non-negative number.

        Args:
            value: Value to validate
            field_name: Name of field for error message

        Returns:
            Error message if invalid, None if valid
        """
        try:
            num = float(value)
            if num < 0:
                return f"{field_name} cannot be negative"
        except (ValueError, TypeError):
            return f"{field_name} must be a valid number"
        return None

    def _show_validation_error(self, message: str) -> None:
        """Show a validation error message."""
        from tkinter import messagebox
        messagebox.showerror("Validation Error", message)