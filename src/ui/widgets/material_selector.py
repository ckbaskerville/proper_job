"""Material selector widget."""

import tkinter as tk
from tkinter import ttk
from typing import Tuple, Optional, List

from src.business.material_manager import MaterialManager


class MaterialSelector(ttk.Frame):
    """Widget for selecting material and thickness."""

    def __init__(
            self,
            parent: tk.Widget,
            material_manager: MaterialManager,
            component_type: str = "Carcass",
            on_change: Optional[callable] = None
    ):
        """Initialize material selector.

        Args:
            parent: Parent widget
            material_manager: Material manager instance
            component_type: Component type for filtering materials
            on_change: Callback when selection changes
        """
        super().__init__(parent)

        self.material_manager = material_manager
        self.component_type = component_type
        self.on_change = on_change

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create selector widgets."""
        # Material combo
        self.material_var = tk.StringVar()
        materials = self.material_manager.get_materials_for_component(
            self.component_type
        )

        self.material_combo = ttk.Combobox(
            self,
            textvariable=self.material_var,
            values=materials,
            state="readonly",
            width=20
        )
        self.material_combo.pack(side=tk.LEFT, padx=2)

        # Thickness combo
        self.thickness_var = tk.StringVar()
        self.thickness_combo = ttk.Combobox(
            self,
            textvariable=self.thickness_var,
            values=[],
            state="readonly",
            width=10
        )
        self.thickness_combo.pack(side=tk.LEFT, padx=2)

        ttk.Label(self, text="mm").pack(side=tk.LEFT)

        # Bind events
        self.material_combo.bind('<<ComboboxSelected>>', self._on_material_changed)
        self.thickness_combo.bind('<<ComboboxSelected>>', self._on_thickness_changed)

        # Set default if available
        if materials:
            self.material_var.set(materials[0])
            self._update_thicknesses()

    def _on_material_changed(self, event=None) -> None:
        """Handle material selection change."""
        self._update_thicknesses()
        if self.on_change:
            self.on_change()

    def _on_thickness_changed(self, event=None) -> None:
        """Handle thickness selection change."""
        if self.on_change:
            self.on_change()

    def _update_thicknesses(self) -> None:
        """Update available thicknesses for selected material."""
        material = self.material_var.get()
        if material:
            thicknesses = self.material_manager.get_available_thicknesses(material)
            thickness_values = [str(t) for t in thicknesses]
            self.thickness_combo['values'] = thickness_values

            # Select first thickness if available
            if thickness_values:
                self.thickness_var.set(thickness_values[0])
            else:
                self.thickness_var.set("")

    def get_selection(self) -> Tuple[str, float]:
        """Get current selection.

        Returns:
            Tuple of (material, thickness)
        """
        material = self.material_var.get()
        thickness_str = self.thickness_var.get()

        thickness = float(thickness_str) if thickness_str else 18.0

        return material, thickness

    def set_material(self, material: str, thickness: float) -> None:
        """Set material and thickness.

        Args:
            material: Material name
            thickness: Material thickness
        """
        self.material_var.set(material)
        self._update_thicknesses()
        self.thickness_var.set(str(int(thickness)))
