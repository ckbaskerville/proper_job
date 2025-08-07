"""DBC drawer panel widget for cabinet editor."""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Any
import csv
from io import StringIO

class DBCDrawerPanel(ttk.LabelFrame):
    """Panel for selecting pre-made DBC drawers."""

    def __init__(
            self,
            parent: tk.Widget,
            dbc_drawers_data: Dict[str, Any],
            drawer_number: int
    ):
        """Initialize DBC drawer panel.

        Args:
            parent: Parent widget
            dbc_drawers_data: DBC drawer pricing data
            drawer_number: Drawer number for display
        """
        super().__init__(parent, text=f"DBC Drawer {drawer_number}", padding=5)

        self.dbc_drawers_data = dbc_drawers_data
        self.drawer_number = drawer_number

        self._create_widgets()

    def _look_up_price(self, material: str, height: int, width: int, depth: int) -> float:
        """Look up price for given parameters.

        Args:
            material: Material type
            height: Drawer height
            width: Drawer width
            depth: Drawer depth

        Returns:
            Price for the specified drawer configuration
        """

        # Check if the material is valid
        if material not in self.dbc_drawers_data:
            raise KeyError(f"DBC Drawer {material} not found")


        price_df = self.dbc_drawers_data[material]

        area_value = price_df[(price_df['width'] == width) & (price_df['height'] == height)][f'depth_{depth}'].iloc[0]

        return area_value

    def _create_widgets(self) -> None:
        """Create panel widgets."""
        # Material selection
        mat_frame = ttk.Frame(self)
        mat_frame.pack(fill=tk.X, pady=2)

        ttk.Label(mat_frame, text="Material:", width=15).pack(side=tk.LEFT)
        self.material_var = tk.StringVar(value="Oak")
        self.material_combo = ttk.Combobox(
            mat_frame,
            textvariable=self.material_var,
            values=["Oak", "Walnut"],
            state="readonly",
            width=15
        )
        self.material_combo.pack(side=tk.LEFT)
        self.material_combo.bind('<<ComboboxSelected>>', self._on_material_changed)

        # Height selection
        height_frame = ttk.Frame(self)
        height_frame.pack(fill=tk.X, pady=2)

        ttk.Label(height_frame, text="Height (mm):", width=15).pack(side=tk.LEFT)
        self.height_var = tk.IntVar()
        self.height_combo = ttk.Combobox(
            height_frame,
            textvariable=self.height_var,
            values=[100, 150, 175, 225, 270, 300],
            state="readonly",
            width=15
        )
        self.height_combo.pack(side=tk.LEFT)
        self.height_combo.bind('<<ComboboxSelected>>', self._update_price)

        # Width selection
        width_frame = ttk.Frame(self)
        width_frame.pack(fill=tk.X, pady=2)

        ttk.Label(width_frame, text="Width (mm):", width=15).pack(side=tk.LEFT)
        self.width_var = tk.IntVar()
        self.width_combo = ttk.Combobox(
            width_frame,
            textvariable=self.width_var,
            values=[252, 352, 452, 552, 652, 752, 852, 952, 1152],
            state="readonly",
            width=15
        )
        self.width_combo.pack(side=tk.LEFT)
        self.width_combo.bind('<<ComboboxSelected>>', self._update_price)

        # Depth selection
        depth_frame = ttk.Frame(self)
        depth_frame.pack(fill=tk.X, pady=2)

        ttk.Label(depth_frame, text="Depth (mm):", width=15).pack(side=tk.LEFT)
        self.depth_var = tk.IntVar()
        self.depth_combo = ttk.Combobox(
            depth_frame,
            textvariable=self.depth_var,
            values=[300, 450, 500, 550, 600],
            state="readonly",
            width=15
        )
        self.depth_combo.pack(side=tk.LEFT)
        self.depth_combo.bind('<<ComboboxSelected>>', self._update_price)

        # Price display
        price_frame = ttk.Frame(self)
        price_frame.pack(fill=tk.X, pady=2)

        ttk.Label(price_frame, text="Price:", width=15).pack(side=tk.LEFT)
        self.price_label = ttk.Label(
            price_frame,
            text="£0.00",
            font=('Arial', 10, 'bold')
        )
        self.price_label.pack(side=tk.LEFT)

        # Set initial selections
        if self.height_combo['values']:
            self.height_var.set(150)  # Default 150mm height
        if self.width_combo['values']:
            self.width_var.set(452)  # Default 452mm width
        if self.depth_combo['values']:
            self.depth_var.set(500)  # Default 500mm depth

        self._update_price()

    def _on_material_changed(self, event=None) -> None:
        """Handle material change."""
        self._update_price()

    def _update_price(self, event=None) -> None:
        """Update price display based on selections."""
        material = self.material_var.get()

        try:
            height = self.height_var.get()
            width = self.width_var.get()
            depth = self.depth_var.get()

            if all([material, height, width, depth]):
                price = self._look_up_price(material, height, width, depth)
                self.price_label.config(text=f"£{price:.2f}")
            else:
                self.price_label.config(text="£0.00")

        except (tk.TclError, ValueError):
            self.price_label.config(text="£0.00")

    def get_dbc_drawer(self, carcass_name: str) -> Optional['DBCDrawer']:
        """Get DBC drawer from panel data.

        Args:
            carcass_name: Name of parent carcass

        Returns:
            DBCDrawer instance or None if invalid
        """
        try:
            material = self.material_var.get()
            height = self.height_var.get()
            width = self.width_var.get()
            depth = self.depth_var.get()

            if not all([material, height, width, depth]):
                return None

            price = self._look_up_price(material, height, width, depth)

            # Import here to avoid circular dependency
            from src.models.components import DBCDrawer

            return DBCDrawer(
                height=height,
                width=width,
                depth=depth,
                material=material,
                price=price,
                carcass_name=carcass_name
            )

        except Exception as e:
            print(f"Error creating DBC drawer: {e}")
            return None

    def load_dbc_drawer(self, drawer: 'DBCDrawer') -> None:
        """Load DBC drawer data into panel.

        Args:
            drawer: DBC drawer to load
        """
        self.material_var.set(drawer.material)
        self.height_var.set(drawer.height)
        self.width_var.set(drawer.width)
        self.depth_var.set(drawer.depth)
        self._update_price()