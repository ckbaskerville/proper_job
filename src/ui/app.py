"""Main application window."""

import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, List, Dict, Any
from pathlib import Path
import sys

from src.config import (
    WINDOW_TITLE,
    DEFAULT_WINDOW_SIZE,
    MIN_WINDOW_WIDTH,
    MIN_WINDOW_HEIGHT,
    Settings,
    SettingsManager,
    ThemeManager,
    PathConfig,
    DarkTheme
)
from src.business.calculator import QuoteCalculator
from src.business.material_manager import MaterialManager
from src.business.labor_manager import LaborManager
from src.data.repository import DataRepository, ProjectRepository
from src.models import Cabinet, Project
from src.ui.dialogs.export_dialog import ExportDialog
from src.ui.dialogs.unit_breakdown_dialog import UnitBreakdownDialog
from src.ui.dialogs.cut_list_dialog import CutListDialog
from src.ui.dialogs.settings_dialog import SettingsDialog
from src.ui.dialogs.project_settings_dialog import ProjectSettingsDialog

from .widgets import (
    UnitTableWidget,
    QuoteDisplayWidget,
    CabinetEditorWidget,
    StatusBar,
    ToolBar
)
# from .dialogs import (
#     SettingsDialog,
#     AboutDialog,
#     CutListDialog,
#     UnitBreakdownDialog,
#     ExportDialog
# )
from .visualization.sheet_visualizer import VisualizationWindow


logger = logging.getLogger(__name__)


