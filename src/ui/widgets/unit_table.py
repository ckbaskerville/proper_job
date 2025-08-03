"""Unit table widget for displaying cabinet units."""

import tkinter as tk
from tkinter import ttk
from typing import List, Optional, Callable

from src.models import Cabinet
from src.config import DarkTheme


class UnitTableWidget(ttk.Frame):
    """Widget for displaying and managing cabinet units."""

    def __init__(
            self,
            parent: tk.Widget,
            on_select: Optional[Callable[[Optional[int]], None]] = None,
            on_add: Optional[Callable[[], None]] = None,
            on_edit: Optional[Callable[[], None]] = None,
            on_remove: Optional[Callable[[], None]] = None,
            on_duplicate: Optional[Callable[[], None]] = None
    ):
        """Initialize unit table widget.

        Args:
            parent: Parent widget
            on_select: Callback for selection changes
            on_add: Callback for add button
            on_edit: Callback for edit button
            on_remove: Callback for remove button
            on_duplicate: Callback for duplicate button
        """
        super().__init__(parent)

        self.on_select = on_select
        self.on_add = on_add
        self.on_edit = on_edit
        self.on_remove = on_remove
        self.on_duplicate = on_duplicate

        self._selected_index: Optional[int] = None
        self._units: List[Cabinet] = []

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create the widget layout."""
        # Configure grid
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Create treeview
        columns = ('name', 'options', 'dimensions', 'material', 'quantity')
        self.tree = ttk.Treeview(
            self,
            columns=columns,
            show='headings',
            selectmode='browse'
        )

        # Configure columns
        self.tree.heading('name', text='Name', anchor='w')
        self.tree.heading('options', text='Options', anchor='w')
        self.tree.heading('dimensions', text='Dimensions (H×W×D)', anchor='w')
        self.tree.heading('material', text='Material', anchor='w')
        self.tree.heading('quantity', text='Quantity', anchor='w')

        # Column widths
        self.tree.column('name', width=150, anchor='w')
        self.tree.column('options', width=200, anchor='w')
        self.tree.column('dimensions', width=150, anchor='w')
        self.tree.column('material', width=100, anchor='w')
        self.tree.column('quantity', width=50, anchor='w')

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            self,
            orient=tk.VERTICAL,
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Grid layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Button frame
        button_frame = ttk.Frame(self)
        button_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        # Summary label
        self.summary_label = ttk.Label(
            button_frame,
            text="0 cabinets, 0 total units"
        )
        self.summary_label.pack(side=tk.RIGHT, padx=5)

        self.remove_btn = ttk.Button(
            button_frame,
            text="Remove",
            command=self._on_remove,
            state=tk.DISABLED
        )
        self.remove_btn.pack(side=tk.RIGHT, padx=2)

        self.duplicate_btn = ttk.Button(
            button_frame,
            text="Duplicate",
            command=self._on_duplicate,
            state=tk.DISABLED
        )
        self.duplicate_btn.pack(side=tk.RIGHT, padx=2)

        self.edit_btn = ttk.Button(
            button_frame,
            text="Edit",
            command=self._on_edit,
            state=tk.DISABLED
        )
        self.edit_btn.pack(side=tk.RIGHT, padx=2)

        # Buttons
        ttk.Button(
            button_frame,
            text="Add Cabinet",
            command=self._on_add
        ).pack(side=tk.RIGHT, padx=2)

        # Bind events
        self.tree.bind('<<TreeviewSelect>>', self._on_selection_changed)
        self.tree.bind('<Double-Button-1>', lambda e: self._on_edit())
        self.tree.bind('<Delete>', lambda e: self._on_remove())
        self.tree.bind('<Return>', lambda e: self._on_edit())

    def _on_selection_changed(self, event=None) -> None:
        """Handle selection change."""
        selection = self.tree.selection()

        if selection:
            item = selection[0]
            self._selected_index = self.tree.index(item)

            # Enable buttons
            self.edit_btn.config(state=tk.NORMAL)
            self.duplicate_btn.config(state=tk.NORMAL)
            self.remove_btn.config(state=tk.NORMAL)
        else:
            self._selected_index = None

            # Disable buttons
            self.edit_btn.config(state=tk.DISABLED)
            self.duplicate_btn.config(state=tk.DISABLED)
            self.remove_btn.config(state=tk.DISABLED)

        # Notify callback
        if self.on_select:
            self.on_select(self._selected_index)

    def _on_add(self) -> None:
        """Handle add button."""
        if self.on_add:
            self.on_add()

    def _on_edit(self) -> None:
        """Handle edit button."""
        if self.on_edit and self._selected_index is not None:
            self.on_edit()

    def _on_duplicate(self) -> None:
        """Handle duplicate button."""
        if self.on_duplicate and self._selected_index is not None:
            self.on_duplicate()

    def _on_remove(self) -> None:
        """Handle remove button."""
        if self.on_remove and self._selected_index is not None:
            self.on_remove()

    def load_units(self, units: List[Cabinet]) -> None:
        """Load units into the table.

        Args:
            units: List of cabinet units
        """
        self._units = units

        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Add units
        total_units = 0
        for unit in units:
            # Determine type
            components = []
            if unit.drawers:
                components.append(f"{len(unit.drawers)} custom drawers")
            # Show DBC drawers
            if unit.dbc_drawers:
                dbc_materials = {}
                for dbc in unit.dbc_drawers:
                    if dbc.material not in dbc_materials:
                        dbc_materials[dbc.material] = 0
                    dbc_materials[dbc.material] += 1

                dbc_str = ", ".join([f"{count} {mat}" for mat, count in dbc_materials.items()])
                components.append(f"{len(unit.dbc_drawers)} DBC drawers ({dbc_str})")
            if unit.doors and unit.doors.quantity > 0:
                components.append(f"{unit.doors.quantity} doors")
            if unit.face_frame:
                components.append("face frame")

            unit_type = ", ".join(components) if components else "Base cabinet"

            # Format dimensions
            c = unit.carcass
            dimensions = f"{c.height:.0f}×{c.width:.0f}×{c.depth:.0f}"

            # Insert item
            self.tree.insert(
                '',
                tk.END,
                values=(
                    c.name,
                    unit_type,
                    dimensions,
                    f"{c.material} {c.material_thickness}mm",
                    unit.quantity
                )
            )

            total_units += unit.quantity

        # Update summary
        self.summary_label.config(
            text=f"{len(units)} cabinets, {total_units} total units"
        )

        # Clear selection
        self._selected_index = None
        self._on_selection_changed()

    def get_selected_index(self) -> Optional[int]:
        """Get the selected unit index."""
        return self._selected_index

    def select_unit(self, index: int) -> None:
        """Select a specific unit.

        Args:
            index: Unit index to select
        """
        if 0 <= index < len(self._units):
            items = self.tree.get_children()
            if index < len(items):
                self.tree.selection_set(items[index])
                self.tree.focus(items[index])
                self.tree.see(items[index])
