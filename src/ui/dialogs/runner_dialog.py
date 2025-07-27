"""Runner configuration dialogs."""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, List, Optional
import json

from ..base import BaseDialog
from src.data.repository import DataRepository


class RunnerDialog(BaseDialog):
    """Dialog for adding/editing runner."""

    def __init__(
            self,
            parent: tk.Widget,
            runner_data: Optional[Dict[str, Any]] = None
    ):
        """Initialize runner dialog.

        Args:
            parent: Parent widget
            runner_data: Existing runner data for editing
        """
        self.runner_data = runner_data

        title = "Edit Runner" if runner_data else "Add Runner"
        super().__init__(parent, title, width=400, height=250)

    def _create_body(self, parent: ttk.Frame) -> None:
        """Create dialog body."""
        # Length
        length_frame = ttk.Frame(parent)
        length_frame.pack(fill=tk.X, pady=5)

        ttk.Label(length_frame, text="Length (mm):", width=15).pack(side=tk.LEFT)
        self.length_var = tk.IntVar(
            value=self.runner_data.get('Length', 500) if self.runner_data else 500
        )
        ttk.Spinbox(
            length_frame,
            from_=200,
            to=800,
            increment=50,
            textvariable=self.length_var,
            width=15
        ).pack(side=tk.LEFT)

        # Capacity
        capacity_frame = ttk.Frame(parent)
        capacity_frame.pack(fill=tk.X, pady=5)

        ttk.Label(capacity_frame, text="Capacity (kg):", width=15).pack(side=tk.LEFT)
        self.capacity_var = tk.IntVar(
            value=self.runner_data.get('Capacity', 30) if self.runner_data else 30
        )
        ttk.Combobox(
            capacity_frame,
            textvariable=self.capacity_var,
            values=[20, 30, 40, 50, 70],
            state="readonly",
            width=13
        ).pack(side=tk.LEFT)

        # Price
        price_frame = ttk.Frame(parent)
        price_frame.pack(fill=tk.X, pady=5)

        ttk.Label(price_frame, text="Price (£):", width=15).pack(side=tk.LEFT)
        self.price_var = tk.DoubleVar(
            value=self.runner_data.get('Price', 0.0) if self.runner_data else 0.0
        )
        ttk.Entry(price_frame, textvariable=self.price_var, width=15).pack(side=tk.LEFT)

        # Features
        features_frame = ttk.LabelFrame(parent, text="Features", padding=10)
        features_frame.pack(fill=tk.X, pady=10)

        self.soft_close_var = tk.BooleanVar(
            value=self.runner_data.get('SoftClose', True) if self.runner_data else True
        )
        ttk.Checkbutton(
            features_frame,
            text="Soft Close",
            variable=self.soft_close_var
        ).pack(anchor=tk.W)

        self.full_extension_var = tk.BooleanVar(
            value=self.runner_data.get('FullExtension', True) if self.runner_data else True
        )
        ttk.Checkbutton(
            features_frame,
            text="Full Extension",
            variable=self.full_extension_var
        ).pack(anchor=tk.W)

    def _validate(self) -> bool:
        """Validate dialog input."""
        if self.price_var.get() < 0:
            messagebox.showerror("Validation Error", "Price cannot be negative")
            return False

        return True

    def _get_result(self) -> Dict[str, Any]:
        """Get dialog result."""
        return {
            'Length': self.length_var.get(),
            'Capacity': self.capacity_var.get(),
            'Price': self.price_var.get(),
            'SoftClose': self.soft_close_var.get(),
            'FullExtension': self.full_extension_var.get()
        }


class RunnerDatabaseDialog(BaseDialog):
    """Dialog for managing runner database."""

    def __init__(
            self,
            parent: tk.Widget,
            runners_data: List[Dict[str, Any]],
            repository: DataRepository
    ):
        """Initialize runner database dialog.

        Args:
            parent: Parent widget
            runners_data: Current runners data
            repository: Data repository
        """
        self.runners_data = runners_data.copy()
        self.repository = repository
        self.has_changes = False
        self.current_brand_index = None

        super().__init__(parent, "Runner Database", width=900, height=600)

    def _create_body(self, parent: ttk.Frame) -> None:
        """Create dialog body."""
        # Main paned window
        paned = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Left panel - Brands
        brands_frame = ttk.LabelFrame(paned, text="Brands", padding=10)
        paned.add(brands_frame, weight=1)

        # Brand list
        self.brand_listbox = tk.Listbox(brands_frame, height=20)
        self.brand_listbox.pack(fill=tk.BOTH, expand=True)

        # Brand buttons
        brand_btn_frame = ttk.Frame(brands_frame)
        brand_btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(brand_btn_frame, text="Add Brand", command=self._add_brand).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(brand_btn_frame, text="Rename", command=self._rename_brand).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(brand_btn_frame, text="Delete", command=self._delete_brand).pack(
            side=tk.LEFT, padx=2
        )

        # Right panel - Runners
        runners_frame = ttk.LabelFrame(paned, text="Runners", padding=10)
        paned.add(runners_frame, weight=2)

        # Runners table
        columns = ('length', 'capacity', 'price', 'features')
        self.runner_tree = ttk.Treeview(
            runners_frame,
            columns=columns,
            show='headings',
            height=18
        )

        # Configure columns
        self.runner_tree.heading('length', text='Length (mm)')
        self.runner_tree.heading('capacity', text='Capacity (kg)')
        self.runner_tree.heading('price', text='Price (£)')
        self.runner_tree.heading('features', text='Features')

        self.runner_tree.column('length', width=100)
        self.runner_tree.column('capacity', width=100)
        self.runner_tree.column('price', width=100)
        self.runner_tree.column('features', width=200)

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            runners_frame,
            orient=tk.VERTICAL,
            command=self.runner_tree.yview
        )
        self.runner_tree.configure(yscrollcommand=scrollbar.set)

        # Pack
        self.runner_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Runner buttons
        runner_btn_frame = ttk.Frame(runners_frame)
        runner_btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(runner_btn_frame, text="Add Runner", command=self._add_runner).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(runner_btn_frame, text="Edit Runner", command=self._edit_runner).pack(
            side=tk.LEFT, padx=2
        )

