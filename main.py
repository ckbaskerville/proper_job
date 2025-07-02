import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import math
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional
import copy
import json
import os


# Define data structures
@dataclass
class Unit:
    name: str
    unit_type: str  # Type of kitchen unit (e.g., "Cabinet", "Drawer", etc.)
    height: float
    width: float
    depth: float
    material_thickness: float
    quantity: int = 1

    def get_parts(self) -> List[Tuple[float, float, str]]:
        """Returns a list of parts needed for this unit as (length, width, part_name)"""
        parts = []
        # Front and back
        parts.append((self.height, self.width, f"{self.name} - Front/Back"))
        parts.append((self.height, self.width, f"{self.name} - Front/Back"))

        # Sides
        parts.append((self.height, self.depth - self.material_thickness, f"{self.name} - Side"))
        parts.append((self.height, self.depth - self.material_thickness, f"{self.name} - Side"))

        # Top and bottom
        parts.append((self.width - 2 * self.material_thickness, self.depth - self.material_thickness,
                      f"{self.name} - Top/Bottom"))
        parts.append((self.width - 2 * self.material_thickness, self.depth - self.material_thickness,
                      f"{self.name} - Top/Bottom"))

        return parts

    def get_total_area(self) -> float:
        """Calculate the total area of material needed for this unit"""
        total_area = 0
        for part in self.get_parts():
            total_area += part[0] * part[1] * self.quantity
        return total_area


class SheetOptimizer:
    def __init__(self, sheet_width: float, sheet_height: float):
        self.sheet_width = sheet_width
        self.sheet_height = sheet_height

    def optimize(self, parts: List[Tuple[float, float, str]]) -> List[Dict]:
        """
        An improved bin packing algorithm to fit parts onto sheets
        Returns a list of sheets with their utilized parts
        """
        # Sort parts by area (decreasing)
        parts.sort(key=lambda p: p[0] * p[1], reverse=True)

        sheets = []

        for part_length, part_width, part_name in parts:
            # Ensure part fits on a sheet (rotate if necessary)
            if max(part_length, part_width) > max(self.sheet_width, self.sheet_height) or \
                    min(part_length, part_width) > min(self.sheet_width, self.sheet_height):
                continue  # Skip parts that can't fit on a sheet

            # Try to find a sheet with available space
            placed = False
            for sheet in sheets:
                if self._place_part_on_sheet(sheet, part_length, part_width, part_name):
                    placed = True
                    break

            # If no existing sheet has space, create a new one
            if not placed:
                new_sheet = {
                    'spaces': [(0, 0, self.sheet_width, self.sheet_height)],  # x, y, width, height
                    'cuts': [],
                    'utilization': 0
                }
                self._place_part_on_sheet(new_sheet, part_length, part_width, part_name)
                sheets.append(new_sheet)

        # Calculate utilization for each sheet
        for sheet in sheets:
            used_area = sum(p[0] * p[1] for p, _, _ in sheet['cuts'])
            sheet['utilization'] = (used_area / (self.sheet_width * self.sheet_height)) * 100

        return sheets

    def _place_part_on_sheet(self, sheet: Dict, part_length: float, part_width: float, part_name: str) -> bool:
        """Attempt to place a part on the given sheet using a more efficient algorithm"""
        # Try each available space
        for i, (space_x, space_y, space_width, space_height) in enumerate(sheet['spaces']):
            # Try original orientation
            if part_length <= space_width and part_width <= space_height:
                # Part fits, place it here
                sheet['cuts'].append(((part_length, part_width, part_name), space_x, space_y))

                # Remove this space
                del sheet['spaces'][i]

                # Add new spaces (split the remaining area)
                # Space to the right of the part
                if space_width - part_length > 0:
                    sheet['spaces'].append((
                        space_x + part_length,
                        space_y,
                        space_width - part_length,
                        space_height
                    ))

                # Space below the part
                if space_height - part_width > 0:
                    sheet['spaces'].append((
                        space_x,
                        space_y + part_width,
                        part_length,
                        space_height - part_width
                    ))

                return True

            # Try rotated orientation
            elif part_width <= space_width and part_length <= space_height:
                # Rotated part fits, place it here
                sheet['cuts'].append(((part_width, part_length, part_name), space_x, space_y))

                # Remove this space
                del sheet['spaces'][i]

                # Add new spaces (split the remaining area)
                # Space to the right of the part
                if space_width - part_width > 0:
                    sheet['spaces'].append((
                        space_x + part_width,
                        space_y,
                        space_width - part_width,
                        space_height
                    ))

                # Space below the part
                if space_height - part_length > 0:
                    sheet['spaces'].append((
                        space_x,
                        space_y + part_length,
                        part_width,
                        space_height - part_length
                    ))

                return True

        return False