class KitchenQuoteApp:
    """Main application window for the kitchen quote system."""

    def __init__(self, root: tk.Tk):
        """Initialize the application.

        Args:
            root: The root Tkinter window
        """
        self.root = root
        self.settings_manager = SettingsManager()
        self.theme_manager = ThemeManager()
        self.paths = PathConfig()


        # Setup window
        self._setup_window()

        # Load resources and initialize business logic
        self._load_resources()
        self._setup_business_logic()

        # Initialize state
        self._current_project = Project(name="Untitled Project")
        self._current_file_path: Optional[Path] = None
        self._is_modified = False
        self._current_cabinet_index: Optional[int] = None

        # Create UI
        self._setup_ui()

        # Bind events
        self._bind_events()

        # Start autosave if enabled
        if self.settings_manager.settings.autosave_enabled:
            self._start_autosave()

        # Restore window state
        self._restore_window_state()

        logger.info("Application initialized successfully")

    def _setup_window(self) -> None:
        """Configure the main window."""
        self.root.title(WINDOW_TITLE)
        self.root.geometry(DEFAULT_WINDOW_SIZE)
        self.root.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)

        # Set window icon
        if self.paths.icon_file.exists():
            try:
                self.root.iconbitmap(str(self.paths.icon_file))
            except Exception as e:
                logger.warning(f"Could not set window icon: {e}")

        # Apply theme
        style = ttk.Style(self.root)
        self.theme_manager.apply_theme(
            style,
            self.settings_manager.settings.theme
        )

        # Configure root window
        self.root.configure(bg=DarkTheme.BG_COLOR)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

    def _load_resources(self) -> None:
        """Load configuration resources."""
        self.repository = DataRepository()

        try:
            self.runners_data = self.repository.load_runners()
            self.materials_data = self.repository.load_materials()
            self.labor_data = self.repository.load_labor_costs()
            self.hinges_data = self.repository.load_hinges()
            self.dbc_drawers_data = self.repository.load_dbc_drawers()

            logger.info("Resources loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load resources: {e}")
            messagebox.showerror(
                "Resource Error",
                f"Failed to load configuration files:\n{e}\n\n"
                "Please ensure all resource files are present."
            )
            self.root.destroy()
            raise

    def _setup_business_logic(self) -> None:
        """Initialize business logic components."""
        # Create managers
        self.material_manager = MaterialManager(self.materials_data)
        self.labor_manager = LaborManager(self.labor_data, self.material_manager)

        # Create calculator
        self.calculator = QuoteCalculator(
            material_manager=self.material_manager,
            labor_manager=self.labor_manager,
            sheet_width=self.settings_manager.settings.default_sheet_width,
            sheet_height=self.settings_manager.settings.default_sheet_height
        )

        # Quote result storage
        self.current_quote = None

    def _setup_ui(self) -> None:
        """Create the UI components."""
        # Create menu bar
        self._create_menu_bar()

        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # # Create logo frame
        # logo_frame = ttk.Frame(main_frame)
        # self.toolbar.grid(row=0, column=0, sticky="ew")
        # logo = tk.PhotoImage(file=str(self.paths.logo_file))
        # logo_label = ttk.Label(logo_frame, image=logo)


        # Toolbar
        self.toolbar = ToolBar(
            main_frame,
            on_new=self._new_project,
            on_open=self._open_project,
            on_save=self._save_project,
            on_add_unit=self._add_unit,
            on_edit_unit=self._edit_unit,
            on_duplicate_unit=self._duplicate_unit,
            on_remove_unit=self._remove_unit,
            on_settings=self._open_settings,
            on_materials_settings=self._open_material_database,
            on_runners_settings=self._open_runner_database,
            on_labor_settings=self._open_labor_database,
            on_hinge_settings=self._open_hinge_database
        )
        self.toolbar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        # Content area
        content_frame = ttk.Frame(main_frame)
        content_frame.grid(row=1, column=0, sticky="nsew", padx=5)
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(0, weight=1)

        # Create paned window
        self.paned = ttk.PanedWindow(content_frame, orient=tk.HORIZONTAL)
        self.paned.grid(row=0, column=0, sticky="nsew")

        # Left panel - Unit list
        left_frame = ttk.Frame(self.paned)
        self.paned.add(left_frame, weight=3)

        # Unit table
        self.unit_table = UnitTableWidget(
            left_frame,
            on_select=self._on_unit_selected,
            on_add=self._add_unit,
            on_edit=self._edit_unit,
            on_remove=self._remove_unit,
            on_duplicate=self._duplicate_unit
        )
        self.unit_table.pack(fill=tk.BOTH, expand=True)

        # Right panel - Cabinet editor (initially hidden)
        self.editor_frame = ttk.Frame(self.paned)
        self.cabinet_editor = None

        # Bottom panel - Quote display
        bottom_frame = ttk.Frame(content_frame)
        bottom_frame.grid(row=1, column=0, sticky="ew", pady=(5, 0))

        # Quote controls
        quote_controls = ttk.Frame(bottom_frame)
        quote_controls.pack(fill=tk.X, pady=5)

        ttk.Button(
            quote_controls,
            text="Calculate Quote",
            command=self._calculate_quote
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            quote_controls,
            text="Show Cut List",
            command=self._show_cut_list
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            quote_controls,
            text="Unit Breakdown",
            command=self._show_unit_breakdown
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            quote_controls,
            text="Visualise Sheets",
            command=self._show_visualization
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            quote_controls,
            text="Export Quote",
            command=self._export_quote
        ).pack(side=tk.LEFT, padx=2)

        # Quote display
        self.quote_display = QuoteDisplayWidget(bottom_frame)
        self.quote_display.pack(fill=tk.X, pady=5)

        # Status bar
        self.status_bar = StatusBar(main_frame)
        self.status_bar.grid(row=2, column=0, sticky="ew")

        # Update status
        self._update_status("Ready")
        self._update_project_info()

    def _create_menu_bar(self) -> None:
        """Create the application menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)

        file_menu.add_command(
            label="New Project",
            accelerator="Ctrl+N",
            command=self._new_project
        )
        file_menu.add_command(
            label="Open Project...",
            accelerator="Ctrl+O",
            command=self._open_project
        )
        file_menu.add_command(
            label="Save Project",
            accelerator="Ctrl+S",
            command=self._save_project
        )
        file_menu.add_command(
            label="Save Project As...",
            accelerator="Ctrl+Shift+S",
            command=self._save_project_as
        )
        file_menu.add_separator()

        # Recent files submenu
        self.recent_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Recent Projects", menu=self.recent_menu)
        self._update_recent_menu()

        file_menu.add_separator()
        file_menu.add_command(
            label="Export...",
            accelerator="Ctrl+E",
            command=self._export_quote
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Settings...",
            command=self._open_settings
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Exit",
            accelerator="Alt+F4",
            command=self._quit_application
        )

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        edit_menu.add_command(
            label="Add Cabinet",
            accelerator="Ctrl+A",
            command=self._add_unit
        )
        edit_menu.add_command(
            label="Edit Cabinet",
            accelerator="F2",
            command=self._edit_unit
        )
        edit_menu.add_command(
            label="Duplicate Cabinet",
            accelerator="Ctrl+D",
            command=self._duplicate_unit
        )
        edit_menu.add_command(
            label="Remove Cabinet",
            accelerator="Delete",
            command=self._remove_unit
        )
        edit_menu.add_separator()
        edit_menu.add_command(
            label="Project Settings...",
            command=self._edit_project_settings
        )

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)

        view_menu.add_command(
            label="Show Cut List",
            accelerator="F5",
            command=self._show_cut_list
        )
        view_menu.add_command(
            label="Show Unit Breakdown",
            accelerator="F6",
            command=self._show_unit_breakdown
        )
        view_menu.add_command(
            label="Visualization",
            accelerator="F7",
            command=self._show_visualization
        )
        view_menu.add_separator()

        # Theme submenu
        theme_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Theme", menu=theme_menu)

        for theme_name in self.theme_manager.get_available_themes():
            theme_menu.add_radiobutton(
                label=theme_name.title(),
                variable=tk.StringVar(value=self.settings_manager.settings.theme),
                value=theme_name,
                command=lambda t=theme_name: self._change_theme(t)
            )

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)

        tools_menu.add_command(
            label="Calculate Quote",
            accelerator="F9",
            command=self._calculate_quote
        )
        tools_menu.add_separator()
        tools_menu.add_command(
            label="Material Database...",
            command=self._open_material_database
        )
        tools_menu.add_command(
            label="Runner Database...",
            command=self._open_runner_database
        )
        tools_menu.add_command(
            label="Hinge Database...",
            command=self._open_hinge_database
        )
        tools_menu.add_separator()
        tools_menu.add_command(
            label="Clean Temporary Files",
            command=self._clean_temp_files
        )

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)

        help_menu.add_command(
            label="Keyboard Shortcuts",
            command=self._show_shortcuts
        )


    def _bind_events(self) -> None:
        """Bind keyboard shortcuts and events."""
        # File shortcuts
        self.root.bind("<Control-n>", lambda e: self._new_project())
        self.root.bind("<Control-o>", lambda e: self._open_project())
        self.root.bind("<Control-s>", lambda e: self._save_project())
        self.root.bind("<Control-Shift-S>", lambda e: self._save_project_as())
        self.root.bind("<Control-e>", lambda e: self._export_quote())

        # Edit shortcuts
        self.root.bind("<Control-a>", lambda e: self._add_unit())
        self.root.bind("<F2>", lambda e: self._edit_unit())
        self.root.bind("<Control-d>", lambda e: self._duplicate_unit())
        self.root.bind("<Delete>", lambda e: self._remove_unit())

        # View shortcuts
        self.root.bind("<F5>", lambda e: self._show_cut_list())
        self.root.bind("<F6>", lambda e: self._show_unit_breakdown())
        self.root.bind("<F7>", lambda e: self._show_visualization())

        # Tools shortcuts
        self.root.bind("<F9>", lambda e: self._calculate_quote())

        # Help shortcuts
        self.root.bind("<F1>", lambda e: self._show_help())

        # Window events
        self.root.protocol("WM_DELETE_WINDOW", self._quit_application)
        self.root.bind("<Configure>", self._on_window_configure)

    def _on_window_configure(self, event=None) -> None:
        """Handle window configuration changes."""
        if event and event.widget == self.root:
            # Update window state in settings
            self.settings_manager.settings.update_window_state(
                maximized=self.root.state() == 'zoomed',
                width=self.root.winfo_width(),
                height=self.root.winfo_height(),
                x=self.root.winfo_x(),
                y=self.root.winfo_y()
            )

    def _restore_window_state(self) -> None:
        """Restore window state from settings."""
        settings = self.settings_manager.settings

        if settings.window_maximized:
            self.root.state('zoomed')
        else:
            # Set size
            self.root.geometry(
                f"{settings.window_width}x{settings.window_height}"
            )

            # Set position if saved
            if settings.window_x is not None and settings.window_y is not None:
                self.root.geometry(
                    f"+{settings.window_x}+{settings.window_y}"
                )

    def _update_status(self, message: str, timeout: int = 0) -> None:
        """Update status bar message.

        Args:
            message: Status message
            timeout: Clear message after timeout (0 = permanent)
        """
        self.status_bar.set_status(message)

        if timeout > 0:
            self.root.after(
                timeout,
                lambda: self.status_bar.set_status("Ready")
            )

    def _update_project_info(self) -> None:
        """Update project information in UI."""
        # Update title
        title = f"{self._current_project.name} - {WINDOW_TITLE}"
        if self._is_modified:
            title = f"*{title}"
        self.root.title(title)

        # Update status bar
        self.status_bar.set_project_info(
            units=self._current_project.total_units,
            modified=self._is_modified
        )

        # Update unit table
        self.unit_table.load_units(self._current_project.cabinets)

    def _set_modified(self, modified: bool = True) -> None:
        """Set project modified state."""
        self._is_modified = modified
        self._update_project_info()

    # Project management methods
    def _new_project(self) -> None:
        """Create a new project."""
        if self._is_modified:
            response = messagebox.askyesnocancel(
                "Save Changes",
                "Save changes to current project?"
            )
            if response is None:
                return
            elif response:
                if not self._save_project():
                    return

        self._current_project = Project(name="Untitled Project")
        self._current_file_path = None
        self._current_cabinet_index = None
        self.current_quote = None

        # Clear UI
        self._hide_cabinet_editor()
        self.quote_display.clear()

        # Update calculator
        self.calculator.units.clear()

        self._set_modified(False)
        self._update_status("New project created")

    def _open_project(self) -> None:
        """Open an existing project."""
        if self._is_modified:
            response = messagebox.askyesnocancel(
                "Save Changes",
                "Save changes to current project?"
            )
            if response is None:
                return
            elif response:
                if not self._save_project():
                    return

        filename = filedialog.askopenfilename(
            title="Open Project",
            defaultextension=".pjb",
            filetypes=[
                ("Proper Job Projects", "*.pjb"),
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ],
            initialdir=str(self.settings_manager.settings.last_save_directory or "")
        )

        if filename:
            self._load_project_file(Path(filename))

    def _load_project_file(self, filepath: Path) -> None:
        """Load a project from file.

        Args:
            filepath: Path to project file
        """
        try:
            self._current_project = Project.load_from_file(filepath)
            self._current_file_path = filepath

            # Update calculator
            self.calculator.units.clear()
            for cabinet in self._current_project.cabinets:
                self.calculator.add_unit(cabinet)

            # Update settings
            self.calculator.sheet_width = self._current_project.settings.sheet_width
            self.calculator.sheet_height = self._current_project.settings.sheet_height
            self.labor_manager.set_hourly_rate(self._current_project.settings.labor_rate)
            self.labor_manager.set_markup_percentage(self._current_project.settings.markup_percentage)

            # Update UI
            self._hide_cabinet_editor()
            self.quote_display.clear()
            self._set_modified(False)

            # Add to recent files
            self.settings_manager.settings.add_recent_file(str(filepath))
            self.settings_manager.save_settings()
            self._update_recent_menu()

            # Update save directory
            self.settings_manager.update_setting(
                'last_save_directory',
                str(filepath.parent)
            )

            self._update_status(f"Loaded: {filepath.name}")

        except Exception as e:
            logger.error(f"Failed to load project: {e}")
            messagebox.showerror(
                "Load Error",
                f"Failed to load project:\n{e}"
            )

    def _save_project(self) -> bool:
        """Save the current project.

        Returns:
            True if saved successfully
        """
        if not self._current_file_path:
            return self._save_project_as()

        return self._save_project_to_file(self._current_file_path)

    def _save_project_as(self) -> bool:
        """Save the project with a new name.

        Returns:
            True if saved successfully
        """
        filename = filedialog.asksaveasfilename(
            title="Save Project As",
            defaultextension=".pjb",
            filetypes=[
                ("Proper Job Projects", "*.pjb"),
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ],
            initialdir=str(self.settings_manager.settings.last_save_directory or ""),
            initialfile=f"{self._current_project.name}.pjb"
        )

        if filename:
            return self._save_project_to_file(Path(filename))

        return False

    def _save_project_to_file(self, filepath: Path) -> bool:
        """Save project to specific file.

        Args:
            filepath: Path to save to

        Returns:
            True if saved successfully
        """
        try:
            # Update project settings
            self._current_project.settings.sheet_width = self.calculator.sheet_width
            self._current_project.settings.sheet_height = self.calculator.sheet_height
            self._current_project.settings.labor_rate = self.labor_manager.hourly_rate
            self._current_project.settings.markup_percentage = self.labor_manager.markup_percentage

            # Update project name from filename
            self._current_project.name = filepath.stem

            # Save project
            self._current_project.save_to_file(filepath)
            self._current_file_path = filepath

            # Update UI
            self._set_modified(False)

            # Add to recent files
            self.settings_manager.settings.add_recent_file(str(filepath))
            self.settings_manager.save_settings()
            self._update_recent_menu()

            # Update save directory
            self.settings_manager.update_setting(
                'last_save_directory',
                str(filepath.parent)
            )

            self._update_status(f"Saved: {filepath.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to save project: {e}")
            messagebox.showerror(
                "Save Error",
                f"Failed to save project:\n{e}"
            )
            return False

    def _update_recent_menu(self) -> None:
        """Update recent files menu."""
        self.recent_menu.delete(0, tk.END)

        for filepath in self.settings_manager.settings.recent_files:
            path = Path(filepath)
            if path.exists():
                self.recent_menu.add_command(
                    label=path.name,
                    command=lambda p=path: self._load_project_file(p)
                )

        if not self.settings_manager.settings.recent_files:
            self.recent_menu.add_command(
                label="(No recent projects)",
                state=tk.DISABLED
            )

    # Cabinet management methods
    def _on_unit_selected(self, index: Optional[int]) -> None:
        """Handle unit selection.

        Args:
            index: Selected unit index
        """
        self._current_cabinet_index = index
        self.toolbar.set_edit_enabled(index is not None)

    def _add_unit(self) -> None:
        """Add a new cabinet unit."""
        self._current_cabinet_index = None
        self._show_cabinet_editor()

    def _edit_unit(self) -> None:
        """Edit the selected unit."""
        if self._current_cabinet_index is None:
            messagebox.showinfo(
                "No Selection",
                "Please select a cabinet to edit."
            )
            return

        cabinet = self._current_project.cabinets[self._current_cabinet_index]
        self._show_cabinet_editor(cabinet)

    def _remove_unit(self) -> None:
        """Remove the selected unit."""
        if self._current_cabinet_index is None:
            messagebox.showinfo(
                "No Selection",
                "Please select a cabinet to remove."
            )
            return

        if self.settings_manager.settings.confirm_delete:
            cabinet = self._current_project.cabinets[self._current_cabinet_index]
            response = messagebox.askyesno(
                "Confirm Delete",
                f"Remove cabinet '{cabinet.carcass.name}'?"
            )
            if not response:
                return

        # Remove from project and calculator
        self._current_project.remove_cabinet(self._current_cabinet_index)
        self.calculator.remove_unit(self._current_cabinet_index)

        # Clear selection
        self._current_cabinet_index = None

        # Update UI
        self._set_modified()
        self._update_status("Cabinet removed")

    def _duplicate_unit(self) -> None:
        """Duplicate the selected unit."""
        if self._current_cabinet_index is None:
            messagebox.showinfo(
                "No Selection",
                "Please select a cabinet to duplicate."
            )
            return

        # Duplicate in project
        self._current_project.duplicate_cabinet(self._current_cabinet_index)

        # Duplicate in calculator
        cabinet = self._current_project.cabinets[-1]
        self.calculator.add_unit(cabinet)

        # Update UI
        self._set_modified()
        self._update_status("Cabinet duplicated")

    def _show_cabinet_editor(self, cabinet: Optional[Cabinet] = None) -> None:
        """Show the cabinet editor.

        Args:
            cabinet: Cabinet to edit (None for new)
        """
        # Add editor frame to paned window if not already there
        if self.editor_frame not in self.paned.panes():
            self.paned.add(self.editor_frame, weight=0)

        # Create or update editor
        if self.cabinet_editor:
            self.cabinet_editor.destroy()

        self.cabinet_editor = CabinetEditorWidget(
            self.editor_frame,
            materials_data=self.materials_data,
            runners_data=self.runners_data,
            labor_data=self.labor_data,
            hinges_data=self.hinges_data,
            dbc_drawers_data=self.dbc_drawers_data,
            material_manager=self.material_manager,
            default_thickness=self.settings_manager.settings.default_thickness,
            on_save=self._save_cabinet,
            on_cancel=self._hide_cabinet_editor
        )
        self.cabinet_editor.pack(fill=tk.BOTH, expand=True)

        if cabinet:
            self.cabinet_editor.load_cabinet(cabinet)

    def _hide_cabinet_editor(self) -> None:
        """Hide the cabinet editor."""
        if str(self.editor_frame) in self.paned.panes():
            self.paned.remove(self.editor_frame)

        if self.cabinet_editor:
            self.cabinet_editor.destroy()
            self.cabinet_editor = None

    def _save_cabinet(self, cabinet: Cabinet) -> None:
        """Save cabinet from editor.

        Args:
            cabinet: Cabinet to save
        """
        if self._current_cabinet_index is not None:
            # Update existing
            self._current_project.cabinets[self._current_cabinet_index] = cabinet
            self.calculator.units[self._current_cabinet_index] = cabinet
        else:
            # Add new
            self._current_project.add_cabinet(cabinet)
            self.calculator.add_unit(cabinet)

        # Update UI
        self._hide_cabinet_editor()
        self._set_modified()
        self._update_status("Cabinet saved")

    # Quote and visualization methods
    def _calculate_quote(self) -> None:
        """Calculate and display quote."""
        if not self._current_project.cabinets:
            messagebox.showinfo(
                "No Cabinets",
                "Please add cabinets before calculating quote."
            )
            return

        try:
            self._update_status("Calculating quote...")

            # Update calculator settings
            self.calculator.sheet_width = self._current_project.settings.sheet_width
            self.calculator.sheet_height = self._current_project.settings.sheet_height

            # Calculate quote
            self.current_quote = self.calculator.calculate_quote()

            # Display quote
            self.quote_display.display_quote(
                self.current_quote.to_dict(),
                self.labor_manager.markup_percentage,
                self.settings_manager.settings.currency_symbol
            )

            self._update_status("Quote calculated successfully", timeout=3000)

        except Exception as e:
            logger.error(f"Error calculating quote: {e}")
            messagebox.showerror(
                "Calculation Error",
                f"Failed to calculate quote:\n{e}"
            )
            self._update_status("Quote calculation failed")

    def _show_cut_list(self) -> None:
        """Show cut list dialog."""
        if not self.current_quote:
            messagebox.showinfo(
                "No Quote",
                "Please calculate a quote first."
            )
            return

        dialog = CutListDialog(
            self.root,
            self.current_quote.to_dict(),
            self.calculator,
            self._current_project
        )
        dialog.show()

    def _show_unit_breakdown(self) -> None:
        """Show unit breakdown dialog."""
        if not self.current_quote:
            messagebox.showinfo(
                "No Quote",
                "Please calculate a quote first."
            )
            return

        breakdown = self.calculator.calculate_unit_breakdown()
        dialog = UnitBreakdownDialog(
            self.root,
            breakdown,
            self.calculator,
            self.settings_manager.settings.currency_symbol
        )
        dialog.show()

    def _show_visualization(self) -> None:
        """Show sheet visualization."""
        if not self.current_quote:
            messagebox.showinfo(
                "No Quote",
                "Please calculate a quote first."
            )
            return

        window = VisualizationWindow(
            self.root,
            self.calculator,
            self.current_quote
        )

    def _export_quote(self) -> None:
        """Export quote."""
        if not self.current_quote:
            messagebox.showinfo(
                "No Quote",
                "Please calculate a quote first."
            )
            return

        dialog = ExportDialog(
            self.root,
            self._current_project,
            self.current_quote,
            self.calculator,
            self.settings_manager.settings
        )

        if dialog.export():
            self._update_status("Quote exported successfully", timeout=3000)

    # Settings and tools methods
    def _open_settings(self) -> None:
        """Open settings dialog."""
        dialog = SettingsDialog(
            self.root,
            self.settings_manager,
            self.paths,
            self.theme_manager,
            self.materials_data,
            self.labor_data,
            self.runners_data,
        )

        if dialog.has_changes:
            # Reload resources if changed
            self._load_resources()
            self._setup_business_logic()
            self._update_status("Settings updated", timeout=3000)

    def _edit_project_settings(self) -> None:
        """Edit project-specific settings."""
        from .dialogs import ProjectSettingsDialog

        dialog = ProjectSettingsDialog(
            self.root,
            self._current_project.settings
        )

        if dialog.show():
            self._set_modified()
            self._update_status("Project settings updated", timeout=3000)

    def _change_theme(self, theme_name: str) -> None:
        """Change application theme.

        Args:
            theme_name: Name of theme to apply
        """
        self.settings_manager.update_setting('theme', theme_name)
        style = ttk.Style(self.root)
        self.theme_manager.apply_theme(style, theme_name)
        self._update_status(f"Theme changed to {theme_name}", timeout=3000)

    def _open_material_database(self) -> None:
        """Open material database dialog."""
        from .dialogs import MaterialDatabaseDialog

        dialog = MaterialDatabaseDialog(
            self.root,
            self.materials_data,
            self.repository
        )

        if dialog.show():
            self._load_resources()
            self._setup_business_logic()
            self._update_status("Material database updated", timeout=3000)

    def _open_runner_database(self) -> None:
        """Open runner database dialog."""
        from .dialogs import RunnerDatabaseDialog

        dialog = RunnerDatabaseDialog(
            self.root,
            self.runners_data,
            self.repository
        )

        if dialog.show():
            self._load_resources()
            self._update_status("Runner database updated", timeout=3000)

    def _open_hinge_database(self) -> None:
        """Open hinge database dialog."""
        from .dialogs import HingeDatabaseDialog

        dialog = HingeDatabaseDialog(
            self.root,
            self.hinges_data,
            self.repository
        )

        if dialog.show():
            self._load_resources()
            self._update_status("Hinges database updated", timeout=3000)

    def _open_labor_database(self) -> None:
        """Open runner database dialog."""
        from .dialogs import LaborDatabaseDialog

        dialog = LaborDatabaseDialog(
            self.root,
            self.labor_data,
            self.repository
        )

        if dialog.show():
            self._load_resources()
            self._update_status("Runner database updated", timeout=3000)

    def _clean_temp_files(self) -> None:
        """Clean temporary files."""
        count = self.paths.clean_temp_files()
        messagebox.showinfo(
            "Clean Complete",
            f"Removed {count} temporary files."
        )

    # Help methods
    def _show_help(self) -> None:
        """Show help documentation."""
        # TODO: Implement help viewer
        messagebox.showinfo(
            "Help",
            "User guide will be available in a future update.\n\n"
            "For now, please refer to the README file."
        )

    def _show_shortcuts(self) -> None:
        """Show keyboard shortcuts."""
        from .dialogs import ShortcutsDialog

        dialog = ShortcutsDialog(self.root)
        dialog.show()

    # Autosave methods
    def _start_autosave(self) -> None:
        """Start autosave timer."""
        interval = self.settings_manager.settings.autosave_interval * 1000
        self._autosave()
        self.root.after(interval, self._start_autosave)

    def _autosave(self) -> None:
        """Perform autosave."""
        if self._is_modified and self._current_file_path:
            try:
                # Create backup
                backup_path = self.paths.get_backup_file(self._current_file_path)
                import shutil
                shutil.copy2(self._current_file_path, backup_path)

                # Save project
                self._save_project_to_file(self._current_file_path)
                logger.info("Autosave completed")
            except Exception as e:
                logger.error(f"Autosave failed: {e}")

    # Application lifecycle
    def _quit_application(self) -> None:
        """Quit the application."""
        if self._is_modified:
            response = messagebox.askyesnocancel(
                "Save Changes",
                "Save changes before exiting?"
            )
            if response is None:
                return
            elif response:
                if not self._save_project():
                    return

        # Save settings
        self.settings_manager.save_settings()

        logger.info("Application closing")
        self.root.destroy()
