"""Runner configuration dialogs."""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, List, Optional
import json

from ..base import BaseDialog
from src.data.repository import DataRepository


class RunnerDialog(BaseDialog):
    """Dialog for adding/editing runner."""

    def __init__(
            self,
            parent: tk.Widget,
            runner_data: Optional[Dict[str, Any]] = None
    ):
        """Initialize runner dialog.

        Args:
            parent: Parent widget
            runner_data: Existing runner data for editing
        """
        self.runner_data = runner_data

        title = "Edit Runner" if runner_data else "Add Runner"
        super().__init__(parent, title, width=400, height=250)

    def _create_body(self, parent: ttk.Frame) -> None:
        """Create dialog body."""
        # Length
        length_frame = ttk.Frame(parent)
        length_frame.pack(fill=tk.X, pady=5)

        ttk.Label(length_frame, text="Length (mm):", width=15).pack(side=tk.LEFT)
        self.length_var = tk.IntVar(
            value=self.runner_data.get('Length', 500) if self.runner_data else 500
        )
        ttk.Spinbox(
            length_frame,
            from_=200,
            to=800,
            increment=50,
            textvariable=self.length_var,
            width=15
        ).pack(side=tk.LEFT)

        # Capacity
        capacity_frame = ttk.Frame(parent)
        capacity_frame.pack(fill=tk.X, pady=5)

        ttk.Label(capacity_frame, text="Capacity (kg):", width=15).pack(side=tk.LEFT)
        self.capacity_var = tk.IntVar(
            value=self.runner_data.get('Capacity', 30) if self.runner_data else 30
        )
        ttk.Combobox(
            capacity_frame,
            textvariable=self.capacity_var,
            values=[20, 30, 40, 50, 70],
            state="readonly",
            width=13
        ).pack(side=tk.LEFT)

        # Price
        price_frame = ttk.Frame(parent)
        price_frame.pack(fill=tk.X, pady=5)

        ttk.Label(price_frame, text="Price (£):", width=15).pack(side=tk.LEFT)
        self.price_var = tk.DoubleVar(
            value=self.runner_data.get('Price', 0.0) if self.runner_data else 0.0
        )
        ttk.Entry(price_frame, textvariable=self.price_var, width=15).pack(side=tk.LEFT)

    def _validate(self) -> bool:
        """Validate dialog input."""
        if self.price_var.get() < 0:
            messagebox.showerror("Validation Error", "Price cannot be negative")
            return False

        return True

    def _get_result(self) -> Dict[str, Any]:
        """Get dialog result."""
        return {
            'Length': self.length_var.get(),
            'Capacity': self.capacity_var.get(),
            'Price': self.price_var.get()
        }


