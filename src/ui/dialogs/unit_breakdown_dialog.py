"""Unit breakdown dialog for displaying detailed cost breakdown."""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Dict, Any

from ..base import BaseDialog
from src.business.calculator import UnitBreakdown, QuoteCalculator


class UnitBreakdownDialog(BaseDialog):
    """Dialog for displaying unit-by-unit cost breakdown."""

    def __init__(
            self,
            parent: tk.Widget,
            breakdown: List[UnitBreakdown],
            calculator: QuoteCalculator,
            currency_symbol: str = "£"
    ):
        """Initialize unit breakdown dialog.

        Args:
            parent: Parent widget
            breakdown: List of unit breakdowns
            calculator: Quote calculator
            currency_symbol: Currency symbol
        """
        self.breakdown = breakdown
        self.calculator = calculator
        self.currency_symbol = currency_symbol

        super().__init__(parent, "Unit Breakdown", width=1000, height=700)

    def _create_body(self, parent: ttk.Frame) -> None:
        """Create dialog body."""
        # Summary at top
        self._create_summary(parent)

        # Notebook for different views
        notebook = ttk.Notebook(parent)
        notebook.pack(fill=tk.BOTH, expand=True, pady=10)

        # By unit tab
        unit_frame = ttk.Frame(notebook)
        notebook.add(unit_frame, text="By Unit")
        self._create_unit_tab(unit_frame)

        # By component tab
        component_frame = ttk.Frame(notebook)
        notebook.add(component_frame, text="By Component Type")
        self._create_component_tab(component_frame)

        # Detailed costs tab
        detailed_frame = ttk.Frame(notebook)
        notebook.add(detailed_frame, text="Detailed Costs")
        self._create_detailed_tab(detailed_frame)

    def _create_summary(self, parent: ttk.Frame) -> None:
        """Create summary section."""
        summary_frame = ttk.LabelFrame(parent, text="Summary", padding=10)
        summary_frame.pack(fill=tk.X, padx=10, pady=5)

        # Calculate totals
        total_material = sum(
            unit.unit_material_cost * unit.quantity
            for unit in self.breakdown
        )
        total_labor = sum(
            unit.unit_labor_cost * unit.quantity
            for unit in self.breakdown
        )
        total_units = sum(unit.quantity for unit in self.breakdown)

        # Display summary
        row_frame = ttk.Frame(summary_frame)
        row_frame.pack(fill=tk.X)

        ttk.Label(
            row_frame,
            text=f"Total Units: {total_units}",
            font=('Arial', 11)
        ).pack(side=tk.LEFT, padx=20)

        ttk.Label(
            row_frame,
            text=f"Total Material: {self.currency_symbol}{total_material:,.2f}",
            font=('Arial', 11)
        ).pack(side=tk.LEFT, padx=20)

        ttk.Label(
            row_frame,
            text=f"Total Labor: {self.currency_symbol}{total_labor:,.2f}",
            font=('Arial', 11)
        ).pack(side=tk.LEFT, padx=20)

        ttk.Label(
            row_frame,
            text=f"Total: {self.currency_symbol}{total_material + total_labor:,.2f}",
            font=('Arial', 11, 'bold')
        ).pack(side=tk.LEFT, padx=20)

    def _create_unit_tab(self, parent: ttk.Frame) -> None:
        """Create by-unit breakdown tab."""
        # Create treeview
        columns = ('quantity', 'material', 'labor hours', 'labor cost', 'subtotal', 'total')
        self.unit_tree = ttk.Treeview(
            parent,
            columns=columns,
            show='tree headings'
        )

        # Configure columns
        self.unit_tree.heading('#0', text='Unit / Component', anchor='w')
        self.unit_tree.heading('quantity', text='Qty', anchor='w')
        self.unit_tree.heading('material', text='Material Cost', anchor='w')
        self.unit_tree.heading('labor hours', text='Labor Hours', anchor='w')
        self.unit_tree.heading('labor cost', text='Labor Cost', anchor='w')
        self.unit_tree.heading('subtotal', text='Unit Cost', anchor='w')
        self.unit_tree.heading('total', text='Total Cost', anchor='w')

        self.unit_tree.column('#0', width=300)
        self.unit_tree.column('quantity', width=50)
        self.unit_tree.column('material', width=120)
        self.unit_tree.column('labor hours', width=120)
        self.unit_tree.column('labor cost', width=120)
        self.unit_tree.column('subtotal', width=120)
        self.unit_tree.column('total', width=120)

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            parent,
            orient=tk.VERTICAL,
            command=self.unit_tree.yview
        )
        self.unit_tree.configure(yscrollcommand=scrollbar.set)

        self.unit_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10))

        # Populate tree
        self._populate_unit_tree()

    def _populate_unit_tree(self) -> None:
        """Populate unit breakdown tree."""
        for unit in self.breakdown:
            # Create unit node
            unit_values = (
                unit.quantity,
                f"{self.currency_symbol}{unit.unit_material_cost:.2f}",
                f"{unit.unit_labor_hours:.2f}",
                f"{self.currency_symbol}{unit.unit_labor_cost:.2f}",
                f"{self.currency_symbol}{unit.unit_subtotal:.2f}",
                f"{self.currency_symbol}{unit.total_with_quantity:.2f}"
            )

            unit_node = self.unit_tree.insert(
                '',
                tk.END,
                text=unit.unit_name,
                values=unit_values,
                open=True
            )

            # Add components
            for component in unit.components:
                comp_values = (
                    '',  # No quantity for components
                    f"{self.currency_symbol}{component.material_cost:.2f}",
                    f"{component.labor_hours:.2f}",
                    f"{self.currency_symbol}{component.labor_cost:.2f}",
                    f"{self.currency_symbol}{component.total_cost:.2f}",
                    ''  # No total for components
                )

                comp_text = f"{component.component_name} - {component.dimensions}"
                if component.notes:
                    comp_text += f" ({component.notes})"

                self.unit_tree.insert(
                    unit_node,
                    tk.END,
                    text=comp_text,
                    values=comp_values
                )

    def _create_component_tab(self, parent: ttk.Frame) -> None:
        """Create by-component breakdown tab."""
        # Create treeview
        columns = ('units', 'material_total', 'labor_total', 'total')
        self.component_tree = ttk.Treeview(
            parent,
            columns=columns,
            show='headings'
        )

        # Configure columns
        self.component_tree.heading('units', text='Component Type', anchor='w')
        self.component_tree.heading('material_total', text='Total Material', anchor='w')
        self.component_tree.heading('labor_total', text='Total Labor', anchor='w')
        self.component_tree.heading('total', text='Total Cost', anchor='w')

        self.component_tree.column('units', width=200)
        self.component_tree.column('material_total', width=150)
        self.component_tree.column('labor_total', width=150)
        self.component_tree.column('total', width=150)

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            parent,
            orient=tk.VERTICAL,
            command=self.component_tree.yview
        )
        self.component_tree.configure(yscrollcommand=scrollbar.set)

        self.component_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10))

        # Calculate component totals
        component_totals = {}

        for unit in self.breakdown:
            for component in unit.components:
                comp_type = component.component_name

                if comp_type not in component_totals:
                    component_totals[comp_type] = {
                        'material': 0,
                        'labor': 0,
                        'count': 0
                    }

                component_totals[comp_type]['material'] += component.material_cost * unit.quantity
                component_totals[comp_type]['labor'] += component.labor_cost * unit.quantity
                component_totals[comp_type]['count'] += unit.quantity

        # Populate tree
        for comp_type, totals in component_totals.items():
            total = totals['material'] + totals['labor']

            values = (
                f"{comp_type} (×{totals['count']})",
                f"{self.currency_symbol}{totals['material']:.2f}",
                f"{self.currency_symbol}{totals['labor']:.2f}",
                f"{self.currency_symbol}{total:.2f}"
            )

            self.component_tree.insert('', tk.END, values=values)

    def _create_detailed_tab(self, parent: ttk.Frame) -> None:
        """Create detailed costs tab."""
        # Create text widget for detailed report
        self.detail_text = tk.Text(
            parent,
            wrap=tk.WORD,
            font=('Courier', 10),
            height=25
        )
        self.detail_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            self.detail_text,
            orient=tk.VERTICAL,
            command=self.detail_text.yview
        )
        self.detail_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Generate detailed report
        self._generate_detailed_report()

    def _generate_detailed_report(self) -> None:
        """Generate detailed cost report."""
        self.detail_text.delete(1.0, tk.END)

        # Header
        self.detail_text.insert(tk.END, "DETAILED COST BREAKDOWN\n", 'header')
        self.detail_text.insert(tk.END, "=" * 80 + "\n\n")

        for unit in self.breakdown:
            # Unit header
            self.detail_text.insert(
                tk.END,
                f"{unit.unit_name} (Quantity: {unit.quantity})\n",
                'unit_header'
            )
            self.detail_text.insert(tk.END, "-" * 60 + "\n")

            # Components
            for component in unit.components:
                self.detail_text.insert(tk.END, f"\n{component.component_name}\n", 'component')
                self.detail_text.insert(tk.END, f"  Material: {component.material} {component.thickness}mm\n")
                self.detail_text.insert(tk.END, f"  Dimensions: {component.dimensions}\n")
                self.detail_text.insert(tk.END, f"  Parts: {component.parts_count}\n")
                self.detail_text.insert(tk.END, f"  Total Area: {component.total_area*1e-6:,.2f} m²\n")
                self.detail_text.insert(tk.END,
                                        f"  Material Cost: {self.currency_symbol}{component.material_cost:.2f}\n")
                self.detail_text.insert(tk.END, f"  Labor Hours: {component.labor_hours:.2f}\n")
                self.detail_text.insert(tk.END, f"  Labor Cost: {self.currency_symbol}{component.labor_cost:.2f}\n")
                self.detail_text.insert(tk.END,
                                        f"  Component Total: {self.currency_symbol}{component.total_cost:.2f}\n")

                if component.notes:
                    self.detail_text.insert(tk.END, f"  Notes: {component.notes}\n")

            # Unit totals
            self.detail_text.insert(tk.END, f"\nUnit Totals:\n", 'totals')
            self.detail_text.insert(tk.END, f"  Material: {self.currency_symbol}{unit.unit_material_cost:.2f}\n")
            self.detail_text.insert(tk.END, f"  Labor: {self.currency_symbol}{unit.unit_labor_cost:.2f}\n")
            self.detail_text.insert(tk.END, f"  Per Unit: {self.currency_symbol}{unit.unit_subtotal:.2f}\n")
            self.detail_text.insert(tk.END,
                                    f"  Total (×{unit.quantity}): {self.currency_symbol}{unit.total_with_quantity:.2f}\n")
            self.detail_text.insert(tk.END, "\n" + "=" * 80 + "\n\n")

        # Configure tags
        self.detail_text.tag_configure('header', font=('Courier', 14, 'bold'))
        self.detail_text.tag_configure('unit_header', font=('Courier', 12, 'bold'))
        self.detail_text.tag_configure('component', font=('Courier', 11, 'bold'))
        self.detail_text.tag_configure('totals', font=('Courier', 11, 'bold'))

    def _create_buttons(self, parent: ttk.Frame) -> None:
        """Create dialog buttons."""
        ttk.Button(
            parent,
            text="Export Report",
            command=self._export_report
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            parent,
            text="Print",
            command=self._print_report
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            parent,
            text="Close",
            command=self.dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)

    def _export_report(self) -> None:
        """Export breakdown report."""
        from tkinter import filedialog

        filename = filedialog.asksaveasfilename(
            title="Export Breakdown Report",
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )

        if filename:
            try:
                if filename.endswith('.csv'):
                    self._export_csv(filename)
                else:
                    self._export_text(filename)

                messagebox.showinfo(
                    "Export Complete",
                    f"Report exported to {filename}"
                )

            except Exception as e:
                messagebox.showerror(
                    "Export Error",
                    f"Failed to export report: {str(e)}"
                )

    def _export_csv(self, filename: str) -> None:
        """Export as CSV."""
        import csv

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                'Unit', 'Quantity', 'Component', 'Material', 'Dimensions',
                'Material Cost', 'Labor Hours', 'Labor Cost', 'Total Cost'
            ])

            # Data
            for unit in self.breakdown:
                for component in unit.components:
                    writer.writerow([
                        unit.unit_name,
                        unit.quantity,
                        component.component_name,
                        f"{component.material} {component.thickness}mm",
                        component.dimensions,
                        component.material_cost,
                        component.labor_hours,
                        component.labor_cost,
                        component.total_cost
                    ])

    def _export_text(self, filename: str) -> None:
        """Export as text."""
        content = self.detail_text.get(1.0, tk.END)

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)

    def _print_report(self) -> None:
        """Print the report."""
        # TODO: Implement printing
        messagebox.showinfo(
            "Print",
            "Printing functionality will be implemented in a future update."
        )