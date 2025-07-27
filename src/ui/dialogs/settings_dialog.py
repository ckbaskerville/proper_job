import tkinter as tk
from tkinter import ttk, messagebox
import json
import copy

from .material_dialog import MaterialDialog
from .runner_dialog import RunnerDialog


class SettingsDialog:
    def __init__(self, parent, settings_manager, theme_manager, materials_dict, labour_cost_dict, runners_dict):
        self.parent = parent
        self.settings_manager = settings_manager
        self.theme_manager = theme_manager
        self.theme = self.theme_manager.get_theme("dark")
        self.dialog = None

        # Load current data
        self.materials_data = copy.deepcopy(materials_dict)
        self.labour_data = copy.deepcopy(labour_cost_dict)
        self.runners_data = copy.deepcopy(runners_dict)

        # Track changes
        self.has_changes = False

        self.create_dialog()

    def create_dialog(self):
        """Create the main settings dialog window"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Settings - Edit Configuration")
        self.dialog.geometry("1000x700")
        self.dialog.configure(bg=self.theme.BG_COLOR)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # Make dialog modal
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Main frame
        main_frame = ttk.Frame(self.dialog, style='TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Title
        title_label = ttk.Label(main_frame, text="Configuration Settings",
                                font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 10))

        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Create tabs
        self.create_materials_tab()
        self.create_labour_tab()
        self.create_runners_tab()

        # Button frame
        button_frame = ttk.Frame(main_frame, style='TFrame')
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(button_frame, text="Save All Changes",
                   command=self.save_all_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Reset All",
                   command=self.reset_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel",
                   command=self.on_closing).pack(side=tk.RIGHT, padx=5)

    def create_materials_tab(self):
        """Create the sheet materials configuration tab"""
        materials_frame = ttk.Frame(self.notebook, style='TFrame')
        self.notebook.add(materials_frame, text="Sheet Materials")

        # Create canvas for scrolling
        canvas = tk.Canvas(materials_frame, bg=self.theme.BG_COLOR, highlightthickness=0)
        scrollbar = ttk.Scrollbar(materials_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style='TFrame')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # VAT section
        vat_frame = ttk.LabelFrame(scrollable_frame, text="VAT Settings", padding=10)
        vat_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(vat_frame, text="VAT Rate:").grid(row=0, column=0, sticky="w", padx=5)
        self.vat_var = tk.DoubleVar(value=self.materials_data.get("VAT", 0.2))
        ttk.Entry(vat_frame, textvariable=self.vat_var, width=10).grid(row=0, column=1, padx=5)

        # Additional costs section
        costs_frame = ttk.LabelFrame(scrollable_frame, text="Additional Costs", padding=10)
        costs_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(costs_frame, text="Veneer Lacquer Cost:").grid(row=0, column=0, sticky="w", padx=5)
        self.veneer_lacquer_var = tk.DoubleVar(value=self.materials_data.get("Veneer Lacquer Cost", 7.5))
        ttk.Entry(costs_frame, textvariable=self.veneer_lacquer_var, width=10).grid(row=0, column=1, padx=5)

        ttk.Label(costs_frame, text="Veneer Edging Cost:").grid(row=1, column=0, sticky="w", padx=5)
        self.veneer_edging_var = tk.DoubleVar(value=self.materials_data.get("Veneer Edging Cost", 4.0))
        ttk.Entry(costs_frame, textvariable=self.veneer_edging_var, width=10).grid(row=1, column=1, padx=5)

        ttk.Label(costs_frame, text="Veneer Screw Cost:").grid(row=2, column=0, sticky="w", padx=5)
        self.veneer_screw_var = tk.DoubleVar(value=self.materials_data.get("Veneer Screw Cost", 3.0))
        ttk.Entry(costs_frame, textvariable=self.veneer_screw_var, width=10).grid(row=2, column=1, padx=5)

        # Materials section
        materials_section = ttk.LabelFrame(scrollable_frame, text="Materials", padding=10)
        materials_section.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Materials table
        columns = ('material', 'veneer', 'hardwood', 'carcass', 'door', 'face_frame')
        self.materials_tree = ttk.Treeview(materials_section, columns=columns, show='headings', height=8)

        # Configure columns
        self.materials_tree.heading('material', text='Material Name')
        self.materials_tree.heading('veneer', text='Veneer')
        self.materials_tree.heading('hardwood', text='Hardwood')
        self.materials_tree.heading('carcass', text='Carcass')
        self.materials_tree.heading('door', text='Door')
        self.materials_tree.heading('face_frame', text='Face Frame')

        self.materials_tree.column('material', width=150)
        self.materials_tree.column('veneer', width=80)
        self.materials_tree.column('hardwood', width=80)
        self.materials_tree.column('carcass', width=80)
        self.materials_tree.column('door', width=80)
        self.materials_tree.column('face_frame', width=80)

        # Add scrollbar for materials tree
        materials_scrollbar = ttk.Scrollbar(materials_section, orient=tk.VERTICAL, command=self.materials_tree.yview)
        self.materials_tree.configure(yscroll=materials_scrollbar.set)

        self.materials_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        materials_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Materials buttons
        materials_buttons = ttk.Frame(materials_section)
        materials_buttons.pack(fill=tk.X, pady=5)

        ttk.Button(materials_buttons, text="Add Material",
                   command=self.add_material).pack(side=tk.LEFT, padx=5)
        ttk.Button(materials_buttons, text="Edit Material",
                   command=self.edit_material).pack(side=tk.LEFT, padx=5)
        ttk.Button(materials_buttons, text="Delete Material",
                   command=self.delete_material).pack(side=tk.LEFT, padx=5)

        # Load materials data
        self.refresh_materials_tree()

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind mousewheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<MouseWheel>", _on_mousewheel)

    def create_labour_tab(self):
        """Create the labour costs configuration tab"""
        labour_frame = ttk.Frame(self.notebook, style='TFrame')
        self.notebook.add(labour_frame, text="Labour Costs")

        # Create canvas for scrolling
        canvas = tk.Canvas(labour_frame, bg=self.theme.BG_COLOR, highlightthickness=0)
        scrollbar = ttk.Scrollbar(labour_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style='TFrame')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Carcass labour costs
        carcass_frame = ttk.LabelFrame(scrollable_frame, text="Carcass Labour Costs (hours)", padding=10)
        carcass_frame.pack(fill=tk.X, padx=5, pady=5)

        self.carcass_labour_vars = {}
        row = 0
        for material_type, hours in self.labour_data["Carcass"].items():
            ttk.Label(carcass_frame, text=f"{material_type}:").grid(row=row, column=0, sticky="w", padx=5, pady=2)
            var = tk.DoubleVar(value=hours)
            self.carcass_labour_vars[material_type] = var
            ttk.Entry(carcass_frame, textvariable=var, width=10).grid(row=row, column=1, padx=5, pady=2)
            row += 1

        # Drawers labour costs
        drawers_frame = ttk.LabelFrame(scrollable_frame, text="Drawers Labour Costs (hours)", padding=10)
        drawers_frame.pack(fill=tk.X, padx=5, pady=5)

        self.drawers_labour_vars = {}
        row = 0
        for material_type, hours in self.labour_data["Drawers"].items():
            ttk.Label(drawers_frame, text=f"{material_type}:").grid(row=row, column=0, sticky="w", padx=5, pady=2)
            var = tk.DoubleVar(value=hours)
            self.drawers_labour_vars[material_type] = var
            ttk.Entry(drawers_frame, textvariable=var, width=10).grid(row=row, column=1, padx=5, pady=2)
            row += 1

        # Doors labour costs
        doors_frame = ttk.LabelFrame(scrollable_frame, text="Doors Labour Costs", padding=10)
        doors_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Doors table
        doors_columns = ('material', 'type', 'per_door', 'moulding', 'cut_handle')
        self.doors_tree = ttk.Treeview(doors_frame, columns=doors_columns, show='headings', height=8)

        self.doors_tree.heading('material', text='Material')
        self.doors_tree.heading('type', text='Type')
        self.doors_tree.heading('per_door', text='Per Door (hrs)')
        self.doors_tree.heading('moulding', text='Moulding (hrs)')
        self.doors_tree.heading('cut_handle', text='Cut Handle (hrs)')

        self.doors_tree.column('material', width=120)
        self.doors_tree.column('type', width=100)
        self.doors_tree.column('per_door', width=100)
        self.doors_tree.column('moulding', width=100)
        self.doors_tree.column('cut_handle', width=120)

        doors_scrollbar = ttk.Scrollbar(doors_frame, orient=tk.VERTICAL, command=self.doors_tree.yview)
        self.doors_tree.configure(yscroll=doors_scrollbar.set)

        self.doors_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        doors_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Doors buttons
        doors_buttons = ttk.Frame(doors_frame)
        doors_buttons.pack(fill=tk.X, pady=5)

        ttk.Button(doors_buttons, text="Add Door Type",
                   command=self.add_door_type).pack(side=tk.LEFT, padx=5)
        ttk.Button(doors_buttons, text="Edit Door Type",
                   command=self.edit_door_type).pack(side=tk.LEFT, padx=5)
        ttk.Button(doors_buttons, text="Delete Door Type",
                   command=self.delete_door_type).pack(side=tk.LEFT, padx=5)

        # Face Frames labour costs
        face_frames_frame = ttk.LabelFrame(scrollable_frame, text="Face Frames Labour Costs", padding=10)
        face_frames_frame.pack(fill=tk.X, padx=5, pady=5)

        self.face_frame_vars = {}
        row = 0
        for material_type, costs in self.labour_data["Face Frames"].items():
            material_frame = ttk.LabelFrame(face_frames_frame, text=material_type, padding=5)
            material_frame.grid(row=row // 2, column=row % 2, sticky="ew", padx=5, pady=5)

            per_frame_var = tk.DoubleVar(value=costs["Per Frame (hours)"])
            moulding_var = tk.DoubleVar(value=costs["Moulding"])

            ttk.Label(material_frame, text="Per Frame (hrs):").grid(row=0, column=0, sticky="w", padx=2)
            ttk.Entry(material_frame, textvariable=per_frame_var, width=8).grid(row=0, column=1, padx=2)

            ttk.Label(material_frame, text="Moulding (hrs):").grid(row=1, column=0, sticky="w", padx=2)
            ttk.Entry(material_frame, textvariable=moulding_var, width=8).grid(row=1, column=1, padx=2)

            self.face_frame_vars[material_type] = {
                "per_frame": per_frame_var,
                "moulding": moulding_var
            }
            row += 1

        # Configure grid weights
        face_frames_frame.columnconfigure(0, weight=1)
        face_frames_frame.columnconfigure(1, weight=1)

        self.refresh_doors_tree()

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind mousewheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<MouseWheel>", _on_mousewheel)

    def create_runners_tab(self):
        """Create the runners configuration tab"""
        runners_frame = ttk.Frame(self.notebook, style='TFrame')
        self.notebook.add(runners_frame, text="Drawer Runners")

        # Create canvas for scrolling
        canvas = tk.Canvas(runners_frame, bg=self.theme.BG_COLOR, highlightthickness=0)
        scrollbar = ttk.Scrollbar(runners_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style='TFrame')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Runner brands section
        brands_frame = ttk.LabelFrame(scrollable_frame, text="Runner Brands", padding=10)
        brands_frame.pack(fill=tk.X, padx=5, pady=5)

        # Brand selection
        ttk.Label(brands_frame, text="Select Brand:").pack(side=tk.LEFT, padx=5)
        self.selected_brand_var = tk.StringVar()
        self.brand_combo = ttk.Combobox(brands_frame, textvariable=self.selected_brand_var,
                                        values=[brand["Name"] for brand in self.runners_data])
        self.brand_combo.pack(side=tk.LEFT, padx=5)
        self.brand_combo.bind("<<ComboboxSelected>>", self.on_brand_selected)

        ttk.Button(brands_frame, text="Add Brand",
                   command=self.add_runner_brand).pack(side=tk.LEFT, padx=5)
        ttk.Button(brands_frame, text="Delete Brand",
                   command=self.delete_runner_brand).pack(side=tk.LEFT, padx=5)

        # Runners table
        runners_section = ttk.LabelFrame(scrollable_frame, text="Runners for Selected Brand", padding=10)
        runners_section.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        runners_columns = ('length', 'capacity', 'price')
        self.runners_tree = ttk.Treeview(runners_section, columns=runners_columns, show='headings', height=12)

        self.runners_tree.heading('length', text='Length (mm)')
        self.runners_tree.heading('capacity', text='Capacity (kg)')
        self.runners_tree.heading('price', text='Price (£)')

        self.runners_tree.column('length', width=120)
        self.runners_tree.column('capacity', width=120)
        self.runners_tree.column('price', width=120)

        runners_scrollbar = ttk.Scrollbar(runners_section, orient=tk.VERTICAL, command=self.runners_tree.yview)
        self.runners_tree.configure(yscroll=runners_scrollbar.set)

        self.runners_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        runners_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Runners buttons
        runners_buttons = ttk.Frame(runners_section)
        runners_buttons.pack(fill=tk.X, pady=5)

        ttk.Button(runners_buttons, text="Add Runner",
                   command=self.add_runner).pack(side=tk.LEFT, padx=5)
        ttk.Button(runners_buttons, text="Edit Runner",
                   command=self.edit_runner).pack(side=tk.LEFT, padx=5)
        ttk.Button(runners_buttons, text="Delete Runner",
                   command=self.delete_runner).pack(side=tk.LEFT, padx=5)

        # Set default brand selection
        if self.runners_data:
            self.selected_brand_var.set(self.runners_data[0]["Name"])
            self.refresh_runners_tree()

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind mousewheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<MouseWheel>", _on_mousewheel)

    def refresh_materials_tree(self):
        """Refresh the materials tree view"""
        # Clear existing items
        for item in self.materials_tree.get_children():
            self.materials_tree.delete(item)

        # Add materials
        for material in self.materials_data["Materials"]:
            values = (
                material["Material"],
                "✓" if material["Veneer"] else "",
                "✓" if material["Hardwood"] else "",
                "✓" if material["Carcass"] else "",
                "✓" if material["Door"] else "",
                "✓" if material["Face Frame"] else ""
            )
            self.materials_tree.insert('', tk.END, values=values)

    def refresh_doors_tree(self):
        """Refresh the doors tree view"""
        # Clear existing items
        for item in self.doors_tree.get_children():
            self.doors_tree.delete(item)

        # Add door types
        for door in self.labour_data["Doors"]:
            values = (
                door["Material"],
                door["Type"],
                door["Per Door (hours)"],
                door["Moulding"],
                door["Cut Handle"]
            )
            self.doors_tree.insert('', tk.END, values=values)

    def refresh_runners_tree(self):
        """Refresh the runners tree view for selected brand"""
        # Clear existing items
        for item in self.runners_tree.get_children():
            self.runners_tree.delete(item)

        brand_name = self.selected_brand_var.get()
        if not brand_name:
            return

        # Find the brand data
        brand_data = None
        for brand in self.runners_data:
            if brand["Name"] == brand_name:
                brand_data = brand
                break

        if brand_data:
            for runner in brand_data["Runners"]:
                values = (
                    runner["Length"],
                    runner["Capacity"],
                    f"{runner['Price']:.2f}"
                )
                self.runners_tree.insert('', tk.END, values=values)

    def on_brand_selected(self, event=None):
        """Handle brand selection change"""
        self.refresh_runners_tree()

    # Material management methods
    def add_material(self):
        """Add a new material"""
        dialog = MaterialDialog(self.dialog, "Add Material")
        if dialog.result:
            self.materials_data["Materials"].append(dialog.result)
            self.refresh_materials_tree()
            self.has_changes = True

    def edit_material(self):
        """Edit selected material"""
        selected = self.materials_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a material to edit.")
            return

        # Get selected material index
        index = self.materials_tree.index(selected[0])
        material_data = self.materials_data["Materials"][index]

        dialog = MaterialDialog(self.dialog, "Edit Material", material_data)
        if dialog.result:
            self.materials_data["Materials"][index] = dialog.result
            self.refresh_materials_tree()
            self.has_changes = True

    def delete_material(self):
        """Delete selected material"""
        selected = self.materials_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a material to delete.")
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this material?"):
            index = self.materials_tree.index(selected[0])
            del self.materials_data["Materials"][index]
            self.refresh_materials_tree()
            self.has_changes = True

    # Door type management methods
    def add_door_type(self):
        """Add a new door type"""
        dialog = DoorTypeDialog(self.dialog, "Add Door Type")
        if dialog.result:
            self.labour_data["Doors"].append(dialog.result)
            self.refresh_doors_tree()
            self.has_changes = True

    def edit_door_type(self):
        """Edit selected door type"""
        selected = self.doors_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a door type to edit.")
            return

        index = self.doors_tree.index(selected[0])
        door_data = self.labour_data["Doors"][index]

        dialog = DoorTypeDialog(self.dialog, "Edit Door Type", door_data)
        if dialog.result:
            self.labour_data["Doors"][index] = dialog.result
            self.refresh_doors_tree()
            self.has_changes = True

    def delete_door_type(self):
        """Delete selected door type"""
        selected = self.doors_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a door type to delete.")
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this door type?"):
            index = self.doors_tree.index(selected[0])
            del self.labour_data["Doors"][index]
            self.refresh_doors_tree()
            self.has_changes = True

    # Runner management methods
    def add_runner_brand(self):
        """Add a new runner brand"""
        name = tk.simpledialog.askstring("Add Brand", "Enter brand name:")
        if name:
            new_brand = {"Name": name, "Runners": []}
            self.runners_data.append(new_brand)
            self.brand_combo['values'] = [brand["Name"] for brand in self.runners_data]
            self.selected_brand_var.set(name)
            self.refresh_runners_tree()
            self.has_changes = True

    def delete_runner_brand(self):
        """Delete selected runner brand"""
        brand_name = self.selected_brand_var.get()
        if not brand_name:
            messagebox.showwarning("No Selection", "Please select a brand to delete.")
            return

        if messagebox.askyesno("Confirm Delete",
                               f"Are you sure you want to delete brand '{brand_name}' and all its runners?"):
            self.runners_data = [brand for brand in self.runners_data if brand["Name"] != brand_name]
            self.brand_combo['values'] = [brand["Name"] for brand in self.runners_data]
            if self.runners_data:
                self.selected_brand_var.set(self.runners_data[0]["Name"])
                self.refresh_runners_tree()
            else:
                self.selected_brand_var.set("")
                self.refresh_runners_tree()
            self.has_changes = True

    def add_runner(self):
        """Add a new runner to selected brand"""
        brand_name = self.selected_brand_var.get()
        if not brand_name:
            messagebox.showwarning("No Brand", "Please select a brand first.")
            return

        dialog = RunnerDialog(self.dialog, "Add Runner")
        if dialog.result:
            # Find the brand and add runner
            for brand in self.runners_data:
                if brand["Name"] == brand_name:
                    brand["Runners"].append(dialog.result)
                    break
            self.refresh_runners_tree()
            self.has_changes = True

    def edit_runner(self):
        """Edit selected runner"""
        selected = self.runners_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a runner to edit.")
            return

        brand_name = self.selected_brand_var.get()
        if not brand_name:
            return

        # Find brand data
        brand_data = None
        for brand in self.runners_data:
            if brand["Name"] == brand_name:
                brand_data = brand
                break

        if brand_data:
            index = self.runners_tree.index(selected[0])
            runner_data = brand_data["Runners"][index]

            dialog = RunnerDialog(self.dialog, "Edit Runner", runner_data)
            if dialog.result:
                brand_data["Runners"][index] = dialog.result
                self.refresh_runners_tree()
                self.has_changes = True

    def delete_runner(self):
        """Delete selected runner"""
        selected = self.runners_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a runner to delete.")
            return

        brand_name = self.selected_brand_var.get()
        if not brand_name:
            return

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this runner?"):
            # Find brand data
            for brand in self.runners_data:
                if brand["Name"] == brand_name:
                    index = self.runners_tree.index(selected[0])
                    del brand["Runners"][index]
                    break
            self.refresh_runners_tree()
            self.has_changes = True

    def save_all_changes(self):
        """Save all changes to JSON files and update app"""
        try:
            # Update materials data with UI values
            self.materials_data["VAT"] = self.vat_var.get()
            self.materials_data["Veneer Lacquer Cost"] = self.veneer_lacquer_var.get()
            self.materials_data["Veneer Edging Cost"] = self.veneer_edging_var.get()
            self.materials_data["Veneer Screw Cost"] = self.veneer_screw_var.get()

            # Update labour data with UI values
            for material_type, var in self.carcass_labour_vars.items():
                self.labour_data["Carcass"][material_type] = var.get()

            for material_type, var in self.drawers_labour_vars.items():
                self.labour_data["Drawers"][material_type] = var.get()

            for material_type, vars_dict in self.face_frame_vars.items():
                self.labour_data["Face Frames"][material_type]["Per Frame (hours)"] = vars_dict["per_frame"].get()
                self.labour_data["Face Frames"][material_type]["Moulding"] = vars_dict["moulding"].get()

            # Save to files
            with open(self.settings_manager.MATERIALS_PATH, 'w') as f:
                json.dump([self.materials_data], f, indent=2)

            with open(self.settings_manager.LABOUR_PATH, 'w') as f:
                json.dump(self.labour_data, f, indent=2)

            with open(self.settings_manager.RUNNERS_PATH, 'w') as f:
                json.dump(self.runners_data, f, indent=2)

            # Update app instance data
            self.settings_manager.materials_dict = self.materials_data
            self.settings_manager.labour_cost_dict = self.labour_data
            self.settings_manager.runners_dict = self.runners_data

            # Recreate calculator with new data
            self.settings_manager.calculator = self.settings_manager.QuoteCalculator(self.settings_manager.labour_cost_dict, self.settings_manager.materials_dict)

            # Update sheet prices in calculator
            for material in self.materials_data["Materials"]:
                for thickness in material["Cost"]:
                    self.settings_manager.calculator.set_sheet_price(
                        material["Material"],
                        thickness["Thickness"],
                        thickness["Sheet Cost (exc. VAT)"] * (1 + self.materials_data["VAT"])
                    )

            self.has_changes = False
            messagebox.showinfo("Success", "All settings have been saved successfully!")
            self.dialog.destroy()

        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save settings: {str(e)}")

    def reset_all(self):
        """Reset all changes"""
        if messagebox.askyesno("Confirm Reset", "Are you sure you want to reset all changes?"):
            # Reload original data
            self.materials_data = copy.deepcopy(self.settings_manager.materials_dict)
            self.labour_data = copy.deepcopy([self.settings_manager.labour_cost_dict])
            self.runners_data = copy.deepcopy(self.settings_manager.runners_dict)

            # Refresh all UI elements
            self.vat_var.set(self.materials_data.get("VAT", 0.2))
            self.veneer_lacquer_var.set(self.materials_data.get("Veneer Lacquer Cost", 7.5))
            self.veneer_edging_var.set(self.materials_data.get("Veneer Edging Cost", 4.0))
            self.veneer_screw_var.set(self.materials_data.get("Veneer Screw Cost", 3.0))

            # Reset labour vars
            for material_type, var in self.carcass_labour_vars.items():
                var.set(self.labour_data["Carcass"][material_type])

            for material_type, var in self.drawers_labour_vars.items():
                var.set(self.labour_data["Drawers"][material_type])

            for material_type, vars_dict in self.face_frame_vars.items():
                vars_dict["per_frame"].set(self.labour_data["Face Frames"][material_type]["Per Frame (hours)"])
                vars_dict["moulding"].set(self.labour_data["Face Frames"][material_type]["Moulding"])

            # Refresh trees
            self.refresh_materials_tree()
            self.refresh_doors_tree()

            # Reset brand combo
            self.brand_combo['values'] = [brand["Name"] for brand in self.runners_data]
            if self.runners_data:
                self.selected_brand_var.set(self.runners_data[0]["Name"])
            self.refresh_runners_tree()

            self.has_changes = False

    def on_closing(self):
        """Handle dialog closing"""
        if self.has_changes:
            result = messagebox.askyesnocancel("Unsaved Changes",
                                               "You have unsaved changes. Do you want to save them before closing?")
            if result is True:  # Yes - save
                self.save_all_changes()
                return
            elif result is False:  # No - don't save
                self.dialog.destroy()
                return
            # Cancel - do nothing
        else:
            self.dialog.destroy()
