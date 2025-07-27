"""Material configuration dialogs."""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, List, Optional
import json

from ..base import BaseDialog
from config import DarkTheme
from data.repository import DataRepository


class MaterialDialog(BaseDialog):
    """Dialog for adding/editing material."""

    def __init__(
            self,
            parent: tk.Widget,
            material_data: Optional[Dict[str, Any]] = None
    ):
        """Initialize material dialog.

        Args:
            parent: Parent widget
            material_data: Existing material data for editing
        """
        self.material_data = material_data
        self.cost_entries = []

        title = "Edit Material" if material_data else "Add Material"
        super().__init__(parent, title, width=600, height=500)

    def _create_body(self, parent: ttk.Frame) -> None:
        """Create dialog body."""
        # Material name
        name_frame = ttk.Frame(parent)
        name_frame.pack(fill=tk.X, pady=5)

        ttk.Label(name_frame, text="Material Name:", width=15).pack(side=tk.LEFT)
        self.name_var = tk.StringVar(
            value=self.material_data.get('Material', '') if self.material_data else ''
        )
        ttk.Entry(name_frame, textvariable=self.name_var, width=30).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )

        # Properties
        props_frame = ttk.LabelFrame(parent, text="Properties", padding=10)
        props_frame.pack(fill=tk.X, pady=10)

        # Create checkboxes in a grid
        self.veneer_var = tk.BooleanVar(
            value=self.material_data.get('Veneer', False) if self.material_data else False
        )
        self.hardwood_var = tk.BooleanVar(
            value=self.material_data.get('Hardwood', False) if self.material_data else False
        )
        self.carcass_var = tk.BooleanVar(
            value=self.material_data.get('Carcass', False) if self.material_data else False
        )
        self.door_var = tk.BooleanVar(
            value=self.material_data.get('Door', False) if self.material_data else False
        )
        self.face_frame_var = tk.BooleanVar(
            value=self.material_data.get('Face Frame', False) if self.material_data else False
        )

        ttk.Checkbutton(props_frame, text="Veneer", variable=self.veneer_var).grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=2
        )
        ttk.Checkbutton(props_frame, text="Hardwood", variable=self.hardwood_var).grid(
            row=0, column=1, sticky=tk.W, padx=5, pady=2
        )
        ttk.Checkbutton(props_frame, text="Carcass", variable=self.carcass_var).grid(
            row=1, column=0, sticky=tk.W, padx=5, pady=2
        )
        ttk.Checkbutton(props_frame, text="Door", variable=self.door_var).grid(
            row=1, column=1, sticky=tk.W, padx=5, pady=2
        )
        ttk.Checkbutton(props_frame, text="Face Frame", variable=self.face_frame_var).grid(
            row=2, column=0, sticky=tk.W, padx=5, pady=2
        )

        # Cost information
        cost_frame = ttk.LabelFrame(parent, text="Cost Information", padding=10)
        cost_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Cost entries container
        self.cost_container = ttk.Frame(cost_frame)
        self.cost_container.pack(fill=tk.BOTH, expand=True)

        # Headers
        header_frame = ttk.Frame(self.cost_container)
        header_frame.pack(fill=tk.X, pady=5)
        ttk.Label(header_frame, text="Thickness (mm)", width=15).pack(side=tk.LEFT, padx=5)
        ttk.Label(header_frame, text="Cost (exc. VAT)", width=15).pack(side=tk.LEFT, padx=5)
        ttk.Label(header_frame, text="", width=10).pack(side=tk.LEFT)  # For remove button

        # Add cost entries
        if self.material_data and 'Cost' in self.material_data:
            for cost_data in self.material_data['Cost']:
                self._add_cost_entry(
                    cost_data['Thickness'],
                    cost_data['Sheet Cost (exc. VAT)']
                )
        else:
            # Add one default entry
            self._add_cost_entry()

        # Add button
        ttk.Button(
            cost_frame,
            text="Add Thickness",
            command=self._add_cost_entry
        ).pack(pady=5)

    def _add_cost_entry(self, thickness: int = 18, cost: float = 0.0) -> None:
        """Add a cost entry row."""
        entry_frame = ttk.Frame(self.cost_container)
        entry_frame.pack(fill=tk.X, pady=2)

        # Thickness entry
        thickness_var = tk.IntVar(value=thickness)
        ttk.Spinbox(
            entry_frame,
            from_=3,
            to=50,
            textvariable=thickness_var,
            width=13
        ).pack(side=tk.LEFT, padx=5)

        # Cost entry
        cost_var = tk.DoubleVar(value=cost)
        ttk.Entry(
            entry_frame,
            textvariable=cost_var,
            width=13
        ).pack(side=tk.LEFT, padx=5)

        # Remove button
        remove_btn = ttk.Button(
            entry_frame,
            text="Remove",
            width=8,
            command=lambda: self._remove_cost_entry(entry_frame)
        )
        remove_btn.pack(side=tk.LEFT, padx=5)

        # Store references
        self.cost_entries.append({
            'frame': entry_frame,
            'thickness': thickness_var,
            'cost': cost_var
        })

    def _remove_cost_entry(self, frame: ttk.Frame) -> None:
        """Remove a cost entry."""
        # Find and remove from list
        self.cost_entries = [
            entry for entry in self.cost_entries
            if entry['frame'] != frame
        ]

        # Destroy frame
        frame.destroy()

    def _validate(self) -> bool:
        """Validate dialog input."""
        # Check name
        if not self.name_var.get().strip():
            messagebox.showerror("Validation Error", "Material name is required")
            return False

        # Check at least one property selected
        if not any([
            self.carcass_var.get(),
            self.door_var.get(),
            self.face_frame_var.get()
        ]):
            messagebox.showerror(
                "Validation Error",
                "Material must be usable for at least one component type"
            )
            return False

        # Check cost entries
        if not self.cost_entries:
            messagebox.showerror(
                "Validation Error",
                "At least one thickness/cost entry is required"
            )
            return False

        # Check for duplicate thicknesses
        thicknesses = [entry['thickness'].get() for entry in self.cost_entries]
        if len(thicknesses) != len(set(thicknesses)):
            messagebox.showerror(
                "Validation Error",
                "Duplicate thickness values are not allowed"
            )
            return False

        return True

    def _get_result(self) -> Dict[str, Any]:
        """Get dialog result."""
        # Build cost list
        cost_list = []
        for entry in self.cost_entries:
            cost_list.append({
                'Thickness': entry['thickness'].get(),
                'Sheet Cost (exc. VAT)': entry['cost'].get()
            })

        # Sort by thickness
        cost_list.sort(key=lambda x: x['Thickness'])

        return {
            'Material': self.name_var.get().strip(),
            'Veneer': self.veneer_var.get(),
            'Hardwood': self.hardwood_var.get(),
            'Carcass': self.carcass_var.get(),
            'Door': self.door_var.get(),
            'Face Frame': self.face_frame_var.get(),
            'Cost': cost_list
        }


