"""Cut list dialog for displaying optimized cutting layouts."""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, List

from ..base import BaseDialog
from src.business.calculator import QuoteCalculator
from src.models import Project


class CutListDialog(BaseDialog):
    """Dialog for displaying cut list information."""

    def __init__(
            self,
            parent: tk.Widget,
            quote: Dict[str, Any],
            calculator: QuoteCalculator,
            project: Project
    ):
        """Initialize cut list dialog.

        Args:
            parent: Parent widget
            quote: Quote data
            calculator: Quote calculator with optimization results
            project: Current project
        """
        self.quote = quote
        self.calculator = calculator
        self.project = project

        super().__init__(parent, "Cut List", width=900, height=600)

    def _create_body(self, parent: ttk.Frame) -> None:
        """Create dialog body."""
        # Notebook for different views
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Summary tab
        summary_frame = ttk.Frame(notebook)
        notebook.add(summary_frame, text="Summary")
        self._create_summary_tab(summary_frame)

        # Detailed cut list tab
        detailed_frame = ttk.Frame(notebook)
        notebook.add(detailed_frame, text="Detailed Cut List")
        self._create_detailed_tab(detailed_frame)

        # By sheet tab
        sheet_frame = ttk.Frame(notebook)
        notebook.add(sheet_frame, text="By Sheet")
        self._create_sheet_tab(sheet_frame)

    def _create_summary_tab(self, parent: ttk.Frame) -> None:
        """Create summary tab."""
        # Title
        ttk.Label(
            parent,
            text="Cut List Summary",
            font=('Arial', 14, 'bold')
        ).pack(pady=10)

        # Summary frame
        summary_frame = ttk.LabelFrame(parent, text="Material Summary", padding=10)
        summary_frame.pack(fill=tk.X, padx=10, pady=5)

        # Create treeview for summary
        columns = ('material', 'thickness', 'sheets', 'parts', 'efficiency', 'cost')
        self.summary_tree = ttk.Treeview(
            summary_frame,
            columns=columns,
            show='headings',
            height=10
        )

        # Configure columns
        self.summary_tree.heading('material', text='Material', anchor='w')
        self.summary_tree.heading('thickness', text='Thickness (mm)', anchor='w')
        self.summary_tree.heading('sheets', text='Sheets', anchor='w')
        self.summary_tree.heading('parts', text='Parts', anchor='w')
        self.summary_tree.heading('efficiency', text='Efficiency', anchor='w')
        self.summary_tree.heading('cost', text='Cost', anchor='w')

        self.summary_tree.column('material', width=150)
        self.summary_tree.column('thickness', width=100)
        self.summary_tree.column('sheets', width=80)
        self.summary_tree.column('parts', width=80)
        self.summary_tree.column('efficiency', width=100)
        self.summary_tree.column('cost', width=100)

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            summary_frame,
            orient=tk.VERTICAL,
            command=self.summary_tree.yview
        )
        self.summary_tree.configure(yscrollcommand=scrollbar.set)

        self.summary_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Populate summary
        self._populate_summary()

        # Totals
        totals_frame = ttk.Frame(parent)
        totals_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(
            totals_frame,
            text=f"Total Sheets: {self.quote['total_sheets_required']}",
            font=('Arial', 11, 'bold')
        ).pack(side=tk.LEFT, padx=10)

        ttk.Label(
            totals_frame,
            text=f"Total Material Cost: £{self.quote['material_cost']:.2f}",
            font=('Arial', 11, 'bold')
        ).pack(side=tk.LEFT, padx=10)

    def _populate_summary(self) -> None:
        """Populate summary tree."""
        sheets_breakdown = self.quote.get('sheets_breakdown', {})

        for (material, thickness), data in sheets_breakdown.items():
            efficiency = data.get('efficiency', 0) * 100

            values = (
                material,
                thickness,
                data['sheets_required'],
                data['parts_count'],
                f"{efficiency:.1f}%",
                f"£{data['material_cost']:.2f}"
            )

            self.summary_tree.insert('', tk.END, values=values)

    def _create_detailed_tab(self, parent: ttk.Frame) -> None:
        """Create detailed cut list tab."""
        # Controls
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(control_frame, text="Group by:").pack(side=tk.LEFT, padx=5)

        self.group_var = tk.StringVar(value="Cabinet")
        ttk.Combobox(
            control_frame,
            textvariable=self.group_var,
            values=["Cabinet", "Material", "Size"],
            state="readonly",
            width=15
        ).pack(side=tk.LEFT)

        ttk.Button(
            control_frame,
            text="Export CSV",
            command=self._export_detailed_csv
        ).pack(side=tk.RIGHT, padx=5)

        # Detailed tree
        columns = ('id', 'cabinet', 'component', 'material', 'dimensions', 'quantity')
        self.detailed_tree = ttk.Treeview(
            parent,
            columns=columns,
            show='tree headings',
            height=20
        )

        # Configure columns
        self.detailed_tree.heading('#0', text='Group', anchor='w')
        self.detailed_tree.heading('id', text='Part ID', anchor='w')
        self.detailed_tree.heading('cabinet', text='Cabinet', anchor='w')
        self.detailed_tree.heading('component', text='Component', anchor='w')
        self.detailed_tree.heading('material', text='Material', anchor='w')
        self.detailed_tree.heading('dimensions', text='Dimensions (mm)', anchor='w')
        self.detailed_tree.heading('quantity', text='Quantity', anchor='w')

        self.detailed_tree.column('#0', width=150)
        self.detailed_tree.column('id', width=100)
        self.detailed_tree.column('cabinet', width=120)
        self.detailed_tree.column('component', width=100)
        self.detailed_tree.column('material', width=120)
        self.detailed_tree.column('dimensions', width=120)
        self.detailed_tree.column('quantity', width=50)

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            parent,
            orient=tk.VERTICAL,
            command=self.detailed_tree.yview
        )
        self.detailed_tree.configure(yscrollcommand=scrollbar.set)

        self.detailed_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10))

        # Populate detailed list
        self._populate_detailed()

    def _populate_detailed(self) -> None:
        """Populate detailed cut list."""
        # Clear existing
        for item in self.detailed_tree.get_children():
            self.detailed_tree.delete(item)

        # Group parts by cabinet
        for cab_idx, cabinet in enumerate(self.project.cabinets):
            # Create cabinet node
            cab_node = self.detailed_tree.insert(
                '',
                tk.END,
                text=f"{cabinet.carcass.name} (×{cabinet.quantity})",
                open=True
            )

            # Add carcass parts
            carcass_node = self.detailed_tree.insert(
                cab_node,
                tk.END,
                text="Carcass"
            )

            for part in cabinet.carcass.get_parts():
                values = (
                    part.id,
                    cabinet.carcass.name,
                    "Carcass",
                    f"{cabinet.carcass.material} {cabinet.carcass.material_thickness}mm",
                    f"{part.width:.0f} × {part.height:.0f}",
                    cabinet.quantity
                )
                self.detailed_tree.insert(carcass_node, tk.END, values=values)

            # Add drawer parts
            if cabinet.drawers:
                drawers_node = self.detailed_tree.insert(
                    cab_node,
                    tk.END,
                    text="Drawers"
                )

                for drawer in cabinet.drawers:
                    for part in drawer.get_parts():
                        values = (
                            part.id,
                            cabinet.carcass.name,
                            "Drawer",
                            f"{drawer.material} {drawer.thickness}mm",
                            f"{part.width:.0f} × {part.height:.0f}",
                            cabinet.quantity
                        )
                        self.detailed_tree.insert(drawers_node, tk.END, values=values)

            # Add door parts
            if cabinet.doors and cabinet.doors.quantity > 0:
                doors_node = self.detailed_tree.insert(
                    cab_node,
                    tk.END,
                    text="Doors"
                )

                for part in cabinet.doors.get_parts():
                    values = (
                        part.id,
                        cabinet.carcass.name,
                        "Door",
                        f"{cabinet.doors.material} {cabinet.doors.material_thickness}mm",
                        f"{part.width:.0f} × {part.height:.0f}",
                        cabinet.quantity
                    )
                    self.detailed_tree.insert(doors_node, tk.END, values=values)

            # Add face frame parts
            if cabinet.face_frame:
                face_frame_node = self.detailed_tree.insert(
                    cab_node,
                    tk.END,
                    text="Face Frame"
                )

                for part in cabinet.face_frame.get_parts():
                    values = (
                        part.id,
                        cabinet.carcass.name,
                        "Face Frame",
                        f"{cabinet.face_frame.material} {cabinet.face_frame.thickness}mm",
                        f"{part.width:.0f} × {part.height:.0f}",
                        cabinet.quantity
                    )
                    self.detailed_tree.insert(face_frame_node, tk.END, values=values)

    def _create_sheet_tab(self, parent: ttk.Frame) -> None:
        """Create by-sheet tab."""
        # Material selector
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(control_frame, text="Material:").pack(side=tk.LEFT, padx=5)

        self.sheet_material_var = tk.StringVar()
        materials = list(self.calculator._sheets_by_material.keys())

        material_strings = [f"{mat} {thick}mm" for mat, thick in materials]

        self.material_combo = ttk.Combobox(
            control_frame,
            textvariable=self.sheet_material_var,
            values=material_strings,
            state="readonly",
            width=25
        )
        self.material_combo.pack(side=tk.LEFT, padx=5)
        self.material_combo.bind('<<ComboboxSelected>>', self._on_material_selected)

        ttk.Button(
            control_frame,
            text="Export All Sheets",
            command=self._export_all_sheets
        ).pack(side=tk.RIGHT, padx=5)

        # Sheet display
        self.sheet_text = tk.Text(
            parent,
            wrap=tk.NONE,
            font=('Courier', 10),
            height=25
        )
        self.sheet_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(
            self.sheet_text,
            orient=tk.VERTICAL,
            command=self.sheet_text.yview
        )
        h_scrollbar = ttk.Scrollbar(
            self.sheet_text,
            orient=tk.HORIZONTAL,
            command=self.sheet_text.xview
        )

        self.sheet_text.configure(
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set
        )

        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Select first material if available
        if material_strings:
            self.sheet_material_var.set(material_strings[0])
            self._on_material_selected()

    def _on_material_selected(self, event=None) -> None:
        """Handle material selection for sheet view."""
        material_str = self.sheet_material_var.get()
        if not material_str:
            return

        # Parse material and thickness
        parts = material_str.rsplit(' ', 1)
        material = parts[0]
        thickness = float(parts[1].replace('mm', ''))

        # Get sheets for this material
        key = (material, thickness)
        sheets = self.calculator._sheets_by_material.get(key, [])

        # Clear text
        self.sheet_text.delete(1.0, tk.END)

        # Display sheets
        for sheet_idx, sheet in enumerate(sheets):
            self.sheet_text.insert(tk.END, f"Sheet {sheet_idx + 1}\n")
            self.sheet_text.insert(tk.END, "=" * 60 + "\n")

            # Calculate efficiency
            sheet_area = self.calculator.sheet_width * self.calculator.sheet_height
            used_area = sum(rect.width * rect.height for rect in sheet)
            efficiency = (used_area / sheet_area) * 100

            self.sheet_text.insert(
                tk.END,
                f"Efficiency: {efficiency:.1f}% | Parts: {len(sheet)}\n\n"
            )

            # List parts
            for rect in sheet:
                self.sheet_text.insert(
                    tk.END,
                    f"  {rect.id}: {rect.width:.0f} × {rect.height:.0f} mm "
                    f"at ({rect.x:.0f}, {rect.y:.0f})\n"
                )

            self.sheet_text.insert(tk.END, "\n")

    def _export_detailed_csv(self) -> None:
        """Export detailed cut list to CSV."""
        from tkinter import filedialog
        import csv

        filename = filedialog.asksaveasfilename(
            title="Export Cut List",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)

                    # Header
                    writer.writerow([
                        'Part ID', 'Cabinet', 'Component', 'Material',
                        'Width (mm)', 'Height (mm)', 'Quantity'
                    ])

                    # Write parts
                    for cabinet in self.project.cabinets:
                        # Carcass parts
                        for part in cabinet.carcass.get_parts():
                            writer.writerow([
                                part.id,
                                cabinet.carcass.name,
                                'Carcass',
                                f"{cabinet.carcass.material} {cabinet.carcass.material_thickness}mm",
                                part.width,
                                part.height,
                                cabinet.quantity
                            ])

                        # Drawer parts
                        for drawer in cabinet.drawers:
                            for part in drawer.get_parts():
                                writer.writerow([
                                    part.id,
                                    cabinet.carcass.name,
                                    'Drawer',
                                    f"{drawer.material} {drawer.thickness}mm",
                                    part.width,
                                    part.height,
                                    cabinet.quantity
                                ])

                        # Door parts
                        for part in cabinet.doors.get_parts():
                            writer.writerow([
                                part.id,
                                cabinet.carcass.name,
                                'Door',
                                f"{cabinet.doors.material} {cabinet.doors.material_thickness}mm",
                                part.width,
                                part.height,
                                cabinet.quantity
                            ])

                        for part in cabinet.face_frame.get_parts():
                            writer.writerow([
                                part.id,
                                cabinet.carcass.name,
                                'Face Frame',
                                f"{cabinet.face_frame.material} {cabinet.face_frame.thickness}mm",
                                part.width,
                                part.height,
                                cabinet.quantity
                            ])

                messagebox.showinfo(
                    "Export Complete",
                    f"Cut list exported to {filename}"
                )

            except Exception as e:
                messagebox.showerror(
                    "Export Error",
                    f"Failed to export cut list: {str(e)}"
                )

    def _export_all_sheets(self) -> None:
        """Export all sheet layouts."""
        from tkinter import filedialog

        directory = filedialog.askdirectory(
            title="Select Export Directory"
        )

        if directory:
            try:
                import os

                for (material, thickness), sheets in self.calculator._sheets_by_material.items():
                    # Create file for each material
                    filename = f"{material}_{thickness}mm_sheets.txt"
                    filepath = os.path.join(directory, filename)

                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(f"Sheet Layout for {material} {thickness}mm\n")
                        f.write("=" * 60 + "\n\n")

                        for sheet_idx, sheet in enumerate(sheets):
                            f.write(f"Sheet {sheet_idx + 1}\n")
                            f.write("-" * 40 + "\n")

                            # Calculate efficiency
                            sheet_area = self.calculator.sheet_width * self.calculator.sheet_height
                            used_area = sum(rect.width * rect.height for rect in sheet)
                            efficiency = (used_area / sheet_area) * 100

                            f.write(f"Efficiency: {efficiency:.1f}%\n")
                            f.write(f"Parts: {len(sheet)}\n\n")

                            # List parts
                            for rect in sheet:
                                f.write(
                                    f"  {rect.id}: {rect.width:.0f} × {rect.height:.0f} mm "
                                    f"at ({rect.x:.0f}, {rect.y:.0f})\n"
                                )

                            f.write("\n")

                messagebox.showinfo(
                    "Export Complete",
                    f"Sheet layouts exported to {directory}"
                )

            except Exception as e:
                messagebox.showerror(
                    "Export Error",
                    f"Failed to export sheets: {str(e)}"
                )

    def _create_buttons(self, parent: ttk.Frame) -> None:
        """Create dialog buttons."""
        ttk.Button(
            parent,
            text="Print",
            command=self._print_cut_list
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            parent,
            text="Close",
            command=self.dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)

    def _print_cut_list(self) -> None:
        """Print cut list."""
        # TODO: Implement printing functionality
        messagebox.showinfo(
            "Print",
            "Printing functionality will be implemented in a future update."
        )