"""Hinge configuration dialogs."""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, List, Optional
import json

from .base_dialog import BaseDialog
from src.data.repository import DataRepository


class HingeDialog(BaseDialog):
    """Dialog for adding/editing hinge."""

    def __init__(
            self,
            parent: tk.Widget,
            hinge_data: Optional[Dict[str, Any]] = None
    ):
        """Initialize hinge dialog.

        Args:
            parent: Parent widget
            hinge_data: Existing hinge data for editing
        """
        self.hinge_data = hinge_data

        title = "Edit Hinge" if hinge_data else "Add Hinge"
        super().__init__(parent, title, width=400, height=200)

    def _create_body(self, parent: ttk.Frame) -> None:
        """Create dialog body."""
        # Name
        name_frame = ttk.Frame(parent)
        name_frame.pack(fill=tk.X, pady=5)

        ttk.Label(name_frame, text="Hinge Name:", width=15).pack(side=tk.LEFT)
        self.name_var = tk.StringVar(
            value=self.hinge_data.get('Name', '') if self.hinge_data else ''
        )
        ttk.Entry(name_frame, textvariable=self.name_var, width=25).pack(side=tk.LEFT)

        # Price
        price_frame = ttk.Frame(parent)
        price_frame.pack(fill=tk.X, pady=5)

        ttk.Label(price_frame, text="Price (Each) (£):", width=15).pack(side=tk.LEFT)
        self.price_var = tk.DoubleVar(
            value=self.hinge_data.get('Price', 0.0) if self.hinge_data else 0.0
        )
        ttk.Entry(price_frame, textvariable=self.price_var, width=15).pack(side=tk.LEFT)

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

    def _validate(self) -> bool:
        """Validate dialog input."""
        if not self.name_var.get().strip():
            messagebox.showerror("Validation Error", "Hinge name is required")
            return False

        if self.price_var.get() < 0:
            messagebox.showerror("Validation Error", "Price cannot be negative")
            return False

        return True

    def _get_result(self) -> Dict[str, Any]:
        """Get dialog result."""
        return {
            'Name': self.name_var.get().strip(),
            'Price': self.price_var.get()
        }


class HingeDatabaseDialog(BaseDialog):
    """Dialog for managing hinge database."""

    def __init__(
            self,
            parent: tk.Widget,
            hinges_data: Dict[str, Any],
            repository: DataRepository
    ):
        """Initialize hinge database dialog.

        Args:
            parent: Parent widget
            hinges_data: Current hinges data
            repository: Data repository
        """
        self.hinges_data = hinges_data.copy()
        self.repository = repository
        self.has_changes = False

        super().__init__(parent, "Hinge Database", width=600, height=500)

    def _create_body(self, parent: ttk.Frame) -> None:
        """Create dialog body."""
        # Controls
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(
            control_frame,
            text="Add Hinge",
            command=self._add_hinge
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            control_frame,
            text="Edit Selected",
            command=self._edit_hinge
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            control_frame,
            text="Delete Selected",
            command=self._delete_hinge
        ).pack(side=tk.LEFT, padx=5)

        # Hinges table
        columns = ('name', 'price')
        self.hinges_tree = ttk.Treeview(
            parent,
            columns=columns,
            show='headings',
            height=15
        )

        # Configure columns
        self.hinges_tree.heading('name', text='Hinge Name')
        self.hinges_tree.heading('price', text='Price Each (£)')

        self.hinges_tree.column('name', width=300)
        self.hinges_tree.column('price', width=150)

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            parent,
            orient=tk.VERTICAL,
            command=self.hinges_tree.yview
        )
        self.hinges_tree.configure(yscrollcommand=scrollbar.set)

        self.hinges_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10))

        # Populate hinges
        self._refresh_hinges_tree()

    def _refresh_hinges_tree(self) -> None:
        """Refresh hinges tree view."""
        # Clear existing items
        for item in self.hinges_tree.get_children():
            self.hinges_tree.delete(item)

        # Add hinges
        for hinge in self.hinges_data.get('Hinges', []):
            values = (
                hinge['Name'],
                f"£{hinge['Price']:.2f}"
            )
            self.hinges_tree.insert('', tk.END, values=values)

    def _add_hinge(self) -> None:
        """Add a new hinge."""
        dialog = HingeDialog(self.dialog)
        result = dialog.show()

        if result:
            if 'Hinges' not in self.hinges_data:
                self.hinges_data['Hinges'] = []

            # Check for duplicate names
            existing_names = [h['Name'] for h in self.hinges_data['Hinges']]
            if result['Name'] in existing_names:
                messagebox.showerror("Error", "A hinge with this name already exists")
                return

            self.hinges_data['Hinges'].append(result)
            self._refresh_hinges_tree()
            self.has_changes = True

    def _edit_hinge(self) -> None:
        """Edit selected hinge."""
        selection = self.hinges_tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a hinge to edit")
            return

        index = self.hinges_tree.index(selection[0])
        hinge_data = self.hinges_data['Hinges'][index]

        dialog = HingeDialog(self.dialog, hinge_data)
        result = dialog.show()

        if result:
            # Check for duplicate names (excluding current hinge)
            existing_names = [h['Name'] for i, h in enumerate(self.hinges_data['Hinges']) if i != index]
            if result['Name'] in existing_names:
                messagebox.showerror("Error", "A hinge with this name already exists")
                return

            self.hinges_data['Hinges'][index] = result
            self._refresh_hinges_tree()
            self.has_changes = True

    def _delete_hinge(self) -> None:
        """Delete selected hinge."""
        selection = self.hinges_tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a hinge to delete")
            return

        if messagebox.askyesno("Confirm Delete", "Delete this hinge?"):
            index = self.hinges_tree.index(selection[0])
            del self.hinges_data['Hinges'][index]
            self._refresh_hinges_tree()
            self.has_changes = True

    def _create_buttons(self, parent: ttk.Frame) -> None:
        """Create dialog buttons."""
        ttk.Button(
            parent,
            text="Cancel",
            command=self._on_cancel
        ).pack(side=tk.RIGHT, padx=(5, 0))

        ttk.Button(
            parent,
            text="Save",
            command=self._on_ok
        ).pack(side=tk.RIGHT)

    def _on_ok(self) -> None:
        """Handle OK button."""
        if self.has_changes:
            # Save to file
            try:
                self.repository.save_hinges(self.hinges_data)
                self.result = True
                self.dialog.destroy()
            except Exception as e:
                messagebox.showerror(
                    "Save Error",
                    f"Failed to save hinges: {str(e)}"
                )
        else:
            self.result = False
            self.dialog.destroy()