class QuoteCalculator:
    def __init__(self):
        self.units: List[Unit] = []
        self.sheet_price: float = 0
        self.sheet_width: float = 2440  # Standard sheet size in mm
        self.sheet_height: float = 1220  # Standard sheet size in mm
        self.labor_rate: float = 0
        self.markup_percentage: float = 0

    def add_unit(self, unit: Unit) -> None:
        self.units.append(unit)

    def remove_unit(self, index: int) -> None:
        if 0 <= index < len(self.units):
            self.units.pop(index)

    def duplicate_unit(self, index: int) -> None:
        if 0 <= index < len(self.units):
            unit = copy.deepcopy(self.units[index])
            unit.name = f"{unit.name} (copy)"
            self.units.append(unit)

    def calculate_quote(self) -> Dict:
        # Collect all parts from all units
        all_parts = []
        for unit in self.units:
            parts = unit.get_parts()
            # Multiply parts by quantity
            for _ in range(unit.quantity):
                all_parts.extend(parts)

        # Optimize sheet usage
        optimizer = SheetOptimizer(self.sheet_width, self.sheet_height)
        sheets = optimizer.optimize(all_parts)

        # Calculate total material cost
        material_cost = len(sheets) * self.sheet_price

        # Calculate labor cost
        # Simple estimate: 2 hours per unit
        labor_hours = sum(2 * unit.quantity for unit in self.units)
        labor_cost = labor_hours * self.labor_rate

        # Calculate total cost
        subtotal = material_cost + labor_cost
        markup = subtotal * (self.markup_percentage / 100)
        total = subtotal + markup

        return {
            'units': len(self.units),
            'sheets_required': len(sheets),
            'sheets': sheets,
            'material_cost': material_cost,
            'labor_hours': labor_hours,
            'labor_cost': labor_cost,
            'subtotal': subtotal,
            'markup': markup,
            'total': total
        }

    def save_to_file(self, filename: str) -> None:
        """Save the current project to a JSON file"""
        data = {
            'units': [vars(c) for c in self.units],
            'sheet_price': self.sheet_price,
            'sheet_width': self.sheet_width,
            'sheet_height': self.sheet_height,
            'labor_rate': self.labor_rate,
            'markup_percentage': self.markup_percentage
        }

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

    def load_from_file(self, filename: str) -> None:
        """Load project from a JSON file"""
        with open(filename, 'r') as f:
            data = json.load(f)

        self.units = []
        for unit_data in data['units']:
            self.units.append(Unit(**unit_data))

        self.sheet_price = data['sheet_price']
        self.sheet_width = data['sheet_width']
        self.sheet_height = data['sheet_height']
        self.labor_rate = data['labor_rate']
        self.markup_percentage = data['markup_percentage']


