"""Base classes for UI components."""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, Any
from abc import ABC, abstractmethod


class BaseWidget(ABC):
    """Abstract base class for custom widgets."""

    def __init__(self, parent: tk.Widget):
        """Initialize base widget.

        Args:
            parent: Parent widget
        """
        self.parent = parent
        self._create_widget()
        self._setup_widget()

    @abstractmethod
    def _create_widget(self) -> None:
        """Create the widget. Must be implemented by subclasses."""
        pass

    def _setup_widget(self) -> None:
        """Setup widget after creation. Can be overridden."""
        pass

    def destroy(self) -> None:
        """Destroy the widget."""
        if hasattr(self, 'widget') and self.widget:
            self.widget.destroy()


class BaseDialog:
    """Base class for application dialogs."""

    def __init__(
            self,
            parent: tk.Widget,
            title: str,
            width: int = 600,
            height: int = 400,
            resizable: bool = True
    ):
        """Initialize base dialog.

        Args:
            parent: Parent widget
            title: Dialog title
            width: Dialog width
            height: Dialog height
            resizable: Whether dialog is resizable
        """
        self.parent = parent
        self.result = None

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry(f"{width}x{height}")

        if not resizable:
            self.dialog.resizable(False, False)

        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Handle window close
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # Center dialog
        self._center_dialog()

        # Create content
        self._create_content()

    def _center_dialog(self) -> None:
        """Center dialog on parent window."""
        self.dialog.update_idletasks()

        # Get parent position
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

        # Ensure dialog is on screen
        x = max(0, x)
        y = max(0, y)

        self.dialog.geometry(f"+{x}+{y}")

    def _create_content(self) -> None:
        """Create dialog content."""
        # Main container
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Body
        body_frame = ttk.Frame(main_frame)
        body_frame.pack(fill=tk.BOTH, expand=True)
        self._create_body(body_frame)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        self._create_buttons(button_frame)

    @abstractmethod
    def _create_body(self, parent: ttk.Frame) -> None:
        """Create dialog body. Must be implemented by subclasses."""
        pass

    def _create_buttons(self, parent: ttk.Frame) -> None:
        """Create dialog buttons."""
        ttk.Button(
            parent,
            text="Cancel",
            command=self._on_cancel
        ).pack(side=tk.RIGHT, padx=(5, 0))

        ttk.Button(
            parent,
            text="OK",
            command=self._on_ok
        ).pack(side=tk.RIGHT)

    def _on_ok(self) -> None:
        """Handle OK button."""
        if self._validate():
            self.result = self._get_result()
            self.dialog.destroy()

    def _on_cancel(self) -> None:
        """Handle Cancel button."""
        self.result = None
        self.dialog.destroy()

    def _validate(self) -> bool:
        """Validate dialog input. Can be overridden."""
        return True

    def _get_result(self) -> Any:
        """Get dialog result. Can be overridden."""
        return True

    def show(self) -> Any:
        """Show dialog and return result."""
        self.dialog.wait_window()
        return self.result


class ScrollableFrame(ttk.Frame):
    """A scrollable frame widget."""

    def __init__(self, parent: tk.Widget, **kwargs):
        """Initialize scrollable frame.

        Args:
            parent: Parent widget
            **kwargs: Additional frame options
        """
        super().__init__(parent, **kwargs)

        # Create canvas and scrollbar
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(
            self,
            orient="vertical",
            command=self.canvas.yview
        )
        self.scrollable_frame = ttk.Frame(self.canvas)

        # Configure canvas
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window(
            (0, 0),
            window=self.scrollable_frame,
            anchor="nw"
        )

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Pack widgets
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Bind mousewheel
        self._bind_mousewheel()

    def _bind_mousewheel(self) -> None:
        """Bind mousewheel events."""

        def _on_mousewheel(event):
            self.canvas.yview_scroll(
                int(-1 * (event.delta / 120)),
                "units"
            )

        def _bind_to_mousewheel(event):
            self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
            self.canvas.bind_all("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))
            self.canvas.bind_all("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))

        def _unbind_from_mousewheel(event):
            self.canvas.unbind_all("<MouseWheel>")
            self.canvas.unbind_all("<Button-4>")
            self.canvas.unbind_all("<Button-5>")

        self.scrollable_frame.bind("<Enter>", _bind_to_mousewheel)
        self.scrollable_frame.bind("<Leave>", _unbind_from_mousewheel)

    def get_frame(self) -> ttk.Frame:
        """Get the scrollable frame."""
        return self.scrollable_frame


class ValidatedEntry(ttk.Entry):
    """Entry widget with validation."""

    def __init__(
            self,
            parent: tk.Widget,
            validate_func: Optional[Callable[[str], bool]] = None,
            error_callback: Optional[Callable[[str], None]] = None,
            **kwargs
    ):
        """Initialize validated entry.

        Args:
            parent: Parent widget
            validate_func: Validation function
            error_callback: Error callback
            **kwargs: Additional entry options
        """
        self.validate_func = validate_func
        self.error_callback = error_callback

        # Create StringVar
        self.var = tk.StringVar()

        # Create entry
        super().__init__(
            parent,
            textvariable=self.var,
            **kwargs
        )

        # Setup validation
        if validate_func:
            self.configure(
                validate="focusout",
                validatecommand=(self.register(self._validate), '%P')
            )

    def _validate(self, value: str) -> bool:
        """Validate entry value."""
        if self.validate_func:
            is_valid = self.validate_func(value)

            if not is_valid and self.error_callback:
                self.error_callback(f"Invalid value: {value}")

            return is_valid

        return True

    def get(self) -> str:
        """Get entry value."""
        return self.var.get()

    def set(self, value: str) -> None:
        """Set entry value."""
        self.var.set(value)