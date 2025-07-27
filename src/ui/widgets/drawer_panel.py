"""Drawer panel widget for cabinet editor."""

import tkinter as tk
from tkinter import ttk
from typing import Optional, List, Dict, Any

from src.models import Drawer, Carcass
from src.business.material_manager import MaterialManager
from .material_selector import MaterialSelector


class DrawerPanel(ttk.LabelFrame):
    """Panel for editing drawer specifications."""

    def __init__(
            self,
            parent: tk.Widget,
            material_manager: MaterialManager,
            runners_data: List[Dict[str, Any]],
            drawer_number: int
    ):
        """Initialize drawer panel.

        Args:
            parent: Parent widget
            material_manager: Material manager instance
            runners_data: Runner specifications
            drawer_number: Drawer number for display
        """
        super().__init__(parent, text=f"Drawer {drawer_number}", padding=5)

        self.material_manager = material_manager
        self.runners_data = runners_data
        self.drawer_number = drawer_number

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create panel widgets."""
        # Height
        height_frame = ttk.Frame(self)
        height_frame.pack(fill=tk.X, pady=2)

        ttk.Label(height_frame, text="Height (mm):", width=15).pack(side=tk.LEFT)
        self.height_var = tk.IntVar(value=150)
        ttk.Spinbox(
            height_frame,
            from_=60,
            to=300,
            textvariable=self.height_var,
            width=10
        ).pack(side=tk.LEFT)

        # Material
        mat_frame = ttk.Frame(self)
        mat_frame.pack(fill=tk.X, pady=2)

        ttk.Label(mat_frame, text="Material:", width=15).pack(side=tk.LEFT)
        self.material_selector = MaterialSelector(
            mat_frame,
            self.material_manager,
            component_type="Carcass"  # Drawers use carcass materials
        )
        self.material_selector.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Runner brand
        brand_frame = ttk.Frame(self)
        brand_frame.pack(fill=tk.X, pady=2)

        ttk.Label(brand_frame, text="Runner Brand:", width=15).pack(side=tk.LEFT)
        self.runner_brand_var = tk.StringVar()
        brands = [r['Name'] for r in self.runners_data]
        self.brand_combo = ttk.Combobox(
            brand_frame,
            textvariable=self.runner_brand_var,
            values=brands,
            state="readonly",
            width=20
        )
        self.brand_combo.pack(side=tk.LEFT)
        self.brand_combo.bind('<<ComboboxSelected>>', self._on_brand_changed)

        # Runner size
        size_frame = ttk.Frame(self)
        size_frame.pack(fill=tk.X, pady=2)

        ttk.Label(size_frame, text="Runner Size (mm):", width=15).pack(side=tk.LEFT)
        self.runner_size_var = tk.IntVar()
        self.size_combo = ttk.Combobox(
            size_frame,
            textvariable=self.runner_size_var,
            values=[],
            state="disabled",
            width=10
        )
        self.size_combo.pack(side=tk.LEFT)
        self.size_combo.bind('<<ComboboxSelected>>', self._on_size_changed)

        # Runner capacity
        capacity_frame = ttk.Frame(self)
        capacity_frame.pack(fill=tk.X, pady=2)

        ttk.Label(capacity_frame, text="Runner Capacity (kg):", width=15).pack(side=tk.LEFT)
        self.runner_capacity_var = tk.IntVar()
        self.capacity_combo = ttk.Combobox(
            capacity_frame,
            textvariable=self.runner_capacity_var,
            values=[],
            state="disabled",
            width=10
        )
        self.capacity_combo.pack(side=tk.LEFT)

        # Price display
        self.price_label = ttk.Label(
            capacity_frame,
            text="£0.00 per pair"
        )
        self.price_label.pack(side=tk.LEFT, padx=10)

        # Set defaults
        if brands:
            self.runner_brand_var.set(brands[0])
            self._on_brand_changed()

    def _on_brand_changed(self, event=None) -> None:
        """Handle runner brand selection."""
        brand = self.runner_brand_var.get()
        if not brand:
            return

        # Find brand data
        brand_data = None
        for b in self.runners_data:
            if b['Name'] == brand:
                brand_data = b
                break

        if brand_data:
            # Get unique sizes
            sizes = sorted(set(r['Length'] for r in brand_data['Runners']))
            self.size_combo['values'] = sizes
            self.size_combo['state'] = 'readonly'

            if sizes:
                self.runner_size_var.set(sizes[0])
                self._on_size_changed()

    def _on_size_changed(self, event=None) -> None:
        """Handle runner size selection."""
        brand = self.runner_brand_var.get()
        size = self.runner_size_var.get()

        if not brand or not size:
            return

        # Find brand data
        brand_data = None
        for b in self.runners_data:
            if b['Name'] == brand:
                brand_data = b
                break

        if brand_data:
            # Get capacities for this size
            capacities = sorted(set(
                r['Capacity'] for r in brand_data['Runners']
                if r['Length'] == size
            ))

            self.capacity_combo['values'] = capacities
            self.capacity_combo['state'] = 'readonly'

            if capacities:
                self.runner_capacity_var.set(capacities[0])
                self._update_price()

    def _update_price(self) -> None:
        """Update price display."""
        brand = self.runner_brand_var.get()
        size = self.runner_size_var.get()
        capacity = self.runner_capacity_var.get()

        if not all([brand, size, capacity]):
            self.price_label.config(text="£0.00 per pair")
            return

        # Find price
        price = 0.0
        for b in self.runners_data:
            if b['Name'] == brand:
                for r in b['Runners']:
                    if r['Length'] == size and r['Capacity'] == capacity:
                        price = r['Price']
                        break
                break

        self.price_label.config(text=f"£{price * 2:.2f} per pair")

    def get_drawer(self, carcass: Carcass) -> Optional[Drawer]:
        """Get drawer from panel data.

        Args:
            carcass: Parent carcass

        Returns:
            Drawer instance or None if invalid
        """
        try:
            material, thickness = self.material_selector.get_selection()

            # Get runner price
            runner_price = 0.0
            brand = self.runner_brand_var.get()
            size = self.runner_size_var.get()
            capacity = self.runner_capacity_var.get()

            for b in self.runners_data:
                if b['Name'] == brand:
                    for r in b['Runners']:
                        if r['Length'] == size and r['Capacity'] == capacity:
                            runner_price = r['Price']
                            break
                    break

            return Drawer(
                height=self.height_var.get(),
                thickness=int(thickness),
                material=material,
                runner_model=brand,
                runner_size=size,
                runner_capacity=capacity,
                carcass=carcass,
                runner_price=runner_price
            )

        except Exception as e:
            print(f"Error creating drawer: {e}")
            return None

    def load_drawer(self, drawer: Drawer) -> None:
        """Load drawer data into panel.

        Args:
            drawer: Drawer to load
        """
        self.height_var.set(drawer.height)
        self.material_selector.set_material(drawer.material, drawer.thickness)
        self.runner_brand_var.set(drawer.runner_model)
        self._on_brand_changed()
        self.runner_size_var.set(drawer.runner_size)
        self._on_size_changed()
        self.runner_capacity_var.set(drawer.runner_capacity)
        self._update_price()