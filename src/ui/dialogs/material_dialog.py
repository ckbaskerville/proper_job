"""Material configuration dialogs."""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, List, Optional
import json

from src.ui.dialogs.base_dialog import BaseDialog
from src.config import DarkTheme
from src.data.repository import DataRepository


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

        # Headers
        header_frame = ttk.Frame(cost_frame)
        header_frame.pack(fill=tk.X, pady=5)
        ttk.Label(header_frame, text="Thickness (mm)", width=15).pack(side=tk.LEFT, padx=5)
        ttk.Label(header_frame, text="Cost (exc. VAT)", width=15).pack(side=tk.LEFT, padx=5)
        ttk.Label(header_frame, text="", width=10).pack(side=tk.LEFT)  # For remove button

        # Scrollable frame for cost entries
        cost_scroll_frame = ttk.Frame(cost_frame)
        cost_scroll_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Canvas and scrollbar for cost entries
        canvas = tk.Canvas(cost_scroll_frame, height=150)
        scrollbar_cost = ttk.Scrollbar(cost_scroll_frame, orient="vertical", command=canvas.yview)
        self.cost_container = ttk.Frame(canvas)

        self.cost_container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.cost_container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar_cost.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar_cost.pack(side="right", fill="y")

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

        # Add button - fixed at bottom of cost frame
        add_btn_frame = ttk.Frame(cost_frame)
        add_btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(
            add_btn_frame,
            text="Add Thickness",
            command=self._add_cost_entry
        ).pack()

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

        super().__init__(parent, "Material Database", width=800, height=700)

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
        ttk.Label(costs_frame, text="Veneer Lacquer (£):").grid(row=0, column=0, sticky=tk.W, padx=2)
        self.veneer_lacquer_var = tk.DoubleVar(
            value=self.materials_data.get('Veneer Lacquer Cost', 7.5)
        )
        ttk.Entry(costs_frame, textvariable=self.veneer_lacquer_var, width=10).grid(
            row=0, column=1, padx=2
        )

        ttk.Label(costs_frame, text="Veneer Edging (£):").grid(row=1, column=0, sticky=tk.W, padx=2)
        self.veneer_edging_var = tk.DoubleVar(
            value=self.materials_data.get('Veneer Edging Cost', 4.0)
        )
        ttk.Entry(costs_frame, textvariable=self.veneer_edging_var, width=10).grid(
            row=1, column=1, padx=2
        )

        ttk.Label(costs_frame, text="Veneer Screw (£):").grid(row=2, column=0, sticky=tk.W, padx=2)
        self.veneer_screw_var = tk.DoubleVar(
            value=self.materials_data.get('Veneer Screw Cost', 3.0)
        )
        ttk.Entry(costs_frame, textvariable=self.veneer_screw_var, width=10).grid(
            row=2, column=1, padx=2
        )

        # Materials table section - this will expand to fill available space
        table_frame = ttk.LabelFrame(parent, text="Materials", padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Button frame - MOVED TO TOP of materials section
        btn_frame = ttk.Frame(table_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(btn_frame, text="Add Material", command=self._add_material).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(btn_frame, text="Edit Material", command=self._edit_material).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(btn_frame, text="Delete Material", command=self._delete_material).pack(
            side=tk.LEFT, padx=2
        )

        # Separator
        ttk.Separator(btn_frame, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=10)

        ttk.Button(btn_frame, text="Import", command=self._import_materials).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(btn_frame, text="Export", command=self._export_materials).pack(
            side=tk.LEFT, padx=2
        )

        # Treeview frame with scrollbar
        tree_frame = ttk.Frame(table_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        # Create treeview
        columns = ('material', 'veneer', 'hardwood', 'carcass', 'door', 'face_frame', 'thicknesses')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings')

        # Configure columns
        self.tree.heading('material', text='Material', anchor='w')
        self.tree.heading('veneer', text='Veneer', anchor='w')
        self.tree.heading('hardwood', text='Hardwood', anchor='w')
        self.tree.heading('carcass', text='Carcass', anchor='w')
        self.tree.heading('door', text='Door', anchor='w')
        self.tree.heading('face_frame', text='Face Frame', anchor='w')
        self.tree.heading('thicknesses', text='Thicknesses', anchor='w')

        # Column widths
        self.tree.column('material', width=150)
        self.tree.column('veneer', width=60)
        self.tree.column('hardwood', width=70)
        self.tree.column('carcass', width=60)
        self.tree.column('door', width=50)
        self.tree.column('face_frame', width=80)
        self.tree.column('thicknesses', width=200)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Grid layout for tree and scrollbars
        self.tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')

        # Configure grid weights
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

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
            if 'Materials' not in self.materials_data:
                self.materials_data['Materials'] = []
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
                        if 'Materials' not in self.materials_data:
                            self.materials_data['Materials'] = []
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
        # Always update the values
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