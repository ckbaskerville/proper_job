"""Cabinet editor widget."""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable, List, Dict, Any

from src.models import Cabinet, Carcass, Drawer, Doors, FaceFrame
from src.config import DarkTheme
from src.business.material_manager import MaterialManager
from src.utils.validators import Validator, ValidationError
from ..base import ScrollableFrame
from .material_selector import MaterialSelector
from .dimension_input import DimensionInput
from .drawer_panel import DrawerPanel


class CabinetEditorWidget(ScrollableFrame):
    """Widget for editing cabinet specifications."""

    def __init__(
        self,
        parent: tk.Widget,
        materials_data: Dict[str, Any],
        runners_data: List[Dict[str, Any]],
        labor_data: Dict[str, Any],
        material_manager: MaterialManager,
        default_thickness: float = 18.0,
        on_save: Optional[Callable[[Cabinet], None]] = None,
        on_cancel: Optional[Callable[[], None]] = None
    ):
        """Initialize cabinet editor.

        Args:
            parent: Parent widget
            materials_data: Materials configuration
            runners_data: Runner specifications
            labor_data: Labor cost data
            material_manager: Material manager instance
            default_thickness: Default material thickness
            on_save: Save callback
            on_cancel: Cancel callback
        """
        super().__init__(parent)

        self.materials_data = materials_data
        self.runners_data = runners_data
        self.labor_data = labor_data
        self.material_manager = material_manager
        self.default_thickness = default_thickness
        self.on_save = on_save
        self.on_cancel = on_cancel

        self._current_cabinet: Optional[Cabinet] = None
        self._drawer_panels: List[DrawerPanel] = []

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create editor widgets."""
        frame = self.get_frame()

        # Title
        title_label = ttk.Label(
            frame,
            text="Cabinet Editor",
            font=('Arial', 14, 'bold')
        )
        title_label.pack(pady=10)

        # Carcass section
        self._create_carcass_section(frame)

        # Drawers section
        self._create_drawers_section(frame)

        # Doors section
        self._create_doors_section(frame)

        # Face frame section
        self._create_face_frame_section(frame)

        # Quantity section
        self._create_quantity_section(frame)

        # Buttons
        self._create_buttons(frame)

    def _create_carcass_section(self, parent: ttk.Frame) -> None:
        """Create carcass section."""
        section = ttk.LabelFrame(parent, text="Carcass", padding=10)
        section.pack(fill=tk.X, padx=10, pady=5)

        # Name
        name_frame = ttk.Frame(section)
        name_frame.pack(fill=tk.X, pady=2)

        ttk.Label(name_frame, text="Name:", width=15).pack(side=tk.LEFT)
        self.name_var = tk.StringVar()
        ttk.Entry(name_frame, textvariable=self.name_var).pack(
            side=tk.LEFT, fill=tk.X, expand=True
        )

        # Dimensions
        dim_frame = ttk.Frame(section)
        dim_frame.pack(fill=tk.X, pady=2)

        ttk.Label(dim_frame, text="Dimensions (mm):", width=17).pack(side=tk.LEFT)

        self.height_input = DimensionInput(dim_frame, label="H:")
        self.height_input.pack(side=tk.LEFT, padx=2)

        self.width_input = DimensionInput(dim_frame, label="W:")
        self.width_input.pack(side=tk.LEFT, padx=2)

        self.depth_input = DimensionInput(dim_frame, label="D:")
        self.depth_input.pack(side=tk.LEFT, padx=2)

        # Material
        mat_frame = ttk.Frame(section)
        mat_frame.pack(fill=tk.X, pady=2)

        ttk.Label(mat_frame, text="Material:", width=15).pack(side=tk.LEFT)

        self.carcass_material_selector = MaterialSelector(
            mat_frame,
            self.material_manager,
            component_type="Carcass"
        )
        self.carcass_material_selector.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Shelves
        shelf_frame = ttk.Frame(section)
        shelf_frame.pack(fill=tk.X, pady=2)

        ttk.Label(shelf_frame, text="Shelves:", width=15).pack(side=tk.LEFT)
        self.shelves_var = tk.IntVar(value=0)
        ttk.Spinbox(
            shelf_frame,
            from_=0,
            to=10,
            textvariable=self.shelves_var,
            width=10
        ).pack(side=tk.LEFT)

        # Back panel
        self.has_back_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            section,
            text="Include back panel",
            variable=self.has_back_var
        ).pack(anchor=tk.W, pady=2)

    def _create_drawers_section(self, parent: ttk.Frame) -> None:
        """Create drawers section."""
        section = ttk.LabelFrame(parent, text="Drawers", padding=10)
        section.pack(fill=tk.X, padx=10, pady=5)

        # Controls
        control_frame = ttk.Frame(section)
        control_frame.pack(fill=tk.X, pady=5)

        ttk.Button(
            control_frame,
            text="Add Drawer",
            command=self._add_drawer
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            control_frame,
            text="Remove Last",
            command=self._remove_drawer
        ).pack(side=tk.LEFT, padx=2)

        self.drawer_count_label = ttk.Label(
            control_frame,
            text="0 drawers"
        )
        self.drawer_count_label.pack(side=tk.LEFT, padx=10)

        # Drawer panels container
        self.drawers_container = ttk.Frame(section)
        self.drawers_container.pack(fill=tk.X, pady=5)

    def _create_doors_section(self, parent: ttk.Frame) -> None:
        """Create doors section."""
        section = ttk.LabelFrame(parent, text="Doors", padding=10)
        section.pack(fill=tk.X, padx=10, pady=5)

        # Number of doors
        doors_frame = ttk.Frame(section)
        doors_frame.pack(fill=tk.X, pady=2)

        ttk.Label(doors_frame, text="Number of doors:", width=15).pack(side=tk.LEFT)
        self.door_count_var = tk.IntVar(value=0)
        ttk.Combobox(
            doors_frame,
            textvariable=self.door_count_var,
            values=[0, 1, 2, 3, 4],
            state="readonly",
            width=10
        ).pack(side=tk.LEFT)

        # Door options frame (initially hidden)
        self.door_options_frame = ttk.Frame(section)

        # Door material
        mat_frame = ttk.Frame(self.door_options_frame)
        mat_frame.pack(fill=tk.X, pady=2)

        ttk.Label(mat_frame, text="Material:", width=15).pack(side=tk.LEFT)

        self.door_material_selector = MaterialSelector(
            mat_frame,
            self.material_manager,
            component_type="Door"
        )
        self.door_material_selector.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Door type
        type_frame = ttk.Frame(self.door_options_frame)
        type_frame.pack(fill=tk.X, pady=2)

        ttk.Label(type_frame, text="Type:", width=15).pack(side=tk.LEFT)
        self.door_type_var = tk.StringVar(value="Shaker")
        ttk.Combobox(
            type_frame,
            textvariable=self.door_type_var,
            values=["Shaker", "Flat", "Raised Panel"],
            state="readonly",
            width=20
        ).pack(side=tk.LEFT)

        # Door position
        pos_frame = ttk.Frame(self.door_options_frame)
        pos_frame.pack(fill=tk.X, pady=2)

        ttk.Label(pos_frame, text="Position:", width=15).pack(side=tk.LEFT)
        self.door_position_var = tk.StringVar(value="Overlay")
        ttk.Combobox(
            pos_frame,
            textvariable=self.door_position_var,
            values=["Overlay", "Inset", "Partial Overlay"],
            state="readonly",
            width=20
        ).pack(side=tk.LEFT)

        # Door margin
        margin_frame = ttk.Frame(self.door_options_frame)
        margin_frame.pack(fill=tk.X, pady=2)

        ttk.Label(margin_frame, text="Margin (mm):", width=15).pack(side=tk.LEFT)
        self.door_margin_var = tk.IntVar(value=4)
        ttk.Spinbox(
            margin_frame,
            from_=0,
            to=20,
            textvariable=self.door_margin_var,
            width=10
        ).pack(side=tk.LEFT)

        # Door options checkboxes
        self.door_moulding_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            self.door_options_frame,
            text="Add moulding",
            variable=self.door_moulding_var
        ).pack(anchor=tk.W, pady=2)

        self.door_cut_handle_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            self.door_options_frame,
            text="Cut handle",
            variable=self.door_cut_handle_var
        ).pack(anchor=tk.W, pady=2)

        # Bind door count change
        self.door_count_var.trace('w', self._on_door_count_changed)

    def _create_face_frame_section(self, parent: ttk.Frame) -> None:
        """Create face frame section."""
        section = ttk.LabelFrame(parent, text="Face Frame", padding=10)
        section.pack(fill=tk.X, padx=10, pady=5)

        # Face frame type
        type_frame = ttk.Frame(section)
        type_frame.pack(fill=tk.X, pady=2)

        ttk.Label(type_frame, text="Type:", width=15).pack(side=tk.LEFT)

        self.face_frame_type_var = tk.StringVar(value="None")
        materials = ["None"] + self.material_manager.get_materials_for_component("Face Frame")
        ttk.Combobox(
            type_frame,
            textvariable=self.face_frame_type_var,
            values=materials,
            state="readonly",
            width=25
        ).pack(side=tk.LEFT)

        # Face frame options
        self.face_frame_options = ttk.Frame(section)

        self.face_frame_moulding_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            self.face_frame_options,
            text="Add moulding",
            variable=self.face_frame_moulding_var
        ).pack(anchor=tk.W, pady=2)

        self.face_frame_center_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            self.face_frame_options,
            text="Add center stile",
            variable=self.face_frame_center_var
        ).pack(anchor=tk.W, pady=2)

        # Bind type change
        self.face_frame_type_var.trace('w', self._on_face_frame_type_changed)

    def _create_quantity_section(self, parent: ttk.Frame) -> None:
        """Create quantity section."""
        section = ttk.LabelFrame(parent, text="Quantity", padding=10)
        section.pack(fill=tk.X, padx=10, pady=5)

        qty_frame = ttk.Frame(section)
        qty_frame.pack(fill=tk.X)

        ttk.Label(qty_frame, text="Number of units:", width=15).pack(side=tk.LEFT)
        self.quantity_var = tk.IntVar(value=1)
        ttk.Spinbox(
            qty_frame,
            from_=1,
            to=50,
            textvariable=self.quantity_var,
            width=10
        ).pack(side=tk.LEFT)

    def _create_buttons(self, parent: ttk.Frame) -> None:
        """Create action buttons."""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, padx=10, pady=90, side=tk.BOTTOM)

        ttk.Button(
            button_frame,
            text="Save",
            command=self._save_cabinet,
            style='Accent.TButton'
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self._cancel
        ).pack(side=tk.RIGHT)

    def _add_drawer(self) -> None:
        """Add a new drawer panel."""
        panel = DrawerPanel(
            self.drawers_container,
            self.material_manager,
            self.runners_data,
            len(self._drawer_panels) + 1
        )
        panel.pack(fill=tk.X, pady=5)

        self._drawer_panels.append(panel)
        self._update_drawer_count()

    def _remove_drawer(self) -> None:
        """Remove the last drawer panel."""
        if self._drawer_panels:
            panel = self._drawer_panels.pop()
            panel.destroy()
            self._update_drawer_count()

    def _update_drawer_count(self) -> None:
        """Update drawer count label."""
        count = len(self._drawer_panels)
        self.drawer_count_label.config(text=f"{count} drawers")

    def _on_door_count_changed(self, *args) -> None:
        """Handle door count change."""
        if self.door_count_var.get() > 0:
            self.door_options_frame.pack(fill=tk.X, pady=5)
        else:
            self.door_options_frame.pack_forget()

    def _on_face_frame_type_changed(self, *args) -> None:
        """Handle face frame type change."""
        if self.face_frame_type_var.get() != "None":
            self.face_frame_options.pack(fill=tk.X, pady=5)
        else:
            self.face_frame_options.pack_forget()

    def load_cabinet(self, cabinet: Cabinet) -> None:
        """Load cabinet data into editor.

        Args:
            cabinet: Cabinet to load
        """
        self._current_cabinet = cabinet

        # Load carcass data
        carcass = cabinet.carcass
        self.name_var.set(carcass.name)
        self.height_input.set(carcass.height)
        self.width_input.set(carcass.width)
        self.depth_input.set(carcass.depth)
        self.carcass_material_selector.set_material(
            carcass.material,
            carcass.material_thickness
        )
        self.shelves_var.set(carcass.shelves)
        self.has_back_var.set(carcass.has_back)

        # Load drawers
        for drawer in cabinet.drawers:
            self._add_drawer()
            panel = self._drawer_panels[-1]
            panel.load_drawer(drawer)

        # Load doors
        if cabinet.doors:
            self.door_count_var.set(cabinet.doors.quantity)
            if cabinet.doors.quantity > 0:
                self.door_material_selector.set_material(
                    cabinet.doors.material,
                    cabinet.doors.material_thickness
                )
                self.door_type_var.set(cabinet.doors.door_type)
                self.door_position_var.set(cabinet.doors.position)
                self.door_margin_var.set(cabinet.doors.margin)
                self.door_moulding_var.set(cabinet.doors.moulding)
                self.door_cut_handle_var.set(cabinet.doors.cut_handle)

        # Load face frame
        if cabinet.face_frame:
            self.face_frame_type_var.set(cabinet.face_frame.frame_type)
            self.face_frame_moulding_var.set(cabinet.face_frame.moulding)
            self.face_frame_center_var.set(cabinet.face_frame.has_center_stile)

        # Load quantity
        self.quantity_var.set(cabinet.quantity)

    def _save_cabinet(self) -> None:
        """Save the cabinet."""
        try:
            # Validate inputs
            name = Validator.validate_string(
                self.name_var.get(),
                "Cabinet name"
            )

            height = self.height_input.get()
            width = self.width_input.get()
            depth = self.depth_input.get()

            material, thickness = self.carcass_material_selector.get_selection()

            # Create carcass
            carcass = Carcass(
                name=name,
                height=height,
                width=width,
                depth=depth,
                material=material,
                material_thickness=thickness,
                shelves=self.shelves_var.get(),
                has_back=self.has_back_var.get()
            )

            # Create drawers
            drawers = []
            for panel in self._drawer_panels:
                drawer = panel.get_drawer(carcass)
                if drawer:
                    drawers.append(drawer)

            # Create doors
            doors = None
            if self.door_count_var.get() > 0:
                door_material, door_thickness = self.door_material_selector.get_selection()
                doors = Doors(
                    carcass=carcass,
                    material=door_material,
                    door_type=self.door_type_var.get(),
                    material_thickness=door_thickness,
                    moulding=self.door_moulding_var.get(),
                    cut_handle=self.door_cut_handle_var.get(),
                    quantity=self.door_count_var.get(),
                    position=self.door_position_var.get(),
                    margin=self.door_margin_var.get()
                )

            # Create face frame
            face_frame = None
            if self.face_frame_type_var.get() != "None":
                face_frame = FaceFrame(
                    carcass=carcass,
                    frame_type=self.face_frame_type_var.get(),
                    moulding=self.face_frame_moulding_var.get(),
                    has_center_stile=self.face_frame_center_var.get()
                )

            # Create cabinet
            cabinet = Cabinet(
                carcass=carcass,
                drawers=drawers,
                quantity=self.quantity_var.get(),
                doors=doors,
                face_frame=face_frame
            )

            # Call save callback
            if self.on_save:
                self.on_save(cabinet)

        except ValidationError as e:
            messagebox.showerror("Validation Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save cabinet: {str(e)}")

    def _cancel(self) -> None:
        """Cancel editing."""
        if self.on_cancel:
            self.on_cancel()