class RunnerDatabaseDialog(BaseDialog):
    """Dialog for managing runner database."""

    def __init__(
            self,
            parent: tk.Widget,
            runners_data: List[Dict[str, Any]],
            repository: DataRepository
    ):
        """Initialize runner database dialog.

        Args:
            parent: Parent widget
            runners_data: Current runners data
            repository: Data repository
        """
        self.runners_data = runners_data.copy()
        self.repository = repository
        self.has_changes = False
        self.current_brand_index = None

        super().__init__(parent, "Runner Database", width=900, height=600)

    def _create_body(self, parent: ttk.Frame) -> None:
        """Create dialog body."""
        # Main paned window
        paned = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Left panel - Brands
        brands_frame = ttk.LabelFrame(paned, text="Brands", padding=10)
        paned.add(brands_frame, weight=4)

        # Brand list
        self.brand_listbox = tk.Listbox(brands_frame, height=20)
        self.brand_listbox.pack(fill=tk.BOTH, expand=True)

        # Brand buttons
        brand_btn_frame = ttk.Frame(brands_frame)
        brand_btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(brand_btn_frame, text="Delete", command=self._delete_brand).pack(
            side=tk.BOTTOM, padx=2
        )
        ttk.Button(brand_btn_frame, text="Rename", command=self._rename_brand).pack(
            side=tk.BOTTOM, padx=2
        )
        ttk.Button(brand_btn_frame, text="Add Brand", command=self._add_brand).pack(
            side=tk.BOTTOM, padx=2
        )

        # Right panel - Runners
        runners_frame = ttk.LabelFrame(paned, text="Runners", padding=10)
        paned.add(runners_frame, weight=2)

        # Runners table
        columns = ('length', 'capacity', 'price')
        self.runner_tree = ttk.Treeview(
            runners_frame,
            columns=columns,
            show='headings',
            height=18
        )

        # Configure columns
        self.runner_tree.heading('length', text='Length (mm)', anchor='w')
        self.runner_tree.heading('capacity', text='Capacity (kg)', anchor='w')
        self.runner_tree.heading('price', text='Price (£)', anchor='w')

        self.runner_tree.column('length', width=100)
        self.runner_tree.column('capacity', width=100)
        self.runner_tree.column('price', width=100)

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            runners_frame,
            orient=tk.VERTICAL,
            command=self.runner_tree.yview
        )
        self.runner_tree.configure(yscrollcommand=scrollbar.set)

        # Pack
        self.runner_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Runner buttons
        runner_btn_frame = ttk.Frame(runners_frame)
        runner_btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(runner_btn_frame, text="Add Runner", command=self._add_runner).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(runner_btn_frame, text="Edit Runner", command=self._edit_runner).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(runner_btn_frame, text="Delete Runner", command=self._delete_runner).pack(
            side=tk.LEFT, padx=2
        )
        # ttk.Button(runner_btn_frame, text="Import", command=self._import_runners).pack(
        #     side=tk.LEFT, padx=20
        # )
        # ttk.Button(runner_btn_frame, text="Export", command=self._export_runners).pack(
        #     side=tk.LEFT, padx=2
        # )

        # Bind brand selection
        self.brand_listbox.bind('<<ListboxSelect>>', self._on_brand_selected)

        # Load brands
        self._refresh_brands()

    def _refresh_brands(self) -> None:
        """Refresh brand list."""
        self.brand_listbox.delete(0, tk.END)

        for brand in self.runners_data:
            self.brand_listbox.insert(tk.END, brand['Name'])

        # Select first brand if exists
        if self.runners_data:
            self.brand_listbox.selection_set(0)
            self._on_brand_selected()

    def _on_brand_selected(self, event=None) -> None:
        """Handle brand selection."""
        selection = self.brand_listbox.curselection()
        if selection:
            self.current_brand_index = selection[0]
            self._refresh_runners()

    def _refresh_runners(self) -> None:
        """Refresh runners table."""
        # Clear existing items
        for item in self.runner_tree.get_children():
            self.runner_tree.delete(item)

        if self.current_brand_index is None:
            return

        # Get current brand
        brand = self.runners_data[self.current_brand_index]

        # Add runners
        for runner in brand['Runners']:

            values = (
                runner['Length'],
                runner['Capacity'],
                f"£{runner['Price']:.2f}"
            )

            self.runner_tree.insert('', tk.END, values=values)

    def _add_brand(self) -> None:
        """Add a new brand."""
        from tkinter import simpledialog

        name = simpledialog.askstring(
            "Add Brand",
            "Enter brand name:",
            parent=self.dialog
        )

        if name:
            # Check for duplicates
            if any(brand['Name'] == name for brand in self.runners_data):
                messagebox.showerror("Error", "Brand name already exists")
                return

            new_brand = {
                'Name': name,
                'Runners': []
            }

            self.runners_data.append(new_brand)
            self._refresh_brands()

            # Select new brand
            self.brand_listbox.selection_clear(0, tk.END)
            self.brand_listbox.selection_set(len(self.runners_data) - 1)
            self._on_brand_selected()

            self.has_changes = True

    def _rename_brand(self) -> None:
        """Rename selected brand."""
        if self.current_brand_index is None:
            messagebox.showinfo("No Selection", "Please select a brand to rename")
            return

        from tkinter import simpledialog

        current_name = self.runners_data[self.current_brand_index]['Name']
        new_name = simpledialog.askstring(
            "Rename Brand",
            "Enter new name:",
            initialvalue=current_name,
            parent=self.dialog
        )

        if new_name and new_name != current_name:
            # Check for duplicates
            if any(brand['Name'] == new_name for brand in self.runners_data):
                messagebox.showerror("Error", "Brand name already exists")
                return

            self.runners_data[self.current_brand_index]['Name'] = new_name
            self._refresh_brands()
            self.has_changes = True

    def _delete_brand(self) -> None:
        """Delete selected brand."""
        if self.current_brand_index is None:
            messagebox.showinfo("No Selection", "Please select a brand to delete")
            return

        brand_name = self.runners_data[self.current_brand_index]['Name']

        if messagebox.askyesno(
            "Confirm Delete",
            f"Delete brand '{brand_name}' and all its runners?"
        ):
            del self.runners_data[self.current_brand_index]
            self.current_brand_index = None
            self._refresh_brands()
            self.has_changes = True

    def _add_runner(self) -> None:
        """Add a new runner to selected brand."""
        if self.current_brand_index is None:
            messagebox.showinfo("No Selection", "Please select a brand first")
            return

        dialog = RunnerDialog(self.dialog)
        result = dialog.show()

        if result:
            self.runners_data[self.current_brand_index]['Runners'].append(result)
            self._refresh_runners()
            self.has_changes = True

    def _edit_runner(self) -> None:
        """Edit selected runner."""
        selection = self.runner_tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a runner to edit")
            return

        runner_index = self.runner_tree.index(selection[0])
        brand = self.runners_data[self.current_brand_index]
        runner_data = brand['Runners'][runner_index]

        dialog = RunnerDialog(self.dialog, runner_data)
        result = dialog.show()

        if result:
            brand['Runners'][runner_index] = result
            self._refresh_runners()
            self.has_changes = True

    def _delete_runner(self) -> None:
        """Delete selected runner."""
        selection = self.runner_tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a runner to delete")
            return

        if messagebox.askyesno("Confirm Delete", "Delete this runner?"):
            runner_index = self.runner_tree.index(selection[0])
            del self.runners_data[self.current_brand_index]['Runners'][runner_index]
            self._refresh_runners()
            self.has_changes = True

    def _import_runners(self) -> None:
        """Import runners from file."""
        from tkinter import filedialog

        filename = filedialog.askopenfilename(
            title="Import Runners",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)

                if isinstance(data, list):
                    # Ask how to import
                    choice = messagebox.askyesnocancel(
                        "Import Options",
                        "Replace existing runners?\n\n"
                        "Yes = Replace all\n"
                        "No = Append to existing\n"
                        "Cancel = Cancel import"
                    )

                    if choice is None:
                        return
                    elif choice:
                        # Replace
                        self.runners_data = data
                    else:
                        # Append
                        self.runners_data.extend(data)

                    self.current_brand_index = None
                    self._refresh_brands()
                    self.has_changes = True
                else:
                    messagebox.showerror(
                        "Import Error",
                        "Invalid runner data format"
                    )

            except Exception as e:
                messagebox.showerror(
                    "Import Error",
                    f"Failed to import runners: {str(e)}"
                )

    def _export_runners(self) -> None:
        """Export runners to file."""
        from tkinter import filedialog

        filename = filedialog.asksaveasfilename(
            title="Export Runners",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(self.runners_data, f, indent=2)

                messagebox.showinfo(
                    "Export Complete",
                    f"Runners exported to {filename}"
                )

            except Exception as e:
                messagebox.showerror(
                    "Export Error",
                    f"Failed to export runners: {str(e)}"
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
            # Save to file
            try:
                self.repository.save_runners(self.runners_data)
                self.result = True
                self.dialog.destroy()
            except Exception as e:
                messagebox.showerror(
                    "Save Error",
                    f"Failed to save runners: {str(e)}"
                )
        else:
            self.result = False
            self.dialog.destroy()