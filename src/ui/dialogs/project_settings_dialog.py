"""Project settings dialog."""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

from ..base import BaseDialog
from src.models import ProjectSettings
from src.config.constants import COMMON_SHEET_SIZES


class ProjectSettingsDialog(BaseDialog):
    """Dialog for editing project-specific settings."""

    def __init__(self, parent: tk.Widget, settings: ProjectSettings):
        """Initialize project settings dialog.

        Args:
            parent: Parent widget
            settings: Current project settings
        """
        self.settings = settings
        self.original_settings = settings.to_dict()

        super().__init__(parent, "Project Settings", width=500, height=400)

    def _create_body(self, parent: ttk.Frame) -> None:
        """Create dialog body."""
        # Sheet dimensions
        sheet_frame = ttk.LabelFrame(parent, text="Sheet Dimensions", padding=10)
        sheet_frame.pack(fill=tk.X, padx=10, pady=5)

        # Preset sizes
        preset_frame = ttk.Frame(sheet_frame)
        preset_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(preset_frame, text="Preset:").pack(side=tk.LEFT, padx=5)

        self.preset_var = tk.StringVar()
        preset_combo = ttk.Combobox(
            preset_frame,
            textvariable=self.preset_var,
            values=[size[2] for size in COMMON_SHEET_SIZES],
            state="readonly",
            width=20
        )
        preset_combo.pack(side=tk.LEFT, padx=5)
        preset_combo.bind('<<ComboboxSelected>>', self._on_preset_selected)

        # Custom dimensions
        dim_frame = ttk.Frame(sheet_frame)
        dim_frame.pack(fill=tk.X)

        ttk.Label(dim_frame, text="Width (mm):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.width_var = tk.DoubleVar(value=self.settings.sheet_width)
        ttk.Entry(dim_frame, textvariable=self.width_var, width=15).grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(dim_frame, text="Height (mm):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.height_var = tk.DoubleVar(value=self.settings.sheet_height)
        ttk.Entry(dim_frame, textvariable=self.height_var, width=15).grid(row=1, column=1, padx=5, pady=2)

        # Labor settings
        labor_frame = ttk.LabelFrame(parent, text="Labor Settings", padding=10)
        labor_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(labor_frame, text="Hourly Rate:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.labor_rate_var = tk.DoubleVar(value=self.settings.labor_rate)
        rate_frame = ttk.Frame(labor_frame)
        rate_frame.grid(row=0, column=1, sticky=tk.W)
        ttk.Label(rate_frame, text=self.settings.currency_symbol).pack(side=tk.LEFT)
        ttk.Entry(rate_frame, textvariable=self.labor_rate_var, width=10).pack(side=tk.LEFT)

        ttk.Label(labor_frame, text="Markup (%):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.markup_var = tk.DoubleVar(value=self.settings.markup_percentage)
        ttk.Entry(labor_frame, textvariable=self.markup_var, width=12).grid(row=1, column=1, sticky=tk.W, padx=5,
                                                                            pady=2)

        # Company info
        company_frame = ttk.LabelFrame(parent, text="Company Information", padding=10)
        company_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(company_frame, text="Company Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.company_var = tk.StringVar(value=self.settings.company_name)
        ttk.Entry(company_frame, textvariable=self.company_var, width=30).grid(row=0, column=1, padx=5, pady=2)

        # Material defaults
        defaults_frame = ttk.LabelFrame(parent, text="Defaults", padding=10)
        defaults_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(defaults_frame, text="Default Thickness (mm):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.thickness_var = tk.DoubleVar(value=self.settings.default_material_thickness)
        ttk.Entry(defaults_frame, textvariable=self.thickness_var, width=10).grid(row=0, column=1, sticky=tk.W, padx=5,
                                                                                  pady=2)

    def _on_preset_selected(self, event=None) -> None:
        """Handle preset size selection."""
        preset = self.preset_var.get()

        for width, height, name in COMMON_SHEET_SIZES:
            if name == preset:
                self.width_var.set(width)
                self.height_var.set(height)
                break

    def _validate(self) -> bool:
        """Validate input values."""
        try:
            # Validate sheet dimensions
            if self.width_var.get() <= 0 or self.height_var.get() <= 0:
                raise ValueError("Sheet dimensions must be positive")

            # Validate labor rate
            if self.labor_rate_var.get() < 0:
                raise ValueError("Labor rate cannot be negative")

            # Validate markup
            if self.markup_var.get() < 0:
                raise ValueError("Markup percentage cannot be negative")

            # Validate thickness
            if self.thickness_var.get() <= 0:
                raise ValueError("Default thickness must be positive")

            return True

        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))
            return False

    def _get_result(self) -> ProjectSettings:
        """Get updated settings."""
        self.settings.sheet_width = self.width_var.get()
        self.settings.sheet_height = self.height_var.get()
        self.settings.labor_rate = self.labor_rate_var.get()
        self.settings.markup_percentage = self.markup_var.get()
        self.settings.company_name = self.company_var.get()
        self.settings.default_material_thickness = self.thickness_var.get()

        return self.settings