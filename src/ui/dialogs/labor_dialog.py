"""Labor configuration dialogs."""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Optional, List
import json

from ..base import BaseDialog
from src.data.repository import DataRepository


class LaborDialog(BaseDialog):
    """Dialog for editing labor costs."""

    def __init__(
            self,
            parent: tk.Widget,
            component_type: str,
            labor_data: Optional[Dict[str, Any]] = None
    ):
        """Initialize labor dialog.

        Args:
            parent: Parent widget
            component_type: Type of component (Carcass, Drawers, Doors, Face Frames)
            labor_data: Existing labor data for editing
        """
        self.component_type = component_type
        self.labor_data = labor_data or {}

        title = f"Edit {component_type} Labor Costs"
        super().__init__(parent, title, width=500, height=400)

    def _create_body(self, parent: ttk.Frame) -> None:
        """Create dialog body."""
        if self.component_type in ["Carcass", "Drawers"]:
            self._create_simple_labor_form(parent)
        elif self.component_type == "Doors":
            self._create_doors_labor_form(parent)
        elif self.component_type == "Face Frames":
            self._create_face_frames_labor_form(parent)

    def _create_simple_labor_form(self, parent: ttk.Frame) -> None:
        """Create form for simple labor costs (Carcass/Drawers)."""
        ttk.Label(
            parent,
            text=f"Labor hours required for {self.component_type}:",
            font=('Arial', 11, 'bold')
        ).pack(pady=10)

        # Create input fields for each material type
        self.labor_vars = {}

        materials = ["Veneer", "Laminate", "Melamine", "MDF", "Hardwood"]

        input_frame = ttk.Frame(parent)
        input_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        for i, material in enumerate(materials):
            ttk.Label(input_frame, text=f"{material}:").grid(
                row=i, column=0, sticky=tk.W, padx=5, pady=5
            )

            var = tk.DoubleVar(value=self.labor_data.get(material, 0.0))
            self.labor_vars[material] = var

            entry = ttk.Entry(input_frame, textvariable=var, width=10)
            entry.grid(row=i, column=1, padx=5, pady=5)

            ttk.Label(input_frame, text="hours").grid(
                row=i, column=2, sticky=tk.W, padx=5, pady=5
            )

    def _create_doors_labor_form(self, parent: ttk.Frame) -> None:
        """Create form for doors labor costs."""
        ttk.Label(
            parent,
            text="Door Type Labor Configuration",
            font=('Arial', 11, 'bold')
        ).pack(pady=10)


        # Material
        config_frame = ttk.Frame(parent)
        config_frame.pack(fill=tk.X, padx=20, pady=5)

        ttk.Label(config_frame, text="Material:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.material_var = tk.StringVar(value=self.labor_data.get('Material', ''))
        material_combo = ttk.Combobox(
            config_frame,
            textvariable=self.material_var,
            values=["Sprayed MDF", "Hardwood", "Veneer", "Laminate", "Melamine", "MDF"],
            width=20
        )
        material_combo.grid(row=0, column=1, padx=5)

        # Type
        ttk.Label(config_frame, text="Type:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.type_var = tk.StringVar(value=self.labor_data.get('Type', ''))
        type_combo = ttk.Combobox(
            config_frame,
            textvariable=self.type_var,
            values=["Shaker", "Flat"],
            width=20
        )
        type_combo.grid(row=1, column=1, padx=5)

        # Labor hours
        hours_frame = ttk.LabelFrame(parent, text="Labor Hours", padding=10)
        hours_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(hours_frame, text="Per Door (hours):").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.per_door_var = tk.DoubleVar(value=self.labor_data.get('Per Door (hours)', 0.0))
        ttk.Entry(hours_frame, textvariable=self.per_door_var, width=10).grid(row=0, column=1, padx=5)

        ttk.Label(hours_frame, text="Moulding (hours):").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.moulding_var = tk.DoubleVar(value=self.labor_data.get('Moulding', 0.0))
        ttk.Entry(hours_frame, textvariable=self.moulding_var, width=10).grid(row=1, column=1, padx=5)

        ttk.Label(hours_frame, text="Cut Handle (hours):").grid(row=2, column=0, sticky=tk.W, padx=5)
        self.cut_handle_var = tk.DoubleVar(value=self.labor_data.get('Cut Handle', 0.0))
        ttk.Entry(hours_frame, textvariable=self.cut_handle_var, width=10).grid(row=2, column=1, padx=5)

    def _create_face_frames_labor_form(self, parent: ttk.Frame) -> None:
        """Create form for face frames labor costs."""
        ttk.Label(
            parent,
            text="Face Frame Labor Configuration",
            font=('Arial', 11, 'bold')
        ).pack(pady=10)

        # Material type selection
        material_frame = ttk.Frame(parent)
        material_frame.pack(fill=tk.X, padx=20, pady=5)

        ttk.Label(material_frame, text="Material Type:").pack(side=tk.LEFT, padx=5)
        self.material_type_var = tk.StringVar(value="Sprayed")
        material_combo = ttk.Combobox(
            material_frame,
            textvariable=self.material_type_var,
            values=["Sprayed", "Hardwood", "MDF"],
            width=20
        )
        material_combo.pack(side=tk.LEFT, padx=5)

        # Labor hours
        hours_frame = ttk.LabelFrame(parent, text="Labor Hours", padding=10)
        hours_frame.pack(fill=tk.X, padx=20, pady=10)

        # Get current values if editing
        current_data = {}
        if isinstance(self.labor_data, dict) and self.material_type_var.get() in self.labor_data:
            current_data = self.labor_data[self.material_type_var.get()]

        ttk.Label(hours_frame, text="Per Frame (hours):").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.per_frame_var = tk.DoubleVar(value=current_data.get('Per Frame (hours)', 0.0))
        ttk.Entry(hours_frame, textvariable=self.per_frame_var, width=10).grid(row=0, column=1, padx=5)

        ttk.Label(hours_frame, text="Moulding (hours):").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.frame_moulding_var = tk.DoubleVar(value=current_data.get('Moulding', 0.0))
        ttk.Entry(hours_frame, textvariable=self.frame_moulding_var, width=10).grid(row=1, column=1, padx=5)

    def _validate(self) -> bool:
        """Validate dialog input."""
        if self.component_type in ["Carcass", "Drawers"]:
            for material, var in self.labor_vars.items():
                if var.get() < 0:
                    messagebox.showerror("Validation Error", f"{material} hours cannot be negative")
                    return False

        elif self.component_type == "Doors":
            if not self.material_var.get() or not self.type_var.get():
                messagebox.showerror("Validation Error", "Please select both material and type")
                return False
            if any(v.get() < 0 for v in [self.per_door_var, self.moulding_var, self.cut_handle_var]):
                messagebox.showerror("Validation Error", "Hours cannot be negative")
                return False

        elif self.component_type == "Face Frames":
            if any(v.get() < 0 for v in [self.per_frame_var, self.frame_moulding_var]):
                messagebox.showerror("Validation Error", "Hours cannot be negative")
                return False

        return True

    def _get_result(self) -> Dict[str, Any]:
        """Get dialog result."""
        if self.component_type in ["Carcass", "Drawers"]:
            return {material: var.get() for material, var in self.labor_vars.items()}

        elif self.component_type == "Doors":
            return {
                'Material': self.material_var.get(),
                'Type': self.type_var.get(),
                'Per Door (hours)': self.per_door_var.get(),
                'Moulding': self.moulding_var.get(),
                'Cut Handle': self.cut_handle_var.get()
            }

        elif self.component_type == "Face Frames":
            return {
                self.material_type_var.get(): {
                    'Per Frame (hours)': self.per_frame_var.get(),
                    'Moulding': self.frame_moulding_var.get()
                }
            }


class LaborDatabaseDialog(BaseDialog):
    """Dialog for managing labor cost database."""

    def __init__(
            self,
            parent: tk.Widget,
            labor_data: Dict[str, Any],
            repository: DataRepository
    ):
        """Initialize labor database dialog.

        Args:
            parent: Parent widget
            labor_data: Current labor data
            repository: Data repository
        """
        self.labor_data = labor_data.copy()
        self.repository = repository
        self.has_changes = False

        super().__init__(parent, "Labour Cost Database", width=900, height=600)

    def _create_body(self, parent: ttk.Frame) -> None:
        """Create dialog body."""
        # Create notebook for different component types
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True, pady=10)

        # Carcass tab
        carcass_frame = ttk.Frame(notebook)
        notebook.add(carcass_frame, text="Carcass")
        self._create_carcass_tab(carcass_frame)

        # Drawers tab
        drawers_frame = ttk.Frame(notebook)
        notebook.add(drawers_frame, text="Drawers")
        self._create_drawers_tab(drawers_frame)

        # Doors tab
        doors_frame = ttk.Frame(notebook)
        notebook.add(doors_frame, text="Doors")
        self._create_doors_tab(doors_frame)

        # Face Frames tab
        face_frames_frame = ttk.Frame(notebook)
        notebook.add(face_frames_frame, text="Face Frames")
        self._create_face_frames_tab(face_frames_frame)

        # Settings tab
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text="Settings")
        self._create_settings_tab(settings_frame)

    def _create_carcass_tab(self, parent: ttk.Frame) -> None:
        """Create carcass labor costs tab."""
        ttk.Label(
            parent,
            text="Labor hours required for carcass construction by material type",
            font=('Arial', 11)
        ).pack(pady=10)

        # Create frame for inputs
        input_frame = ttk.Frame(parent)
        input_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.carcass_vars = {}

        for i, (material, hours) in enumerate(self.labor_data.get('Carcass', {}).items()):
            ttk.Label(input_frame, text=f"{material}:", width=15).grid(
                row=i, column=0, sticky=tk.W, padx=10, pady=5
            )

            var = tk.DoubleVar(value=hours)
            self.carcass_vars[material] = var

            ttk.Entry(input_frame, textvariable=var, width=10).grid(
                row=i, column=1, padx=5, pady=5
            )

            ttk.Label(input_frame, text="hours").grid(
                row=i, column=2, sticky=tk.W, padx=5, pady=5
            )

        # Info label
        info_frame = ttk.Frame(parent)
        info_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(
            info_frame,
            text="Note: Additional time for shelves will be calculated automatically (0.25 hours per shelf)",
            font=('Arial', 9, 'italic')
        ).pack(anchor=tk.W)

    def _create_drawers_tab(self, parent: ttk.Frame) -> None:
        """Create drawers labor costs tab."""
        ttk.Label(
            parent,
            text="Labor hours required for drawer construction by material type",
            font=('Arial', 11)
        ).pack(pady=10)

        # Create frame for inputs
        input_frame = ttk.Frame(parent)
        input_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.drawers_vars = {}

        for i, (material, hours) in enumerate(self.labor_data.get('Drawers', {}).items()):
            ttk.Label(input_frame, text=f"{material}:", width=15).grid(
                row=i, column=0, sticky=tk.W, padx=10, pady=5
            )

            var = tk.DoubleVar(value=hours)
            self.drawers_vars[material] = var

            ttk.Entry(input_frame, textvariable=var, width=10).grid(
                row=i, column=1, padx=5, pady=5
            )

            ttk.Label(input_frame, text="hours per drawer").grid(
                row=i, column=2, sticky=tk.W, padx=5, pady=5
            )

    def _create_doors_tab(self, parent: ttk.Frame) -> None:
        """Create doors labor costs tab."""
        # Controls
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(
            control_frame,
            text="Add Door Type",
            command=self._add_door_type
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            control_frame,
            text="Edit Selected",
            command=self._edit_door_type
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            control_frame,
            text="Delete Selected",
            command=self._delete_door_type
        ).pack(side=tk.LEFT, padx=5)

        # Doors table
        columns = ('material', 'type', 'per_door', 'moulding', 'cut_handle')
        self.doors_tree = ttk.Treeview(
            parent,
            columns=columns,
            show='headings',
            height=15
        )

        # Configure columns
        self.doors_tree.heading('material', text='Material')
        self.doors_tree.heading('type', text='Type')
        self.doors_tree.heading('per_door', text='Per Door (hrs)')
        self.doors_tree.heading('moulding', text='Moulding (hrs)')
        self.doors_tree.heading('cut_handle', text='Cut Handle (hrs)')

        self.doors_tree.column('material', width=150)
        self.doors_tree.column('type', width=120)
        self.doors_tree.column('per_door', width=120)
        self.doors_tree.column('moulding', width=120)
        self.doors_tree.column('cut_handle', width=120)

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            parent,
            orient=tk.VERTICAL,
            command=self.doors_tree.yview
        )
        self.doors_tree.configure(yscrollcommand=scrollbar.set)

        self.doors_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10))

        # Populate doors
        self._refresh_doors_tree()

    def _create_face_frames_tab(self, parent: ttk.Frame) -> None:
        """Create face frames labor costs tab."""
        ttk.Label(
            parent,
            text="Labor hours required for face frame construction",
            font=('Arial', 11)
        ).pack(pady=10)

        # Create frames for each material type
        self.face_frame_vars = {}

        for material_type, costs in self.labor_data.get('Face Frames', {}).items():
            material_frame = ttk.LabelFrame(parent, text=material_type, padding=10)
            material_frame.pack(fill=tk.X, padx=20, pady=10)

            per_frame_var = tk.DoubleVar(value=costs.get('Per Frame (hours)', 0.0))
            moulding_var = tk.DoubleVar(value=costs.get('Moulding', 0.0))

            ttk.Label(material_frame, text="Per Frame (hours):").grid(
                row=0, column=0, sticky=tk.W, padx=5, pady=5
            )
            ttk.Entry(material_frame, textvariable=per_frame_var, width=10).grid(
                row=0, column=1, padx=5, pady=5
            )

            ttk.Label(material_frame, text="Moulding (additional hours):").grid(
                row=1, column=0, sticky=tk.W, padx=5, pady=5
            )
            ttk.Entry(material_frame, textvariable=moulding_var, width=10).grid(
                row=1, column=1, padx=5, pady=5
            )

            self.face_frame_vars[material_type] = {
                'per_frame': per_frame_var,
                'moulding': moulding_var
            }

    def _create_settings_tab(self, parent: ttk.Frame) -> None:
        """Create general settings tab."""
        # Labor rate
        rate_frame = ttk.LabelFrame(parent, text="Default Labor Rate", padding=10)
        rate_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(rate_frame, text="Hourly Rate (£):").pack(side=tk.LEFT, padx=5)
        self.labor_rate_var = tk.DoubleVar(value=40.0)  # Default value
        ttk.Entry(rate_frame, textvariable=self.labor_rate_var, width=10).pack(side=tk.LEFT, padx=5)

        # Markup
        markup_frame = ttk.LabelFrame(parent, text="Default Markup", padding=10)
        markup_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(markup_frame, text="Markup Percentage (%):").pack(side=tk.LEFT, padx=5)
        self.markup_var = tk.DoubleVar(value=20.0)  # Default value
        ttk.Entry(markup_frame, textvariable=self.markup_var, width=10).pack(side=tk.LEFT, padx=5)

        # Import/Export
        io_frame = ttk.LabelFrame(parent, text="Import/Export", padding=10)
        io_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Button(
            io_frame,
            text="Import Labor Costs",
            command=self._import_labor_costs
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            io_frame,
            text="Export Labor Costs",
            command=self._export_labor_costs
        ).pack(side=tk.LEFT, padx=5)

    def _refresh_doors_tree(self) -> None:
        """Refresh doors tree view."""
        # Clear existing items
        for item in self.doors_tree.get_children():
            self.doors_tree.delete(item)

        # Add door types
        for door in self.labor_data.get('Doors', []):
            values = (
                door['Material'],
                door['Type'],
                door['Per Door (hours)'],
                door['Moulding'],
                door['Cut Handle']
            )
            self.doors_tree.insert('', tk.END, values=values)

    def _add_door_type(self) -> None:
        """Add a new door type."""
        dialog = LaborDialog(self.dialog, "Doors")
        result = dialog.show()

        if result:
            if 'Doors' not in self.labor_data:
                self.labor_data['Doors'] = []
            self.labor_data['Doors'].append(result)
            self._refresh_doors_tree()
            self.has_changes = True

    def _edit_door_type(self) -> None:
        """Edit selected door type."""
        selection = self.doors_tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a door type to edit")
            return

        index = self.doors_tree.index(selection[0])
        door_data = self.labor_data['Doors'][index]

        dialog = LaborDialog(self.dialog, "Doors", door_data)
        result = dialog.show()

        if result:
            self.labor_data['Doors'][index] = result
            self._refresh_doors_tree()
            self.has_changes = True

    def _delete_door_type(self) -> None:
        """Delete selected door type."""
        selection = self.doors_tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a door type to delete")
            return

        if messagebox.askyesno("Confirm Delete", "Delete this door type?"):
            index = self.doors_tree.index(selection[0])
            del self.labor_data['Doors'][index]
            self._refresh_doors_tree()
            self.has_changes = True

    def _import_labor_costs(self) -> None:
        """Import labor costs from file."""
        from tkinter import filedialog

        filename = filedialog.askopenfilename(
            title="Import Labor Costs",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)

                # Validate structure
                if isinstance(data, list) and data:
                    data = data[0]

                if all(key in data for key in ['Carcass', 'Drawers', 'Doors', 'Face Frames']):
                    self.labor_data = data
                    self._refresh_all_tabs()
                    self.has_changes = True
                    messagebox.showinfo("Success", "Labor costs imported successfully")
                else:
                    messagebox.showerror("Import Error", "Invalid labor cost data format")

            except Exception as e:
                messagebox.showerror(
                    "Import Error",
                    f"Failed to import labor costs: {str(e)}"
                )

    def _export_labor_costs(self) -> None:
        """Export labor costs to file."""
        from tkinter import filedialog

        filename = filedialog.asksaveasfilename(
            title="Export Labor Costs",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filename:
            try:
                # Update data from UI before export
                self._update_data_from_ui()

                with open(filename, 'w') as f:
                    json.dump([self.labor_data], f, indent=2)

                messagebox.showinfo(
                    "Export Complete",
                    f"Labor costs exported to {filename}"
                )

            except Exception as e:
                messagebox.showerror(
                    "Export Error",
                    f"Failed to export labor costs: {str(e)}"
                )

    def _refresh_all_tabs(self) -> None:
        """Refresh all tab data from labor_data."""
        # Update carcass vars
        for material, var in self.carcass_vars.items():
            var.set(self.labor_data.get('Carcass', {}).get(material, 0.0))

        # Update drawer vars
        for material, var in self.drawers_vars.items():
            var.set(self.labor_data.get('Drawers', {}).get(material, 0.0))

        # Update face frame vars
        for material_type, vars_dict in self.face_frame_vars.items():
            data = self.labor_data.get('Face Frames', {}).get(material_type, {})
            vars_dict['per_frame'].set(data.get('Per Frame (hours)', 0.0))
            vars_dict['moulding'].set(data.get('Moulding', 0.0))

        # Refresh doors tree
        self._refresh_doors_tree()

    def _update_data_from_ui(self) -> None:
        """Update labor_data from UI values."""
        # Update carcass
        for material, var in self.carcass_vars.items():
            self.labor_data['Carcass'][material] = var.get()

        # Update drawers
        for material, var in self.drawers_vars.items():
            self.labor_data['Drawers'][material] = var.get()

        # Update face frames
        for material_type, vars_dict in self.face_frame_vars.items():
            self.labor_data['Face Frames'][material_type] = {
                'Per Frame (hours)': vars_dict['per_frame'].get(),
                'Moulding': vars_dict['moulding'].get()
            }

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
            # Update data from UI
            self._update_data_from_ui()

            # Save to file
            try:
                self.repository.save_labor_costs(self.labor_data)
                self.result = True
                self.dialog.destroy()
            except Exception as e:
                messagebox.showerror(
                    "Save Error",
                    f"Failed to save labor costs: {str(e)}"
                )
        else:
            self.result = False
            self.dialog.destroy()