class DarkTheme:
    """Theme constants for the dark UI"""
    BG_COLOR = "#2E2E2E"
    FRAME_BG = "#363636"
    TEXT_COLOR = "#E0E0E0"
    ACCENT_COLOR = "#4A6BDC"
    BUTTON_BG = "#3D3D3D"
    BUTTON_ACTIVE = "#505050"
    TABLE_BG = "#1E1E1E"
    TABLE_SELECTED = "#4A6BDC"
    ENTRY_BG = "#1E1E1E"
    ERROR_COLOR = "#DC5050"


class KitchenQuoteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Proper Job")
        self.root.geometry("1200x700")
        self.root.configure(bg=DarkTheme.BG_COLOR)

        self.calculator = QuoteCalculator()
        self.setup_styles()
        self.create_ui()

        # Track the current unit being edited
        self.current_edit_index = None
        # Define available unit types
        self.unit_types = ["Cabinet", "Drawer", "Shelving", "Pantry", "Island", "Other"]

    def setup_styles(self):
        """Configure ttk styles for the dark theme"""
        style = ttk.Style()
        style.theme_use('default')

        # Configure common elements
        style.configure('TFrame', background=DarkTheme.FRAME_BG)
        style.configure('TLabel', background=DarkTheme.FRAME_BG, foreground=DarkTheme.TEXT_COLOR)
        style.configure('TButton', background=DarkTheme.BUTTON_BG, foreground=DarkTheme.TEXT_COLOR)
        style.map('TButton',
                  background=[('active', DarkTheme.BUTTON_ACTIVE)],
                  foreground=[('active', DarkTheme.TEXT_COLOR)])

        # Table style
        style.configure('Treeview',
                        background=DarkTheme.TABLE_BG,
                        foreground=DarkTheme.TEXT_COLOR,
                        fieldbackground=DarkTheme.TABLE_BG)
        style.map('Treeview',
                  background=[('selected', DarkTheme.TABLE_SELECTED)],
                  foreground=[('selected', DarkTheme.TEXT_COLOR)])

        # Entry style
        style.configure('TEntry',
                        fieldbackground=DarkTheme.ENTRY_BG,
                        foreground=DarkTheme.TEXT_COLOR)

        # Combobox style
        style.configure('TCombobox',
                        fieldbackground=DarkTheme.ENTRY_BG,
                        foreground=DarkTheme.TEXT_COLOR,
                        background=DarkTheme.BUTTON_BG)
        style.map('TCombobox',
                  fieldbackground=[('readonly', DarkTheme.ENTRY_BG)],
                  foreground=[('readonly', DarkTheme.TEXT_COLOR)])

    def create_ui(self):
        """Create the main application UI"""
        # Main frame
        main_frame = ttk.Frame(self.root, style='TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Top section for global settings
        settings_frame = ttk.Frame(main_frame, style='TFrame')
        settings_frame.pack(fill=tk.X, padx=5, pady=5)

        # Project settings
        ttk.Label(settings_frame, text="Sheet Price (£):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.sheet_price_var = tk.DoubleVar(value=50.0)
        ttk.Entry(settings_frame, textvariable=self.sheet_price_var, width=10).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(settings_frame, text="Labor Rate (£/hr):").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.labor_rate_var = tk.DoubleVar(value=25.0)
        ttk.Entry(settings_frame, textvariable=self.labor_rate_var, width=10).grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(settings_frame, text="Markup (%):").grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        self.markup_var = tk.DoubleVar(value=20.0)
        ttk.Entry(settings_frame, textvariable=self.markup_var, width=10).grid(row=0, column=5, padx=5, pady=5)

        ttk.Label(settings_frame, text="Sheet Dimensions (mm):").grid(row=0, column=6, padx=5, pady=5, sticky=tk.W)
        self.sheet_width_var = tk.DoubleVar(value=2440)
        self.sheet_height_var = tk.DoubleVar(value=1220)
        ttk.Entry(settings_frame, textvariable=self.sheet_width_var, width=8).grid(row=0, column=7, padx=5, pady=5)
        ttk.Label(settings_frame, text="×").grid(row=0, column=8)
        ttk.Entry(settings_frame, textvariable=self.sheet_height_var, width=8).grid(row=0, column=9, padx=5, pady=5)

        # Buttons for file operations
        ttk.Button(settings_frame, text="Save Project", command=self.save_project).grid(row=0, column=10, padx=10,
                                                                                        pady=5)
        ttk.Button(settings_frame, text="Load Project", command=self.load_project).grid(row=0, column=11, padx=10,
                                                                                        pady=5)

        # Middle section with unit table and detail panel
        content_frame = ttk.Frame(main_frame, style='TFrame')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Split into unit list and detail panel
        content_frame.columnconfigure(0, weight=3)
        content_frame.columnconfigure(1, weight=0)  # This will be shown/hidden dynamically
        content_frame.rowconfigure(0, weight=1)

        # Unit list frame
        list_frame = ttk.Frame(content_frame, style='TFrame')
        list_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Unit table
        columns = ('name', 'type', 'dimensions', 'material', 'quantity')
        self.unit_table = ttk.Treeview(list_frame, columns=columns, show='headings')

        # Set column headings
        self.unit_table.heading('name', text='Unit')
        self.unit_table.heading('type', text='Type')
        self.unit_table.heading('dimensions', text='Dimensions (H×W×D mm)')
        self.unit_table.heading('material', text='Material Thickness (mm)')
        self.unit_table.heading('quantity', text='Quantity')

        # Set column widths
        self.unit_table.column('name', width=150)
        self.unit_table.column('type', width=100)
        self.unit_table.column('dimensions', width=200)
        self.unit_table.column('material', width=150)
        self.unit_table.column('quantity', width=100)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.unit_table.yview)
        self.unit_table.configure(yscroll=scrollbar.set)

        # Pack the table and scrollbar
        self.unit_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Add button frame below table
        button_frame = ttk.Frame(list_frame, style='TFrame')
        button_frame.pack(fill=tk.X, pady=5)

        ttk.Button(button_frame, text="Add Unit", command=self.add_unit).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Edit Unit", command=self.edit_unit).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Remove Unit", command=self.remove_unit).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Duplicate Unit", command=self.duplicate_unit).pack(side=tk.LEFT, padx=5)

        # Unit detail panel (initially hidden)
        self.detail_panel = ttk.Frame(content_frame, style='TFrame')

        # Bottom section for quote results
        results_frame = ttk.Frame(main_frame, style='TFrame')
        results_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(results_frame, text="Calculate Quote", command=self.update_quote).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(results_frame, text="Show Cut List", command=self.show_cut_list).pack(side=tk.LEFT, padx=5, pady=5)

        # Quote summary section
        self.quote_frame = ttk.Frame(main_frame, style='TFrame')
        self.quote_frame.pack(fill=tk.X, padx=5, pady=5)

        # Initialize the calculator with default values
        self.update_calculator_settings()

    def update_calculator_settings(self):
        """Update the calculator with the current UI settings"""
        try:
            self.calculator.sheet_price = self.sheet_price_var.get()
            self.calculator.labor_rate = self.labor_rate_var.get()
            self.calculator.markup_percentage = self.markup_var.get()
            self.calculator.sheet_width = self.sheet_width_var.get()
            self.calculator.sheet_height = self.sheet_height_var.get()
        except tk.TclError:
            # Handle invalid numeric input
            messagebox.showerror("Input Error", "Please enter valid numbers for all fields.")

    def add_unit(self):
        """Show the unit detail panel for adding a new unit"""
        self.current_edit_index = None
        self.show_detail_panel(Unit(
            name="New Unit",
            unit_type="",  # Empty type initially
            height=720,
            width=600,
            depth=570,
            material_thickness=18,
            quantity=1
        ))

    def edit_unit(self):
        """Edit the selected unit"""
        selected = self.unit_table.selection()
        if not selected:
            messagebox.showinfo("Selection Required", "Please select a unit to edit.")
            return

        # Get the index from the table item ID
        index = self.unit_table.index(selected[0])
        self.current_edit_index = index

        # Show the detail panel with the selected unit
        self.show_detail_panel(self.calculator.units[index])

    def remove_unit(self):
        """Remove the selected unit"""
        selected = self.unit_table.selection()
        if not selected:
            messagebox.showinfo("Selection Required", "Please select a unit to remove.")
            return

        index = self.unit_table.index(selected[0])
        self.calculator.remove_unit(index)
        self.refresh_unit_table()

    def duplicate_unit(self):
        """Duplicate the selected unit"""
        selected = self.unit_table.selection()
        if not selected:
            messagebox.showinfo("Selection Required", "Please select a unit to duplicate.")
            return

        index = self.unit_table.index(selected[0])
        self.calculator.duplicate_unit(index)
        self.refresh_unit_table()

    def show_detail_panel(self, unit: Unit):
        """Show the detail panel with the given unit data"""
        # Clear existing panel if it exists
        for widget in self.detail_panel.winfo_children():
            widget.destroy()

        # Configure and show the panel
        self.detail_panel.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # Add fields for unit details
        ttk.Label(self.detail_panel, text="Unit Details", font=("Arial", 12)).pack(pady=10)

        # Unit name
        name_frame = ttk.Frame(self.detail_panel, style='TFrame')
        name_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(name_frame, text="Name:").pack(side=tk.LEFT, padx=5)
        self.unit_name_var = tk.StringVar(value=unit.name)
        ttk.Entry(name_frame, textvariable=self.unit_name_var, width=25).pack(side=tk.LEFT, padx=5, fill=tk.X,
                                                                              expand=True)

        # Unit type selection
        type_frame = ttk.Frame(self.detail_panel, style='TFrame')
        type_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(type_frame, text="Unit Type:").pack(side=tk.LEFT, padx=5)
        self.unit_type_var = tk.StringVar(value=unit.unit_type)
        self.unit_type_combo = ttk.Combobox(type_frame, textvariable=self.unit_type_var,
                                            values=self.unit_types, width=20, state="readonly")
        self.unit_type_combo.pack(side=tk.LEFT, padx=5)
        self.unit_type_combo.bind("<<ComboboxSelected>>", self.on_type_selected)

        # Container for dimension inputs (initially hidden)
        self.dimension_container = ttk.Frame(self.detail_panel, style='TFrame')
        self.dimension_container.pack(fill=tk.X, padx=10, pady=5)

        # Dimensions
        dim_frame = ttk.Frame(self.dimension_container, style='TFrame')
        dim_frame.pack(fill=tk.X, padx=0, pady=5)
        ttk.Label(dim_frame, text="Dimensions (mm):").pack(side=tk.LEFT, padx=5)

        dim_inputs = ttk.Frame(dim_frame, style='TFrame')
        dim_inputs.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Height
        height_frame = ttk.Frame(dim_inputs, style='TFrame')
        height_frame.pack(fill=tk.X, pady=2)
        ttk.Label(height_frame, text="Height:").pack(side=tk.LEFT, padx=5)
        self.unit_height_var = tk.DoubleVar(value=unit.height)
        ttk.Entry(height_frame, textvariable=self.unit_height_var, width=10).pack(side=tk.LEFT, padx=5)

        # Width
        width_frame = ttk.Frame(dim_inputs, style='TFrame')
        width_frame.pack(fill=tk.X, pady=2)
        ttk.Label(width_frame, text="Width:").pack(side=tk.LEFT, padx=5)
        self.unit_width_var = tk.DoubleVar(value=unit.width)
        ttk.Entry(width_frame, textvariable=self.unit_width_var, width=10).pack(side=tk.LEFT, padx=5)

        # Depth
        depth_frame = ttk.Frame(dim_inputs, style='TFrame')
        depth_frame.pack(fill=tk.X, pady=2)
        ttk.Label(depth_frame, text="Depth:").pack(side=tk.LEFT, padx=5)
        self.unit_depth_var = tk.DoubleVar(value=unit.depth)
        ttk.Entry(depth_frame, textvariable=self.unit_depth_var, width=10).pack(side=tk.LEFT, padx=5)

        # Material thickness
        thickness_frame = ttk.Frame(self.dimension_container, style='TFrame')
        thickness_frame.pack(fill=tk.X, padx=0, pady=5)
        ttk.Label(thickness_frame, text="Material Thickness (mm):").pack(side=tk.LEFT, padx=5)
        self.unit_thickness_var = tk.DoubleVar(value=unit.material_thickness)
        ttk.Entry(thickness_frame, textvariable=self.unit_thickness_var, width=10).pack(side=tk.LEFT, padx=5)

        # Quantity
        quantity_frame = ttk.Frame(self.dimension_container, style='TFrame')
        quantity_frame.pack(fill=tk.X, padx=0, pady=5)
        ttk.Label(quantity_frame, text="Quantity:").pack(side=tk.LEFT, padx=5)
        self.unit_quantity_var = tk.IntVar(value=unit.quantity)
        ttk.Entry(quantity_frame, textvariable=self.unit_quantity_var, width=10).pack(side=tk.LEFT, padx=5)

        # Buttons
        button_frame = ttk.Frame(self.detail_panel, style='TFrame')
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Button(button_frame, text="Save", command=self.save_unit).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.hide_detail_panel).pack(side=tk.LEFT, padx=5)

        # Hide the dimension inputs initially if no type is selected
        if not unit.unit_type:
            self.dimension_container.pack_forget()

    def on_type_selected(self, event):
        """Show dimension inputs when a unit type is selected"""
        if self.unit_type_var.get():
            self.dimension_container.pack(fill=tk.X, padx=10, pady=5)
        else:
            self.dimension_container.pack_forget()

    def save_unit(self):
        """Save the unit from the detail panel"""
        try:
            # Check if a unit type is selected
            if not self.unit_type_var.get():
                messagebox.showinfo("Type Required", "Please select a unit type.")
                return

            # Create a unit from the UI fields
            unit = Unit(
                name=self.unit_name_var.get(),
                unit_type=self.unit_type_var.get(),
                height=self.unit_height_var.get(),
                width=self.unit_width_var.get(),
                depth=self.unit_depth_var.get(),
                material_thickness=self.unit_thickness_var.get(),
                quantity=self.unit_quantity_var.get()
            )

            # Add or update the unit in the calculator
            if self.current_edit_index is not None:
                self.calculator.units[self.current_edit_index] = unit
            else:
                self.calculator.add_unit(unit)

            # Hide the detail panel and refresh the table
            self.hide_detail_panel()
            self.refresh_unit_table()

        except tk.TclError:
            messagebox.showerror("Input Error", "Please enter valid numbers for all fields.")

    def hide_detail_panel(self):
        """Hide the unit detail panel"""
        self.detail_panel.grid_forget()
        self.current_edit_index = None

    def refresh_unit_table(self):
        """Refresh the unit table with current data"""
        # Clear the table
        for item in self.unit_table.get_children():
            self.unit_table.delete(item)

        # Add units to the table
        for unit in self.calculator.units:
            dimensions = f"{unit.height} × {unit.width} × {unit.depth}"
            self.unit_table.insert('', tk.END, values=(
                unit.name,
                unit.unit_type,
                dimensions,
                unit.material_thickness,
                unit.quantity
            ))

    def update_quote(self):
        """Calculate and display the quote"""
        self.update_calculator_settings()

        # Clear existing quote display
        for widget in self.quote_frame.winfo_children():
            widget.destroy()

        if not self.calculator.units:
            ttk.Label(self.quote_frame, text="Add units to generate a quote", foreground=DarkTheme.ERROR_COLOR).pack(
                pady=10)
            return

        # Calculate the quote
        quote = self.calculator.calculate_quote()

        # Display the quote
        quote_text = ttk.Frame(self.quote_frame, style='TFrame')
        quote_text.pack(fill=tk.X, padx=10, pady=10)

        # Summary section
        summary = ttk.Frame(quote_text, style='TFrame')
        summary.pack(fill=tk.X, pady=5)

        ttk.Label(summary, text="QUOTE SUMMARY", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2,
                                                                                  sticky="w", pady=5)

        ttk.Label(summary, text="Units:").grid(row=1, column=0, sticky="w", padx=5)
        ttk.Label(summary, text=str(quote['units'])).grid(row=1, column=1, sticky="w", padx=5)

        ttk.Label(summary, text="Sheets Required:").grid(row=2, column=0, sticky="w", padx=5)
        ttk.Label(summary, text=str(quote['sheets_required'])).grid(row=2, column=1, sticky="w", padx=5)

        ttk.Label(summary, text="Material Cost:").grid(row=3, column=0, sticky="w", padx=5)
        ttk.Label(summary, text=f"£{quote['material_cost']:.2f}").grid(row=3, column=1, sticky="w", padx=5)

        ttk.Label(summary, text="Labor Hours:").grid(row=4, column=0, sticky="w", padx=5)
        ttk.Label(summary, text=f"{quote['labor_hours']} hrs").grid(row=4, column=1, sticky="w", padx=5)

        ttk.Label(summary, text="Labor Cost:").grid(row=5, column=0, sticky="w", padx=5)
        ttk.Label(summary, text=f"£{quote['labor_cost']:.2f}").grid(row=5, column=1, sticky="w", padx=5)

        ttk.Label(summary, text="Subtotal:").grid(row=6, column=0, sticky="w", padx=5)
        ttk.Label(summary, text=f"£{quote['subtotal']:.2f}").grid(row=6, column=1, sticky="w", padx=5)

        ttk.Label(summary, text=f"Markup ({self.calculator.markup_percentage}%):").grid(row=7, column=0, sticky="w",
                                                                                        padx=5)
        ttk.Label(summary, text=f"£{quote['markup']:.2f}").grid(row=7, column=1, sticky="w", padx=5)

        ttk.Label(summary, text="TOTAL:", font=("Arial", 10, "bold")).grid(row=8, column=0, sticky="w", padx=5, pady=5)
        ttk.Label(summary, text=f"£{quote['total']:.2f}", font=("Arial", 10, "bold")).grid(row=8, column=1, sticky="w",
                                                                                           padx=5, pady=5)

    def show_cut_list(self):
        """Display the cut list in a new window"""
        self.update_calculator_settings()

        if not self.calculator.units:
            messagebox.showinfo("No Units", "Add units to generate a cut list.")
            return

        # Calculate the quote to get the cut list
        quote = self.calculator.calculate_quote()

        # Create a new window
        cut_list_window = tk.Toplevel(self.root)
        cut_list_window.title("Cut List")
        cut_list_window.geometry("800x600")
        cut_list_window.configure(bg=DarkTheme.BG_COLOR)

        # Main frame
        main_frame = ttk.Frame(cut_list_window, style='TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Title
        ttk.Label(main_frame, text="Cut List", font=("Arial", 14, "bold")).pack(pady=10)

        # Sheet summary
        summary_frame = ttk.Frame(main_frame, style='TFrame')
        summary_frame.pack(fill=tk.X, pady=5)

        ttk.Label(summary_frame, text=f"Total Sheets Required: {quote['sheets_required']}").pack(anchor="w")
        ttk.Label(summary_frame,
                  text=f"Sheet Size: {self.calculator.sheet_width} × {self.calculator.sheet_height} mm").pack(
            anchor="w")

        # Create a notebook for sheets
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=10)

        # Add a tab for each sheet
        for i, sheet in enumerate(quote['sheets']):
            sheet_frame = ttk.Frame(notebook, style='TFrame')
            notebook.add(sheet_frame, text=f"Sheet {i + 1}")

            # Sheet info
            info_frame = ttk.Frame(sheet_frame, style='TFrame')
            info_frame.pack(fill=tk.X, pady=5)

            ttk.Label(info_frame, text=f"Utilization: {sheet['utilization']:.1f}%").pack(anchor="w")

            # Cut list table
            columns = ('part_name', 'dimensions')
            cut_table = ttk.Treeview(sheet_frame, columns=columns, show='headings')

            cut_table.heading('part_name', text='Part Name')
            cut_table.heading('dimensions', text='Dimensions (mm)')

            cut_table.column('part_name', width=300)
            cut_table.column('dimensions', width=200)

            # Add scrollbar
            scrollbar = ttk.Scrollbar(sheet_frame, orient=tk.VERTICAL, command=cut_table.yview)
            cut_table.configure(yscroll=scrollbar.set)

            # Pack the table and scrollbar
            cut_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            # Add cuts to the table
            for part, x, y in sheet['cuts']:
                length, width, part_name = part
                cut_table.insert('', tk.END, values=(
                    part_name,
                    f"{length} × {width}"
                ))

        # Add buttons at the bottom
        button_frame = ttk.Frame(main_frame, style='TFrame')
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(button_frame, text="Print Cut List", command=lambda: self.print_cut_list(quote)).pack(side=tk.LEFT,
                                                                                                         padx=5)
        ttk.Button(button_frame, text="Close", command=cut_list_window.destroy).pack(side=tk.LEFT, padx=5)

    def print_cut_list(self, quote):
        """Print the cut list (simulated with a save dialog)"""
        filename = tk.filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Save Cut List As"
        )

        if not filename:
            return

        with open(filename, 'w') as f:
            f.write("KITCHEN CABINET CUT LIST\n")
            f.write("=======================\n\n")

            f.write(f"Sheet Size: {self.calculator.sheet_width} × {self.calculator.sheet_height} mm\n")
            f.write(f"Total Sheets Required: {quote['sheets_required']}\n\n")

            for i, sheet in enumerate(quote['sheets']):
                f.write(f"SHEET {i + 1} (Utilization: {sheet['utilization']:.1f}%)\n")
                f.write("-" * 50 + "\n")

                for part, x, y in sheet['cuts']:
                    length, width, part_name = part
                    f.write(f"{part_name}: {length} × {width} mm\n")

                f.write("\n")

            f.write("\nUnits Summary:\n")
            for unit in self.calculator.units:
                f.write(
                    f"{unit.name} ({unit.unit_type}, Qty: {unit.quantity}): {unit.height} × {unit.width} × {unit.depth} mm\n")

        messagebox.showinfo("Cut List Saved", f"Cut list has been saved to {filename}")

    def save_project(self):
        """Save the current project to a file"""
        self.update_calculator_settings()

        filename = tk.filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Project As"
        )

        if not filename:
            return

        try:
            self.calculator.save_to_file(filename)
            messagebox.showinfo("Project Saved", f"Project has been saved to {filename}")
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save project: {str(e)}")

    def load_project(self):
        """Load a project from a file"""
        filename = tk.filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Project"
        )

        if not filename:
            return

        try:
            self.calculator.load_from_file(filename)

            # Update UI with loaded values
            self.sheet_price_var.set(self.calculator.sheet_price)
            self.labor_rate_var.set(self.calculator.labor_rate)
            self.markup_var.set(self.calculator.markup_percentage)
            self.sheet_width_var.set(self.calculator.sheet_width)
            self.sheet_height_var.set(self.calculator.sheet_height)

            self.refresh_unit_table()
            messagebox.showinfo("Project Loaded", f"Project has been loaded from {filename}")
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load project: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = KitchenQuoteApp(root)
    root.mainloop()