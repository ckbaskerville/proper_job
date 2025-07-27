"""Export dialog for various export options."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Any, Optional
from datetime import datetime
import json
import csv
from pathlib import Path

from ..base import BaseDialog
from src.models import Project
from src.business.calculator import QuoteCalculator, QuoteResult
from src.config import Settings, COMPANY_INFO, QUOTE_TERMS


class ExportDialog(BaseDialog):
    """Dialog for exporting project data."""

    def __init__(
            self,
            parent: tk.Widget,
            project: Project,
            quote: Optional[QuoteResult],
            calculator: QuoteCalculator,
            settings: Settings
    ):
        """Initialize export dialog.

        Args:
            parent: Parent widget
            project: Current project
            quote: Quote result (optional)
            calculator: Quote calculator
            settings: Application settings
        """
        self.project = project
        self.quote = quote
        self.calculator = calculator
        self.settings = settings
        self.export_successful = False

        super().__init__(parent, "Export Project", width=600, height=500)

    def _create_body(self, parent: ttk.Frame) -> None:
        """Create dialog body."""
        # Export type selection
        type_frame = ttk.LabelFrame(parent, text="Export Type", padding=10)
        type_frame.pack(fill=tk.X, padx=10, pady=5)

        self.export_type_var = tk.StringVar(value="quote_pdf")

        ttk.Radiobutton(
            type_frame,
            text="Quote PDF",
            variable=self.export_type_var,
            value="quote_pdf",
            command=self._on_type_changed
        ).pack(anchor=tk.W, pady=2)

        ttk.Radiobutton(
            type_frame,
            text="Cut List (CSV)",
            variable=self.export_type_var,
            value="cut_list_csv",
            command=self._on_type_changed
        ).pack(anchor=tk.W, pady=2)

        ttk.Radiobutton(
            type_frame,
            text="Project Data (JSON)",
            variable=self.export_type_var,
            value="project_json",
            command=self._on_type_changed
        ).pack(anchor=tk.W, pady=2)

        ttk.Radiobutton(
            type_frame,
            text="Material Summary (Excel)",
            variable=self.export_type_var,
            value="material_excel",
            command=self._on_type_changed
        ).pack(anchor=tk.W, pady=2)

        ttk.Radiobutton(
            type_frame,
            text="Complete Report (ZIP)",
            variable=self.export_type_var,
            value="complete_zip",
            command=self._on_type_changed
        ).pack(anchor=tk.W, pady=2)

        # Options frame
        self.options_frame = ttk.LabelFrame(parent, text="Export Options", padding=10)
        self.options_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Default options
        self._create_pdf_options()

        # File location
        location_frame = ttk.LabelFrame(parent, text="Save Location", padding=10)
        location_frame.pack(fill=tk.X, padx=10, pady=5)

        self.filename_var = tk.StringVar()
        self._update_default_filename()

        ttk.Label(location_frame, text="Filename:").pack(anchor=tk.W)

        file_frame = ttk.Frame(location_frame)
        file_frame.pack(fill=tk.X, pady=5)

        ttk.Entry(
            file_frame,
            textvariable=self.filename_var,
            state="readonly"
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(
            file_frame,
            text="Browse...",
            command=self._browse_location
        ).pack(side=tk.LEFT, padx=(5, 0))

    def _on_type_changed(self) -> None:
        """Handle export type change."""
        # Clear options frame
        for widget in self.options_frame.winfo_children():
            widget.destroy()

        # Create appropriate options
        export_type = self.export_type_var.get()

        if export_type == "quote_pdf":
            self._create_pdf_options()
        elif export_type == "cut_list_csv":
            self._create_csv_options()
        elif export_type == "material_excel":
            self._create_excel_options()
        elif export_type == "complete_zip":
            self._create_zip_options()

        # Update default filename
        self._update_default_filename()

    def _create_pdf_options(self) -> None:
        """Create PDF export options."""
        # Include options
        self.include_summary_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            self.options_frame,
            text="Include quote summary",
            variable=self.include_summary_var
        ).pack(anchor=tk.W, pady=2)

        self.include_breakdown_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            self.options_frame,
            text="Include unit breakdown",
            variable=self.include_breakdown_var
        ).pack(anchor=tk.W, pady=2)

        self.include_cutlist_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            self.options_frame,
            text="Include cut list",
            variable=self.include_cutlist_var
        ).pack(anchor=tk.W, pady=2)

        self.include_diagrams_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            self.options_frame,
            text="Include cutting diagrams",
            variable=self.include_diagrams_var
        ).pack(anchor=tk.W, pady=2)

        # Company info
        company_frame = ttk.LabelFrame(self.options_frame, text="Company Information", padding=5)
        company_frame.pack(fill=tk.X, pady=10)

        ttk.Label(company_frame, text="Company Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.company_name_var = tk.StringVar(value=COMPANY_INFO['name'])
        ttk.Entry(company_frame, textvariable=self.company_name_var, width=40).grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(company_frame, text="Address:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.company_address_var = tk.StringVar(value=COMPANY_INFO['address'])
        ttk.Entry(company_frame, textvariable=self.company_address_var, width=40).grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(company_frame, text="Phone:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.company_phone_var = tk.StringVar(value=COMPANY_INFO['phone'])
        ttk.Entry(company_frame, textvariable=self.company_phone_var, width=40).grid(row=2, column=1, padx=5, pady=2)

    def _create_csv_options(self) -> None:
        """Create CSV export options."""
        self.csv_separator_var = tk.StringVar(value=",")

        ttk.Label(self.options_frame, text="CSV Separator:").pack(anchor=tk.W)

        sep_frame = ttk.Frame(self.options_frame)
        sep_frame.pack(fill=tk.X, pady=5)

        ttk.Radiobutton(sep_frame, text="Comma (,)", variable=self.csv_separator_var, value=",").pack(side=tk.LEFT,
                                                                                                      padx=5)
        ttk.Radiobutton(sep_frame, text="Semicolon (;)", variable=self.csv_separator_var, value=";").pack(side=tk.LEFT,
                                                                                                          padx=5)
        ttk.Radiobutton(sep_frame, text="Tab", variable=self.csv_separator_var, value="\t").pack(side=tk.LEFT, padx=5)

        self.include_headers_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            self.options_frame,
            text="Include column headers",
            variable=self.include_headers_var
        ).pack(anchor=tk.W, pady=5)

        self.group_by_material_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            self.options_frame,
            text="Group by material",
            variable=self.group_by_material_var
        ).pack(anchor=tk.W, pady=2)

    def _create_excel_options(self) -> None:
        """Create Excel export options."""
        self.excel_sheets_var = tk.StringVar(value="all")

        ttk.Label(self.options_frame, text="Include sheets:").pack(anchor=tk.W, pady=5)

        ttk.Radiobutton(
            self.options_frame,
            text="All data in separate sheets",
            variable=self.excel_sheets_var,
            value="all"
        ).pack(anchor=tk.W, padx=20, pady=2)

        ttk.Radiobutton(
            self.options_frame,
            text="Summary only",
            variable=self.excel_sheets_var,
            value="summary"
        ).pack(anchor=tk.W, padx=20, pady=2)

        ttk.Radiobutton(
            self.options_frame,
            text="Detailed breakdown",
            variable=self.excel_sheets_var,
            value="detailed"
        ).pack(anchor=tk.W, padx=20, pady=2)

        self.include_charts_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            self.options_frame,
            text="Include charts",
            variable=self.include_charts_var
        ).pack(anchor=tk.W, pady=5)

    def _create_zip_options(self) -> None:
        """Create ZIP export options."""
        ttk.Label(
            self.options_frame,
            text="This will create a complete export package including:",
            wraplength=400
        ).pack(anchor=tk.W, pady=5)

        options_text = """• Quote PDF
        - Cut list (CSV and Excel)
        - Material summary
        - Cutting diagrams
        - Project file (JSON)
        - Cost breakdown report"""

        ttk.Label(
            self.options_frame,
            text=options_text,
            justify=tk.LEFT
        ).pack(anchor=tk.W, padx=20, pady=5)

        self.open_folder_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            self.options_frame,
            text="Open folder after export",
            variable=self.open_folder_var
        ).pack(anchor=tk.W, pady=10)

    def _update_default_filename(self) -> None:
        """Update default filename based on export type."""
        export_type = self.export_type_var.get()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_name = self.project.name.replace(" ", "_")

        extensions = {
            "quote_pdf": ".pdf",
            "cut_list_csv": ".csv",
            "project_json": ".json",
            "material_excel": ".xlsx",
            "complete_zip": ".zip"
        }

        ext = extensions.get(export_type, ".txt")
        filename = f"{project_name}_export_{timestamp}{ext}"

        # Use last export directory if available
        if self.settings.last_export_directory:
            filepath = Path(self.settings.last_export_directory) / filename
        else:
            filepath = Path.home() / "Documents" / filename

        self.filename_var.set(str(filepath))

    def _browse_location(self) -> None:
        """Browse for save location."""
        export_type = self.export_type_var.get()

        filetypes = {
            "quote_pdf": [("PDF files", "*.pdf")],
            "cut_list_csv": [("CSV files", "*.csv")],
            "project_json": [("JSON files", "*.json")],
            "material_excel": [("Excel files", "*.xlsx")],
            "complete_zip": [("ZIP files", "*.zip")]
        }

        filename = filedialog.asksaveasfilename(
            title="Export Location",
            defaultextension=Path(self.filename_var.get()).suffix,
            initialfile=Path(self.filename_var.get()).name,
            filetypes=filetypes.get(export_type, [("All files", "*.*")])
        )

        if filename:
            self.filename_var.set(filename)

    def _create_buttons(self, parent: ttk.Frame) -> None:
        """Create dialog buttons."""
        ttk.Button(
            parent,
            text="Export",
            command=self._do_export,
            style='Accent.TButton'
        ).pack(side=tk.RIGHT, padx=(5, 0))

        ttk.Button(
            parent,
            text="Cancel",
            command=self.dialog.destroy
        ).pack(side=tk.RIGHT)

    def _do_export(self) -> None:
        """Perform the export."""
        if not self.filename_var.get():
            messagebox.showerror("Error", "Please select a save location")
            return

        export_type = self.export_type_var.get()

        try:
            if export_type == "quote_pdf":
                self._export_pdf()
            elif export_type == "cut_list_csv":
                self._export_csv()
            elif export_type == "project_json":
                self._export_json()
            elif export_type == "material_excel":
                self._export_excel()
            elif export_type == "complete_zip":
                self._export_zip()

            self.export_successful = True

            # Update last export directory
            export_path = Path(self.filename_var.get())
            self.settings.last_export_directory = str(export_path.parent)

            messagebox.showinfo(
                "Export Complete",
                f"Export saved to:\n{self.filename_var.get()}"
            )

            self.dialog.destroy()

        except Exception as e:
            messagebox.showerror(
                "Export Error",
                f"Failed to export: {str(e)}"
            )

    def _export_pdf(self) -> None:
        """Export as PDF."""
        # This would require a PDF library like reportlab
        # For now, create a text file as placeholder
        filepath = Path(self.filename_var.get())

        with open(filepath.with_suffix('.txt'), 'w', encoding='utf-8') as f:
            f.write(f"QUOTE - {self.project.name}\n")
            f.write("=" * 60 + "\n\n")

            # Company info
            f.write(f"{self.company_name_var.get()}\n")
            f.write(f"{self.company_address_var.get()}\n")
            f.write(f"{self.company_phone_var.get()}\n\n")

            # Quote summary
            if self.quote and self.include_summary_var.get():
                f.write("QUOTE SUMMARY\n")
                f.write("-" * 40 + "\n")
                f.write(f"Units: {self.quote.units_count}\n")
                f.write(f"Material Cost: {self.settings.currency_symbol}{self.quote.material_cost:.2f}\n")
                f.write(f"Labor Cost: {self.settings.currency_symbol}{self.quote.labor_cost:.2f}\n")
                f.write(f"Subtotal: {self.settings.currency_symbol}{self.quote.subtotal:.2f}\n")
                f.write(f"Markup ({self.quote.markup}%): {self.settings.currency_symbol}{self.quote.markup:.2f}\n")
                f.write(f"TOTAL: {self.settings.currency_symbol}{self.quote.total:.2f}\n\n")

            # Terms
            f.write("TERMS & CONDITIONS\n")
            f.write("-" * 40 + "\n")
            for term in QUOTE_TERMS:
                f.write(f"• {term}\n")

    def _export_csv(self) -> None:
        """Export cut list as CSV."""
        filepath = Path(self.filename_var.get())
        separator = self.csv_separator_var.get()

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=separator)

            # Header
            if self.include_headers_var.get():
                writer.writerow([
                    'Part ID', 'Cabinet', 'Component', 'Material',
                    'Width (mm)', 'Height (mm)', 'Quantity'
                ])

            # Parts
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

    def _export_json(self) -> None:
        """Export project as JSON."""
        filepath = Path(self.filename_var.get())
        self.project.save_to_file(filepath)

    def _export_excel(self) -> None:
        """Export as Excel file."""
        # This would require openpyxl or xlsxwriter
        # For now, export as CSV
        self._export_csv()

    def _export_zip(self) -> None:
        """Export complete package as ZIP."""
        import zipfile
        import tempfile
        import os

        filepath = Path(self.filename_var.get())

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Export various formats
            # PDF
            pdf_path = temp_path / f"{self.project.name}_quote.txt"
            self.filename_var.set(str(pdf_path))
            self._export_pdf()

            # CSV
            csv_path = temp_path / f"{self.project.name}_cutlist.csv"
            self.filename_var.set(str(csv_path))
            self._export_csv()

            # JSON
            json_path = temp_path / f"{self.project.name}_project.json"
            self.filename_var.set(str(json_path))
            self._export_json()

            # Create ZIP
            with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
                for file in temp_path.iterdir():
                    if file.is_file():
                        zf.write(file, file.name)

            # Reset filename
            self.filename_var.set(str(filepath))

            # Open folder if requested
            if self.open_folder_var.get():
                import subprocess
                import platform

                if platform.system() == 'Windows':
                    subprocess.Popen(['explorer', str(filepath.parent)])
                elif platform.system() == 'Darwin':  # macOS
                    subprocess.Popen(['open', str(filepath.parent)])
                else:  # Linux
                    subprocess.Popen(['xdg-open', str(filepath.parent)])

    def export(self) -> bool:
        """Show dialog and return True if export was successful."""
        self.dialog.wait_window()
        return self.export_successful