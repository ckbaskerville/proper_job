"""Sheet visualization window."""

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Rectangle as MplRectangle
import matplotlib.patches as patches
from typing import List, Dict, Any, Optional
import math

from src.models.geometry import PlacedRectangle, Rectangle
from src.business.calculator import QuoteCalculator
from src.config import DarkTheme


class VisualizationWindow:
    """Window for visualizing sheet layouts."""

    def __init__(
            self,
            parent: tk.Widget,
            calculator: QuoteCalculator,
            quote: Dict[str, Any]
    ):
        """Initialize visualization window.

        Args:
            parent: Parent widget
            calculator: Quote calculator with optimization results
            quote: Quote data
        """
        self.parent = parent
        self.calculator = calculator
        self.quote = quote

        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title("Sheet Layout Visualization")
        self.window.geometry("1000x700")

        # Get sheet data
        self.sheets_by_material = calculator._sheets_by_material
        self.current_material_index = 0
        self.material_keys = list(self.sheets_by_material.keys())

        self._create_widgets()

        # Show first material
        if self.material_keys:
            self._show_material(0)

    def _create_widgets(self) -> None:
        """Create window widgets."""
        # Control frame
        control_frame = ttk.Frame(self.window)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        # Material selector
        ttk.Label(control_frame, text="Material:").pack(side=tk.LEFT, padx=5)

        self.material_var = tk.StringVar()
        material_values = [
            f"{mat} {thick}mm"
            for mat, thick in self.material_keys
        ]
        self.material_combo = ttk.Combobox(
            control_frame,
            textvariable=self.material_var,
            values=material_values,
            state="readonly",
            width=30
        )
        self.material_combo.pack(side=tk.LEFT, padx=5)
        self.material_combo.bind('<<ComboboxSelected>>', self._on_material_changed)

        # Navigation buttons
        self.prev_btn = ttk.Button(
            control_frame,
            text="← Previous Sheet",
            command=self._prev_sheet,
            state=tk.DISABLED
        )
        self.prev_btn.pack(side=tk.LEFT, padx=5)

        self.next_btn = ttk.Button(
            control_frame,
            text="Next Sheet →",
            command=self._next_sheet,
            state=tk.DISABLED
        )
        self.next_btn.pack(side=tk.LEFT, padx=5)

        # Sheet info
        self.sheet_info_label = ttk.Label(
            control_frame,
            text="Sheet: 0/0"
        )
        self.sheet_info_label.pack(side=tk.LEFT, padx=20)

        # View options
        self.show_labels_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            control_frame,
            text="Show Labels",
            variable=self.show_labels_var,
            command=self._update_display
        ).pack(side=tk.RIGHT, padx=5)

        self.show_dimensions_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            control_frame,
            text="Show Dimensions",
            variable=self.show_dimensions_var,
            command=self._update_display
        ).pack(side=tk.RIGHT, padx=5)

        # Canvas frame
        canvas_frame = ttk.Frame(self.window)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Create matplotlib figure
        self.fig = plt.Figure(figsize=(10, 8), dpi=100)
        self.ax = self.fig.add_subplot(111)

        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=canvas_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Info frame
        info_frame = ttk.Frame(self.window)
        info_frame.pack(fill=tk.X, padx=10, pady=5)

        self.efficiency_label = ttk.Label(
            info_frame,
            text="Efficiency: 0%"
        )
        self.efficiency_label.pack(side=tk.LEFT, padx=10)

        self.parts_label = ttk.Label(
            info_frame,
            text="Parts: 0"
        )
        self.parts_label.pack(side=tk.LEFT, padx=10)

        self.waste_label = ttk.Label(
            info_frame,
            text="Waste: 0 mm²"
        )
        self.waste_label.pack(side=tk.LEFT, padx=10)

        # Button frame
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(
            button_frame,
            text="Export All",
            command=self._export_all
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Export Current",
            command=self._export_current
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Close",
            command=self.window.destroy
        ).pack(side=tk.RIGHT, padx=5)

    def _on_material_changed(self, event=None) -> None:
        """Handle material selection change."""
        index = self.material_combo.current()
        if index >= 0:
            self._show_material(index)

    def _show_material(self, index: int) -> None:
        """Show sheets for a specific material.

        Args:
            index: Material index
        """
        self.current_material_index = index
        self.material_var.set(
            f"{self.material_keys[index][0]} {self.material_keys[index][1]}mm"
        )

        # Reset sheet index
        self.current_sheet_index = 0

        # Update display
        self._update_display()

    def _prev_sheet(self) -> None:
        """Show previous sheet."""
        if self.current_sheet_index > 0:
            self.current_sheet_index -= 1
            self._update_display()

    def _next_sheet(self) -> None:
        """Show next sheet."""
        material_key = self.material_keys[self.current_material_index]
        sheets = self.sheets_by_material[material_key]

        if self.current_sheet_index < len(sheets) - 1:
            self.current_sheet_index += 1
            self._update_display()

    def _update_display(self) -> None:
        """Update the sheet display."""
        if not self.material_keys:
            return

        # Get current sheet data
        material_key = self.material_keys[self.current_material_index]
        sheets = self.sheets_by_material[material_key]

        if not sheets:
            return

        # Update navigation buttons
        self.prev_btn['state'] = (
            tk.NORMAL if self.current_sheet_index > 0 else tk.DISABLED
        )
        self.next_btn['state'] = (
            tk.NORMAL if self.current_sheet_index < len(sheets) - 1
            else tk.DISABLED
        )

        # Update sheet info
        self.sheet_info_label.config(
            text=f"Sheet: {self.current_sheet_index + 1}/{len(sheets)}"
        )

        # Clear plot
        self.ax.clear()

        # Get sheet
        sheet = sheets[self.current_sheet_index]

        # Draw sheet
        self._draw_sheet(sheet)

        # Update canvas
        self.canvas.draw()

        # Update info
        self._update_info(sheet)

    def _draw_sheet(self, sheet: List[PlacedRectangle]) -> None:
        """Draw a sheet with placed rectangles.

        Args:
            sheet: List of placed rectangles
        """
        # Sheet dimensions
        width = self.calculator.sheet_width
        height = self.calculator.sheet_height

        # Draw sheet boundary
        sheet_rect = MplRectangle(
            (0, 0), width, height,
            linewidth=2, edgecolor='black',
            facecolor='lightgray', alpha=0.3
        )
        self.ax.add_patch(sheet_rect)

        # Color palette
        colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
            '#DDA0DD', '#98D8E8', '#F7DC6F', '#BB8FCE', '#85C1E9'
        ]

        # Draw rectangles
        for i, rect in enumerate(sheet):
            color = colors[i % len(colors)]

            # Draw rectangle
            rectangle = MplRectangle(
                (rect.x, rect.y), rect.width, rect.height,
                linewidth=1.5, edgecolor='black',
                facecolor=color, alpha=0.7
            )
            self.ax.add_patch(rectangle)

            # Add labels if enabled
            if self.show_labels_var.get():
                center_x = rect.x + rect.width / 2
                center_y = rect.y + rect.height / 2

                # Rectangle ID
                self.ax.text(
                    center_x, center_y,
                    rect.id,
                    ha='center', va='center',
                    fontsize=8,
                    color='black'
                )

            # Add dimensions if enabled
            if self.show_dimensions_var.get():
                center_x = rect.x + rect.width / 2
                center_y = rect.y + rect.height / 2

                # Dimensions text
                dim_text = f"{rect.width:.0f}×{rect.height:.0f}"
                self.ax.text(
                    center_x, center_y - rect.height * 0.15,
                    dim_text,
                    ha='center', va='center',
                    fontsize=8,
                    color='black'
                )

        # Set axis properties
        self.ax.set_xlim(-50, width + 50)
        self.ax.set_ylim(-50, height + 50)
        self.ax.set_aspect('equal')
        self.ax.grid(True, alpha=0.3)
        self.ax.set_xlabel('Width (mm)', fontsize=12)
        self.ax.set_ylabel('Height (mm)', fontsize=12)

        # Title
        material, thickness = self.material_keys[self.current_material_index]
        self.ax.set_title(
            f'{material} {thickness}mm - Sheet {self.current_sheet_index + 1}',
            fontsize=14, fontweight='bold'
        )

    def _update_info(self, sheet: List[PlacedRectangle]) -> None:
        """Update information labels.

        Args:
            sheet: Current sheet
        """
        # Calculate efficiency
        sheet_area = self.calculator.sheet_width * self.calculator.sheet_height
        used_area = sum(rect.width * rect.height for rect in sheet)
        efficiency = (used_area / sheet_area) * 100 if sheet_area > 0 else 0
        waste_area = sheet_area - used_area

        # Update labels
        self.efficiency_label.config(
            text=f"Efficiency: {efficiency:.1f}%"
        )
        self.parts_label.config(
            text=f"Parts: {len(sheet)}"
        )
        self.waste_label.config(
            text=f"Waste: {waste_area:,.0f} mm²"
        )

    def _export_current(self) -> None:
        """Export current sheet visualization."""
        from tkinter import filedialog

        filename = filedialog.asksaveasfilename(
            title="Export Sheet",
            defaultextension=".png",
            filetypes=[
                ("PNG files", "*.png"),
                ("PDF files", "*.pdf"),
                ("All files", "*.*")
            ]
        )

        if filename:
            self.fig.savefig(filename, dpi=300, bbox_inches='tight')
            tk.messagebox.showinfo(
                "Export Complete",
                f"Sheet exported to {filename}"
            )

    def _export_all(self) -> None:
        """Export all sheets."""
        from tkinter import filedialog, messagebox
        import os

        directory = filedialog.askdirectory(
            title="Select Export Directory"
        )

        if directory:
            # Store current state
            current_material = self.current_material_index
            current_sheet = self.current_sheet_index

            # Export all sheets
            count = 0
            for mat_idx, material_key in enumerate(self.material_keys):
                material, thickness = material_key
                sheets = self.sheets_by_material[material_key]

                for sheet_idx, sheet in enumerate(sheets):
                    # Update display
                    self.current_material_index = mat_idx
                    self.current_sheet_index = sheet_idx
                    self._update_display()

                    # Generate filename
                    filename = (
                        f"{material}_{thickness}mm_sheet_{sheet_idx + 1}.png"
                    )
                    filepath = os.path.join(directory, filename)

                    # Save
                    self.fig.savefig(filepath, dpi=300, bbox_inches='tight')
                    count += 1

            # Restore state
            self.current_material_index = current_material
            self.current_sheet_index = current_sheet
            self._update_display()

            messagebox.showinfo(
                "Export Complete",
                f"Exported {count} sheets to {directory}"
            )