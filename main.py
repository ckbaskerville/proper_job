import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from visualisation import SheetVisualizer
from proper_job_dataclasses import Carcass, Cabinet, Drawer, Doors, FaceFrame
import json
from quote_calculator import QuoteCalculator

RUNNERS_PATH = r"resources/runners.json"
MATERIALS_PATH = r"resources/sheet_material.json"
LABOUR_PATH = r"resources/labour_costs.json"

def read_resources():
    def read_resource(path: str):
        with open(path, "r") as f:
            return json.load(f)

    runners_dict = read_resource(RUNNERS_PATH)
    materials_dict = read_resource(MATERIALS_PATH)[0]
    labour_costs_dict = read_resource(LABOUR_PATH)[0]

    return runners_dict, materials_dict, labour_costs_dict

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
        self.runners_dict, self.materials_dict, self.labour_cost_dict = read_resources()
        self.calculator = QuoteCalculator(self.labour_cost_dict, self.materials_dict)
        self.setup_styles()
        self.create_ui()

        # Track the current unit being edited
        self.current_edit_index = None
        # Define available unit types
        self.unit_types = ["Cabinet"]

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

    def get_carcass_materials(self):
        return [material["Material"] for material in self.materials_dict["Materials"] if material["Carcass"]]

    def get_door_materials(self):
        return [material["Material"] for material in self.materials_dict["Materials"] if material["Door"]]

    def get_face_frame_materials(self):
        return [material["Material"] for material in self.materials_dict["Materials"] if material["Face Frame"]]

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
        self.labor_rate_var = tk.DoubleVar(value=40.0)
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
        columns = ('name', 'dimensions', 'material', 'quantity')
        self.unit_table = ttk.Treeview(list_frame, columns=columns, show='headings')

        # Set column headings
        self.unit_table.heading('name', text='Unit')
        self.unit_table.heading('dimensions', text='Dimensions (H×W×D mm)')
        self.unit_table.heading('material', text='Material Thickness (mm)')
        self.unit_table.heading('quantity', text='Quantity')

        # Set column widths
        self.unit_table.column('name', width=150)
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

    def visualise_sheets(self, optimiser, parts, sheets):
        # Create visualizations
        print("\n" + "=" * 50)
        print("CREATING VISUALIZATIONS")
        print("=" * 50)

        # Create visualizer
        visualizer = SheetVisualizer(optimiser.sheet_width, optimiser.sheet_height)

        # Show overview of all sheets
        print("\nShowing overview of all sheets...")
        visualizer.visualize_all_sheets(sheets, parts)

        # Show detailed view of each sheet
        print("\nShowing detailed view of each sheet...")
        for sheet_idx, sheet in enumerate(sheets):
            visualizer.visualize_sheet(sheet, sheet_idx + 1, parts)

        # Create technical cutting diagram
        print("\nCreating technical cutting diagram...")
        visualizer.create_cutting_diagram(sheets, parts)

        print("\nVisualization complete!")

    def update_calculator_settings(self):
        """Update the calculator with the current UI settings"""
        try:
            for material in self.materials_dict["Materials"]:
                for thickness in material["Cost"]:
                    self.calculator.set_sheet_price(material["Material"],
                                                    thickness["Thickness"],
                                                    (thickness["Sheet Cost (exc. VAT)"] * (1+self.materials_dict["VAT"])))
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
        self.show_detail_panel(self.create_default_cabinet())

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

    def create_runners_list(self, model):
        for runner_model in self.runners_dict:
            if runner_model["Name"] == model:
                return runner_model["Runners"]

    def show_detail_panel(self, cabinet: Cabinet):
        """Show the detail panel with the given unit data"""
        # Clear existing panel if it exists
        for widget in self.detail_panel.winfo_children():
            widget.destroy()

        carcass = cabinet.carcass

        # Configure and show the panel
        self.detail_panel.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # Create a canvas with scrollbar for the detail panel
        self.detail_canvas = tk.Canvas(self.detail_panel, highlightthickness=0)
        self.detail_scrollbar = ttk.Scrollbar(self.detail_panel, orient="vertical", command=self.detail_canvas.yview)
        self.detail_scrollable_frame = ttk.Frame(self.detail_canvas)

        # Configure scrolling
        self.detail_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.detail_canvas.configure(scrollregion=self.detail_canvas.bbox("all"))
        )

        # Create window in canvas
        self.detail_canvas.create_window((0, 0), window=self.detail_scrollable_frame, anchor="nw")
        self.detail_canvas.configure(yscrollcommand=self.detail_scrollbar.set)

        # Pack canvas and scrollbar
        self.detail_canvas.pack(side="left", fill="both", expand=True)
        self.detail_scrollbar.pack(side="right", fill="y")

        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            self.detail_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.detail_canvas.bind("<MouseWheel>", _on_mousewheel)  # Windows
        self.detail_canvas.bind("<Button-4>", lambda e: self.detail_canvas.yview_scroll(-1, "units"))  # Linux
        self.detail_canvas.bind("<Button-5>", lambda e: self.detail_canvas.yview_scroll(1, "units"))  # Linux

        # Main title
        ttk.Label(self.detail_scrollable_frame, text="Cabinet Details", font=("Arial", 14, "bold")).pack(pady=10)

        # Unit name
        name_frame = ttk.Frame(self.detail_scrollable_frame, style='TFrame')
        name_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(name_frame, text="Cabinet Name:").pack(side=tk.LEFT, padx=5)
        self.unit_name_var = tk.StringVar(value=carcass.name)
        ttk.Entry(name_frame, textvariable=self.unit_name_var, width=25).pack(side=tk.LEFT, padx=5, fill=tk.X,
                                                                              expand=True)

        # ==================== SECTION 1: CARCASS ====================
        carcass_section = ttk.LabelFrame(self.detail_scrollable_frame, text="Carcass", padding=10)
        carcass_section.pack(fill=tk.X, padx=10, pady=10)

        # Dimensions row
        dim_frame = ttk.Frame(carcass_section)
        dim_frame.pack(fill=tk.X, pady=5)
        ttk.Label(dim_frame, text="Dimensions (mm):").pack(side=tk.LEFT, padx=5)

        # Height
        ttk.Label(dim_frame, text="H:").pack(side=tk.LEFT, padx=(20, 2))
        self.unit_height_var = tk.DoubleVar(value=carcass.height)
        ttk.Entry(dim_frame, textvariable=self.unit_height_var, width=8).pack(side=tk.LEFT, padx=2)

        # Width
        ttk.Label(dim_frame, text="W:").pack(side=tk.LEFT, padx=(10, 2))
        self.unit_width_var = tk.DoubleVar(value=carcass.width)
        ttk.Entry(dim_frame, textvariable=self.unit_width_var, width=8).pack(side=tk.LEFT, padx=2)

        # Depth
        ttk.Label(dim_frame, text="D:").pack(side=tk.LEFT, padx=(10, 2))
        self.unit_depth_var = tk.DoubleVar(value=carcass.depth)
        ttk.Entry(dim_frame, textvariable=self.unit_depth_var, width=8).pack(side=tk.LEFT, padx=2)

        # Material row
        material_frame = ttk.Frame(carcass_section)
        material_frame.pack(fill=tk.X, pady=5)
        ttk.Label(material_frame, text="Material:").pack(side=tk.LEFT, padx=5)
        self.material_var = tk.StringVar(value=carcass.material)
        ttk.Combobox(material_frame, textvariable=self.material_var, width=15,
                     values=self.get_carcass_materials()).pack(side=tk.LEFT, padx=10)

        # Material thickness row
        thickness_frame = ttk.Frame(carcass_section)
        thickness_frame.pack(fill=tk.X, pady=5)
        ttk.Label(thickness_frame, text="Material Thickness (mm):").pack(side=tk.LEFT, padx=5)
        self.unit_thickness_var = tk.DoubleVar(value=carcass.material_thickness)
        ttk.Combobox(thickness_frame, textvariable=self.unit_thickness_var, width=10,
                     values=["18", "19"]).pack(side=tk.LEFT, padx=10)

        # Shelves row
        shelves_frame = ttk.Frame(carcass_section)
        shelves_frame.pack(fill=tk.X, pady=5)
        ttk.Label(shelves_frame, text="Number of Shelves:").pack(side=tk.LEFT, padx=5)
        self.shelves_var = tk.IntVar(value=carcass.shelves)
        ttk.Entry(shelves_frame, textvariable=self.shelves_var, width=10).pack(side=tk.LEFT, padx=10)

        # ==================== SECTION 2: DRAWERS ====================
        drawers_section = ttk.LabelFrame(self.detail_scrollable_frame, text="Drawers", padding=10)
        drawers_section.pack(fill=tk.X, padx=10, pady=10)

        # Number of Drawers with Add/Remove buttons
        number_of_drawers_frame = ttk.Frame(drawers_section)
        number_of_drawers_frame.pack(fill=tk.X, pady=5)
        ttk.Label(number_of_drawers_frame, text="Number of Drawers:").pack(side=tk.LEFT, padx=5)

        self.number_of_drawers_var = tk.IntVar(value=len(cabinet.drawers))
        drawer_count_label = ttk.Label(number_of_drawers_frame, textvariable=self.number_of_drawers_var)
        drawer_count_label.pack(side=tk.LEFT, padx=5)

        ttk.Button(number_of_drawers_frame, text="Add Drawer",
                   command=self.add_drawer_panel).pack(side=tk.LEFT, padx=10)
        ttk.Button(number_of_drawers_frame, text="Remove Drawer",
                   command=self.remove_drawer_panel).pack(side=tk.LEFT, padx=5)

        # Container for all drawer panels
        self.drawer_panels_container = ttk.Frame(drawers_section)
        self.drawer_panels_container.pack(fill=tk.X, pady=10)

        # Initialize drawer panels data
        self.drawer_panels = []

        # Create panels for existing drawers only if unit has drawers
        for drawer in cabinet.drawers:
            self.create_drawer_panel(drawer)

        # ==================== SECTION 3: DOORS ====================
        doors_section = ttk.LabelFrame(self.detail_scrollable_frame, text="Doors", padding=10)
        doors_section.pack(fill=tk.X, padx=10, pady=10)

        doors = cabinet.doors
        # Door material row
        door_material_frame = ttk.Frame(doors_section)
        door_material_frame.pack(fill=tk.X, pady=5)
        ttk.Label(door_material_frame, text="Door Material:").pack(side=tk.LEFT, padx=5)
        self.door_material_var = tk.StringVar(value=getattr(doors, 'material', ''))
        ttk.Combobox(door_material_frame, textvariable=self.door_material_var, width=15,
                     values=self.get_door_materials()).pack(side=tk.LEFT, padx=10)

        # Door type row
        door_type_frame = ttk.Frame(doors_section)
        door_type_frame.pack(fill=tk.X, pady=5)
        ttk.Label(door_type_frame, text="Door Type:").pack(side=tk.LEFT, padx=5)
        self.door_type_var = tk.StringVar(value=getattr(doors, 'type', ''))
        ttk.Combobox(door_type_frame, textvariable=self.door_type_var, width=15,
                     values=["Shaker", "Flat"]).pack(side=tk.LEFT, padx=10)

        # Door thickness row
        door_thickness_frame = ttk.Frame(doors_section)
        door_thickness_frame.pack(fill=tk.X, pady=5)
        ttk.Label(door_thickness_frame, text="Door Thickness (mm):").pack(side=tk.LEFT, padx=5)
        self.door_thickness_var = tk.IntVar(value=getattr(doors, 'door_thickness', 25))
        ttk.Combobox(door_thickness_frame, textvariable=self.door_thickness_var, width=10,
                     values=[18, 25], state="readonly").pack(side=tk.LEFT, padx=10)

        # Door position row
        door_position_frame = ttk.Frame(doors_section)
        door_position_frame.pack(fill=tk.X, pady=5)
        ttk.Label(door_position_frame, text="Door Position:").pack(side=tk.LEFT, padx=5)
        self.door_position_var = tk.StringVar(value=getattr(doors, 'position', ''))
        ttk.Combobox(door_position_frame, textvariable=self.door_position_var, width=10,
                     values=['Overlay', 'Inset'], state="readonly").pack(side=tk.LEFT, padx=10)

        # Door margin row
        door_margin_frame = ttk.Frame(doors_section)
        door_margin_frame.pack(fill=tk.X, pady=5)
        ttk.Label(door_margin_frame, text="Door Margin (mm):").pack(side=tk.LEFT, padx=5)
        self.door_margin_var = tk.IntVar(value=getattr(doors, 'margin', 25))
        ttk.Combobox(door_margin_frame, textvariable=self.door_margin_var, width=10,
                     values=[4, 3, 2], state="readonly").pack(side=tk.LEFT, padx=10)
        # Door options row
        door_options_frame = ttk.Frame(doors_section)
        door_options_frame.pack(fill=tk.X, pady=5)

        self.door_moulding_var = tk.BooleanVar(value=getattr(doors, 'moulding', False))
        ttk.Checkbutton(door_options_frame, text="Moulding",
                        variable=self.door_moulding_var).pack(side=tk.LEFT, padx=10)

        self.door_cut_handle_var = tk.BooleanVar(value=getattr(doors, 'cut_handle', False))
        ttk.Checkbutton(door_options_frame, text="Cut Handle",
                        variable=self.door_cut_handle_var).pack(side=tk.LEFT, padx=10)

        # Number of doors row
        doors_count_frame = ttk.Frame(doors_section)
        doors_count_frame.pack(fill=tk.X, pady=5)
        ttk.Label(doors_count_frame, text="Number of Doors:").pack(side=tk.LEFT, padx=5)
        self.number_of_doors_var = tk.IntVar(value=getattr(doors, 'quantity', 0))
        ttk.Combobox(doors_count_frame, textvariable=self.number_of_doors_var, width=10,
                     values=[0, 1, 2], state="readonly").pack(side=tk.LEFT, padx=10)

        # ==================== SECTION 4: FACE FRAME ====================
        face_frame_section = ttk.LabelFrame(self.detail_scrollable_frame, text="Face Frame", padding=10)
        face_frame_section.pack(fill=tk.X, padx=10, pady=10)

        # Frame type row
        frame_type_frame = ttk.Frame(face_frame_section)
        frame_type_frame.pack(fill=tk.X, pady=5)
        ttk.Label(frame_type_frame, text="Frame Type:").pack(side=tk.LEFT, padx=5)
        self.face_frame_type_var = tk.StringVar(value=getattr(cabinet, 'face_frame_type', ''))
        ttk.Combobox(frame_type_frame, textvariable=self.face_frame_type_var, width=15,
                     values=self.get_face_frame_materials()).pack(side=tk.LEFT, padx=10)

        # Face frame moulding row
        face_frame_options_frame = ttk.Frame(face_frame_section)
        face_frame_options_frame.pack(fill=tk.X, pady=5)
        self.face_frame_moulding_var = tk.BooleanVar(value=getattr(cabinet, 'face_frame_moulding', False))
        ttk.Checkbutton(face_frame_options_frame, text="Face Frame Moulding",
                        variable=self.face_frame_moulding_var).pack(side=tk.LEFT, padx=10)

        # ==================== SECTION 5: QUANTITY ====================
        quantity_section = ttk.LabelFrame(self.detail_scrollable_frame, text="Quantity", padding=10)
        quantity_section.pack(fill=tk.X, padx=10, pady=10)

        quantity_frame = ttk.Frame(quantity_section)
        quantity_frame.pack(fill=tk.X, pady=5)
        ttk.Label(quantity_frame, text="Quantity:").pack(side=tk.LEFT, padx=5)
        self.unit_quantity_var = tk.IntVar(value=cabinet.quantity)
        ttk.Entry(quantity_frame, textvariable=self.unit_quantity_var, width=10).pack(side=tk.LEFT, padx=10)

        # ==================== BUTTONS ====================
        button_frame = ttk.Frame(self.detail_scrollable_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=20)
        ttk.Button(button_frame, text="Save", command=self.save_unit).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.hide_detail_panel).pack(side=tk.LEFT, padx=5)

        # Update canvas scroll region after all widgets are added
        self.detail_scrollable_frame.update_idletasks()
        self.detail_canvas.configure(scrollregion=self.detail_canvas.bbox("all"))

    def create_drawer_panel(self, drawer=None):
        """Create a new drawer panel"""
        panel_index = len(self.drawer_panels)

        # Main frame for this drawer
        drawer_frame = ttk.LabelFrame(self.drawer_panels_container, text=f"Drawer {panel_index + 1}",
                                      style='TLabelframe', padding=5)
        drawer_frame.pack(fill=tk.X, padx=5, pady=5)

        # Panel data dictionary
        panel_data = {
            'frame': drawer_frame,
            'index': panel_index,
            'height_var': tk.IntVar(value=drawer.height if drawer else ""),
            'thickness_var': tk.IntVar(value=drawer.thickness if drawer else 18),
            'material_var': tk.StringVar(value=drawer.material if drawer else ""),
            'runner_model_var': tk.StringVar(value=drawer.runner_model if drawer else ""),
            'runner_size_var': tk.IntVar(value=drawer.runner_size if drawer else ""),
            'runner_capacity_var': tk.IntVar(value=drawer.runner_capacity if drawer else ""),
            'runner_size_combo': None,
            'runner_capacity_combo': None
        }

        # Row 1: Height and Thickness
        row1_frame = ttk.Frame(drawer_frame)
        row1_frame.pack(fill=tk.X, pady=2)

        ttk.Label(row1_frame, text="Height:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(row1_frame, textvariable=panel_data['height_var'], width=8).pack(side=tk.LEFT, padx=5)

        ttk.Label(row1_frame, text="Thickness:").pack(side=tk.LEFT, padx=(15, 5))
        ttk.Entry(row1_frame, textvariable=panel_data['thickness_var'], width=8).pack(side=tk.LEFT, padx=5)

        # Row 2: Material
        row2_frame = ttk.Frame(drawer_frame)
        row2_frame.pack(fill=tk.X, pady=2)

        ttk.Label(row2_frame, text="Material:").pack(side=tk.LEFT, padx=5)
        ttk.Combobox(row2_frame, textvariable=panel_data['material_var'], width=12,
                     values=self.get_carcass_materials()).pack(side=tk.LEFT, padx=5)

        # Row 3: Runner Model
        row3_frame = ttk.Frame(drawer_frame)
        row3_frame.pack(fill=tk.X, pady=2)

        ttk.Label(row3_frame, text="Runner Model:").pack(side=tk.LEFT, padx=5)
        runner_model_combo = ttk.Combobox(row3_frame, textvariable=panel_data['runner_model_var'],
                                          width=12, values=[runner["Name"] for runner in self.runners_dict])
        runner_model_combo.pack(side=tk.LEFT, padx=5)

        # Bind the selection event
        runner_model_combo.bind("<<ComboboxSelected>>",
                                lambda event: self.on_runner_model_selected(event, panel_data))

        # Row 4: Runner Size and Capacity (initially disabled)
        row4_frame = ttk.Frame(drawer_frame)
        row4_frame.pack(fill=tk.X, pady=2)

        ttk.Label(row4_frame, text="Size (mm):").pack(side=tk.LEFT, padx=5)
        panel_data['runner_size_combo'] = ttk.Combobox(row4_frame, textvariable=panel_data['runner_size_var'],
                                                       width=8, state="disabled")
        panel_data['runner_size_combo'].pack(side=tk.LEFT, padx=5)
        panel_data['runner_size_combo'].bind("<<ComboboxSelected>>",
                                             lambda event: self.on_runner_size_selected(event, panel_data))

        ttk.Label(row4_frame, text="Capacity (kg):").pack(side=tk.LEFT, padx=(10, 5))
        panel_data['runner_capacity_combo'] = ttk.Combobox(row4_frame, textvariable=panel_data['runner_capacity_var'],
                                                           width=8, state="disabled")
        panel_data['runner_capacity_combo'].pack(side=tk.LEFT, padx=5)

        # Store panel data
        self.drawer_panels.append(panel_data)

        # Update drawer count
        self.number_of_drawers_var.set(len(self.drawer_panels))

    def on_runner_model_selected(self, event, panel_data):
        """Handle runner model selection"""
        selected_model = panel_data['runner_model_var'].get()

        if selected_model:
            # Get available sizes for this model
            runners = self.create_runners_list(selected_model)
            sizes = list(set([runner['Length'] for runner in runners]))
            sizes.sort()

            # Enable and populate size combobox
            panel_data['runner_size_combo'].config(state="normal")
            panel_data['runner_size_combo']['values'] = sizes
            panel_data['runner_size_var'].set("")
            panel_data['runner_capacity_var'].set("")
            panel_data['runner_capacity_combo'].config(state="disabled")
            panel_data['runner_capacity_combo']['values'] = []
        else:
            # Disable size and capacity comboboxes
            panel_data['runner_size_combo'].config(state="disabled")
            panel_data['runner_capacity_combo'].config(state="disabled")
            panel_data['runner_size_var'].set("")
            panel_data['runner_capacity_var'].set("")

    def on_runner_size_selected(self, event, panel_data):
        """Handle runner size selection"""
        selected_model = panel_data['runner_model_var'].get()
        selected_size = panel_data['runner_size_var'].get()

        if selected_model and selected_size:
            # Extract numeric size
            # size_value = int(selected_size.replace('mm', ''))

            # Get available capacities for this model and size

            runners = self.create_runners_list(selected_model)
            capacities = list(set([runner['Capacity'] for runner in runners
                                   if runner['Length'] == selected_size]))

            capacities.sort()

            # Enable and populate capacity combobox
            panel_data['runner_capacity_combo'].config(state="normal")
            panel_data['runner_capacity_combo']['values'] = capacities

            # Reset capacity selection
            panel_data['runner_capacity_var'].set("")

    def add_drawer_panel(self):
        """Add a new drawer panel"""
        self.create_drawer_panel()
        # Update scroll region after adding panel
        self.update_scroll_region()

    def remove_drawer_panel(self):
        """Remove the last drawer panel"""
        if len(self.drawer_panels) > 1:
            # Remove the last panel
            last_panel = self.drawer_panels.pop()
            last_panel['frame'].destroy()

            # Update drawer count
            self.number_of_drawers_var.set(len(self.drawer_panels))

            # Renumber remaining panels
            for i, panel in enumerate(self.drawer_panels):
                panel['frame'].config(text=f"Drawer {i + 1}")
                panel['index'] = i

            # Update scroll region after removing panel
            self.update_scroll_region()

    def update_scroll_region(self):
        """Update the canvas scroll region"""
        self.detail_scrollable_frame.update_idletasks()
        self.detail_canvas.configure(scrollregion=self.detail_canvas.bbox("all"))

    def create_runners_list(self, brand_name):
        """Create runners list for a specific brand"""
        for runner_brand in self.runners_dict:
            if runner_brand["Name"] == brand_name:
                return runner_brand["Runners"]
        return []

    def get_cabinet_data(self):
        """Get data from all sections of the cabinet form"""
        cabinet_data = {
            'name': self.unit_name_var.get(),
            'carcass': {
                'height': self.unit_height_var.get(),
                'width': self.unit_width_var.get(),
                'depth': self.unit_depth_var.get(),
                'material_thickness': self.unit_thickness_var.get(),
                'material': self.material_var.get(),
                'shelves': self.shelves_var.get()
            },
            'drawers': self.get_drawer_data(),
            'doors': {
                'door_material': self.door_material_var.get(),
                'door_type': self.door_type_var.get(),
                'door_thickness': self.door_thickness_var.get(),
                'moulding': self.door_moulding_var.get(),
                'cut_handle': self.door_cut_handle_var.get(),
                'number_of_doors': self.number_of_doors_var.get(),
                'position': self.door_position_var.get(),
                'margin': self.door_margin_var.get()
            },
            'face_frame': {
                'frame_type': self.face_frame_type_var.get(),
                'moulding': self.face_frame_moulding_var.get()
            },
            'quantity': self.unit_quantity_var.get()
        }
        return cabinet_data

    def get_drawer_data(self):
        """Get data from all drawer panels"""
        drawers_data = []
        for panel in self.drawer_panels:
            drawer_data = {
                'height': panel['height_var'].get(),
                'thickness': panel['thickness_var'].get(),
                'material': panel['material_var'].get(),
                'runner_model': panel['runner_model_var'].get(),
                'runner_size': panel['runner_size_var'].get(),
                'runner_capacity': panel['runner_capacity_var'].get()
            }
            drawers_data.append(drawer_data)
        return drawers_data

    def get_runner_price(self, runner_model_name, runner_size, runner_capacity):
        runner_model = self.create_runners_list(runner_model_name)
        for runner in runner_model:
            if runner["Length"] == runner_size and runner["Capacity"] == runner_capacity:
                return runner["Price"]

        raise ValueError("Specified runner information not found")

    def create_default_cabinet(self):
        carcass = Carcass("",
                          None,
                          None,
                          None,
                          "Laminate",
                          17,
                          0)

        drawers = []

        doors = Doors(carcass,
                      "",
                      "",
                      "",
                      False,
                      False,
                      0,
                      "",
                      "")

        face_frame = FaceFrame(carcass,
                               "",
                               False)

        return Cabinet(carcass, drawers, 1, doors, face_frame)

    def parse_cabinet_data(self, cabinet_data):
        carcass_data = cabinet_data['carcass']
        carcass = Carcass(cabinet_data['name'],
                          carcass_data['height'],
                          carcass_data['width'],
                          carcass_data['depth'],
                          carcass_data['material'],
                          carcass_data['material_thickness'],
                          carcass_data['shelves'])

        drawers = []
        for drawer_data in cabinet_data['drawers']:
            drawers.append(Drawer(drawer_data['height'],
                            drawer_data['thickness'],
                            drawer_data['material'],
                            drawer_data['runner_model'],
                            drawer_data['runner_size'],
                            drawer_data['runner_capacity'],
                            carcass,
                            self.get_runner_price(drawer_data['runner_model'],
                                                  drawer_data['runner_size'],
                                                  drawer_data['runner_capacity'])))

        door_data = cabinet_data['doors']

        doors = Doors(carcass,
                      door_data['door_material'],
                      door_data['door_type'],
                      door_data['door_thickness'],
                      door_data['moulding'],
                      door_data['cut_handle'],
                      door_data['number_of_doors'],
                      door_data['position'],
                      door_data['margin'])

        face_frame_data = cabinet_data['face_frame']
        face_frame = FaceFrame(carcass,
                               face_frame_data['frame_type'],
                               face_frame_data['moulding'])

        return Cabinet(carcass, drawers, cabinet_data['quantity'], doors, face_frame)

    def save_unit(self):
        """Save the unit from the detail panel"""
        try:
            # Create a unit from the UI fields
            unit = self.parse_cabinet_data(self.get_cabinet_data())

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
            carcass = unit.carcass
            dimensions = f"{carcass.height} × {carcass.width} × {carcass.depth}"
            self.unit_table.insert('', tk.END, values=(
                carcass.name,
                dimensions,
                carcass.material_thickness,
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
        ttk.Label(summary, text=str(quote['total_sheets_required'])).grid(row=2, column=1, sticky="w", padx=5)

        ttk.Label(summary, text="Sheets Breakdown:").grid(row=2, column=0, sticky="w", padx=5)
        ttk.Label(summary, text=str(quote['sheets_breakdown'])).grid(row=2, column=1, sticky="w", padx=5)

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

        ttk.Label(summary, text="Materials Used:").grid(row=6, column=0, sticky="w", padx=5)
        ttk.Label(summary, text=f"{quote['materials_used']}").grid(row=6, column=1, sticky="w", padx=5)

    def show_cut_list(self):
        """Display the cut list in a new window"""
        self.update_calculator_settings()

        if not self.calculator.units:
            messagebox.showinfo("No Units", "Add units to generate a cut list.")
            return

        # Calculate the quote to get the cut list
        quote = self.calculator.calculate_quote()

        self.visualise_sheets(self.calculator.optimizer, self.calculator.get_all_parts(), self.calculator.sheets)

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