class MaterialDatabaseDialog(BaseDialog):
    """Dialog for managing material database."""

    def __init__(
            self,
            parent: tk.Widget,
            materials_data: Dict[str, Any],
            repository: DataRepository
    ):
        """Initialize material database dialog.

        Args:
            parent: Parent widget
            materials_data: Current materials data
            repository: Data repository
        """
        self.materials_data = materials_data.copy()
        self.repository = repository
        self.has_changes = False

        super().__init__(parent, "Material Database", width=800, height=600)

    def _create_body(self, parent: ttk.Frame) -> None:
        """Create dialog body."""
        # Top section - VAT and additional costs
        top_frame = ttk.Frame(parent)
        top_frame.pack(fill=tk.X, pady=5)

        # VAT rate
        vat_frame = ttk.LabelFrame(top_frame, text="VAT Settings", padding=5)
        vat_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        ttk.Label(vat_frame, text="VAT Rate:").pack(side=tk.LEFT, padx=5)
        self.vat_var = tk.DoubleVar(value=self.materials_data.get('VAT', 0.2))
        ttk.Spinbox(
            vat_frame,
            from_=0,
            to=1,
            increment=0.01,
            textvariable=self.vat_var,
            width=10,
            format="%.2f"
        ).pack(side=tk.LEFT, padx=5)

        # Additional costs
        costs_frame = ttk.LabelFrame(top_frame, text="Additional Costs", padding=5)
        costs_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Veneer costs
        ttk.Label(costs_frame, text="Veneer Lacquer:").grid(row=0, column=0, sticky=tk.W, padx=2)
        self.veneer_lacquer_var = tk.DoubleVar(
            value=self.materials_data.get('Veneer Lacquer Cost', 7.5)
        )
        ttk.Entry(costs_frame, textvariable=self.veneer_lacquer_var, width=10).grid(
            row=0, column=1, padx=2
        )

        ttk.Label(costs_frame, text="Veneer Edging:").grid(row=1, column=0, sticky=tk.W, padx=2)
        self.veneer_edging_var = tk.DoubleVar(
            value=self.materials_data.get('Veneer Edging Cost', 4.0)
        )
        ttk.Entry(costs_frame, textvariable=self.veneer_edging_var, width=10).grid(
            row=1, column=1, padx=2
        )

        ttk.Label(costs_frame, text="Veneer Screw:").grid(row=2, column=0, sticky=tk.W, padx=2)
        self.veneer_screw_var = tk.DoubleVar(
            value=self.materials_data.get('Veneer Screw Cost', 3.0)
        )
        ttk.Entry(costs_frame, textvariable=self.veneer_screw_var, width=10).grid(
            row=2, column=1, padx=2
        )

        # Materials table
        table_frame = ttk.LabelFrame(parent, text="Materials", padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Create treeview
        columns = ('material', 'veneer', 'hardwood', 'carcass', 'door', 'face_frame', 'thicknesses')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)

        # Configure columns
        self.tree.heading('material', text='Material')
        self.tree.heading('veneer', text='Veneer')
        self.tree.heading('hardwood', text='Hardwood')
        self.tree.heading('carcass', text='Carcass')
        self.tree.heading('door', text='Door')
        self.tree.heading('face_frame', text='Face Frame')
        self.tree.heading('thicknesses', text='Thicknesses')

        # Column widths
        self.tree.column('material', width=150)
        self.tree.column('veneer', width=60)
        self.tree.column('hardwood', width=70)
        self.tree.column('carcass', width=60)
        self.tree.column('door', width=50)
        self.tree.column('face_frame', width=80)
        self.tree.column('thicknesses', width=200)

        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Pack
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Button frame
        btn_frame = ttk.Frame(table_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="Add Material", command=self._add_material).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(btn_frame, text="Edit Material", command=self._edit_material).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(btn_frame, text="Delete Material", command=self._delete_material).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(btn_frame, text="Import", command=self._import_materials).pack(
            side=tk.LEFT, padx=20
        )
        ttk.Button(btn_frame, text="Export", command=self._export_materials).pack(
            side=tk.LEFT, padx=2
        )

        # Load materials
        self._refresh_table()

    def _refresh_table(self) -> None:
        """Refresh the materials table."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Add materials
        for material in self.materials_data.get('Materials', []):
            # Format thicknesses
            thicknesses = [
                str(cost['Thickness'])
                for cost in material.get('Cost', [])
            ]
            thickness_str = ', '.join(thicknesses) + ' mm'

            values = (
                material['Material'],
                '✓' if material.get('Veneer', False) else '',
                '✓' if material.get('Hardwood', False) else '',
                '✓' if material.get('Carcass', False) else '',
                '✓' if material.get('Door', False) else '',
                '✓' if material.get('Face Frame', False) else '',
                thickness_str
            )

            self.tree.insert('', tk.END, values=values)

    def _add_material(self) -> None:
        """Add a new material."""
        dialog = MaterialDialog(self.dialog)
        result = dialog.show()

        if result:
            self.materials_data['Materials'].append(result)
            self._refresh_table()
            self.has_changes = True

    def _edit_material(self) -> None:
        """Edit selected material."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a material to edit")
            return

        index = self.tree.index(selection[0])
        material = self.materials_data['Materials'][index]

        dialog = MaterialDialog(self.dialog, material)
        result = dialog.show()

        if result:
            self.materials_data['Materials'][index] = result
            self._refresh_table()
            self.has_changes = True

    def _delete_material(self) -> None:
        """Delete selected material."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a material to delete")
            return

        index = self.tree.index(selection[0])
        material = self.materials_data['Materials'][index]

        if messagebox.askyesno(
                "Confirm Delete",
                f"Delete material '{material['Material']}'?"
        ):
            del self.materials_data['Materials'][index]
            self._refresh_table()
            self.has_changes = True

    def _import_materials(self) -> None:
        """Import materials from file."""
        from tkinter import filedialog

        filename = filedialog.askopenfilename(
            title="Import Materials",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)

                # Validate structure
                if isinstance(data, list) and data:
                    data = data[0]

                if 'Materials' in data:
                    # Ask how to import
                    choice = messagebox.askyesnocancel(
                        "Import Options",
                        "Replace existing materials?\n\n"
                        "Yes = Replace all\n"
                        "No = Append to existing\n"
                        "Cancel = Cancel import"
                    )

                    if choice is None:
                        return
                    elif choice:
                        # Replace
                        self.materials_data = data
                    else:
                        # Append
                        self.materials_data['Materials'].extend(data['Materials'])

                    self._refresh_table()
                    self.has_changes = True
                else:
                    messagebox.showerror(
                        "Import Error",
                        "Invalid material data format"
                    )

            except Exception as e:
                messagebox.showerror(
                    "Import Error",
                    f"Failed to import materials: {str(e)}"
                )

    def _export_materials(self) -> None:
        """Export materials to file."""
        from tkinter import filedialog

        filename = filedialog.asksaveasfilename(
            title="Export Materials",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump([self.materials_data], f, indent=2)

                messagebox.showinfo(
                    "Export Complete",
                    f"Materials exported to {filename}"
                )

            except Exception as e:
                messagebox.showerror(
                    "Export Error",
                    f"Failed to export materials: {str(e)}"
                )

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
            # Update VAT and costs
            self.materials_data['VAT'] = self.vat_var.get()
            self.materials_data['Veneer Lacquer Cost'] = self.veneer_lacquer_var.get()
            self.materials_data['Veneer Edging Cost'] = self.veneer_edging_var.get()
            self.materials_data['Veneer Screw Cost'] = self.veneer_screw_var.get()

            # Save to file
            try:
                self.repository.save_materials(self.materials_data)
                self.result = True
                self.dialog.destroy()
            except Exception as e:
                messagebox.showerror(
                    "Save Error",
                    f"Failed to save materials: {str(e)}"
                )
        else:
            self.result = False
            self.dialog.destroy()
