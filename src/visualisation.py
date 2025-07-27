import matplotlib.pyplot as plt
import matplotlib.patches as patches
from gene_algorithm import PlacedRectangle, Rectangle
from typing import List
import math


class SheetVisualizer:
    """Visualizes the layout of rectangles on sheets"""

    def __init__(self, sheet_width: float, sheet_height: float):
        self.sheet_width = sheet_width
        self.sheet_height = sheet_height

        # Generate a nice color palette
        self.colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
            '#DDA0DD', '#98D8E8', '#F7DC6F', '#BB8FCE', '#85C1E9',
            '#F8C471', '#82E0AA', '#F1948A', '#85929E', '#D7BDE2'
        ]

    def visualize_sheet(self, sheet: List[PlacedRectangle], sheet_number: int = 1,
                        rectangles: List[Rectangle] = None, show_labels: bool = True,
                        save_path: str = None) -> None:
        """
        Visualize a single sheet with its rectangles

        Args:
            sheet: List of PlacedRectangle objects on this sheet
            sheet_number: Sheet number for title
            rectangles: Original rectangles list to check for rotations
            show_labels: Whether to show rectangle IDs and dimensions
            save_path: Optional path to save the figure
        """
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))

        # Draw sheet boundary
        sheet_rect = patches.Rectangle((0, 0), self.sheet_width, self.sheet_height,
                                       linewidth=2, edgecolor='black', facecolor='lightgray', alpha=0.3)
        ax.add_patch(sheet_rect)

        # Calculate efficiency
        total_area_used = sum(rect.width * rect.height for rect in sheet)
        sheet_area = self.sheet_width * self.sheet_height
        efficiency = (total_area_used / sheet_area) * 100

        # Draw rectangles
        for i, rect in enumerate(sheet):
            color = self.colors[i % len(self.colors)]

            # Create rectangle patch
            rectangle = patches.Rectangle(
                (rect.x, rect.y), rect.width, rect.height,
                linewidth=1.5, edgecolor='black', facecolor=color, alpha=0.7
            )
            ax.add_patch(rectangle)

            if show_labels:
                # Check if rectangle was rotated
                rotation_marker = ""
                if rectangles:
                    original = next((r for r in rectangles if r.id == rect.id), None)
                    if original and rect.width != original.width:
                        rotation_marker = " ↻"

                # Add rectangle ID and dimensions
                center_x = rect.x + rect.width / 2
                center_y = rect.y + rect.height / 2

                # Rectangle ID (larger text)
                ax.text(center_x, center_y + rect.height * 0.1, f'#{rect.id}{rotation_marker}',
                        ha='center', va='center', fontsize=12, fontweight='bold', color='white')

                # Dimensions (smaller text)
                ax.text(center_x, center_y - rect.height * 0.1, f'{rect.width}×{rect.height}',
                        ha='center', va='center', fontsize=9, color='white')

        # Set axis properties
        ax.set_xlim(-5, self.sheet_width + 5)
        ax.set_ylim(-5, self.sheet_height + 5)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('Width', fontsize=12)
        ax.set_ylabel('Height', fontsize=12)

        # Title with efficiency info
        ax.set_title(f'Sheet {sheet_number} Layout\n'
                     f'Efficiency: {efficiency:.1f}% ({len(sheet)} rectangles)',
                     fontsize=14, fontweight='bold')

        # Add legend with rectangle details
        legend_text = []
        for rect in sheet:
            rotation_info = ""
            if rectangles:
                original = next((r for r in rectangles if r.id == rect.id), None)
                if original and rect.width != original.width:
                    rotation_info = " (rotated)"
            legend_text.append(f'#{rect.id}: {rect.width}×{rect.height}{rotation_info}')

        if legend_text:
            ax.text(1.02, 1, '\n'.join(legend_text), transform=ax.transAxes,
                    fontsize=9, verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Sheet {sheet_number} saved to {save_path}")

        plt.show()

    def visualize_all_sheets(self, sheets: List[List[PlacedRectangle]],
                             rectangles: List[Rectangle] = None,
                             save_directory: str = None) -> None:
        """
        Visualize all sheets in a grid layout

        Args:
            sheets: List of sheets, each containing PlacedRectangle objects
            rectangles: Original rectangles list to check for rotations
            save_directory: Optional directory to save individual sheet images
        """
        num_sheets = len(sheets)

        if num_sheets <= 4:
            # Single row for up to 4 sheets
            cols = num_sheets
            rows = 1
        else:
            # Grid layout for more sheets
            cols = 3
            rows = math.ceil(num_sheets / cols)

        fig, axes = plt.subplots(rows, cols, figsize=(6 * cols, 5 * rows))

        # Handle single sheet case
        if num_sheets == 1:
            axes = [axes]
        elif rows == 1:
            axes = axes if hasattr(axes, '__len__') else [axes]
        else:
            axes = axes.flatten()

        for sheet_idx, sheet in enumerate(sheets):
            ax = axes[sheet_idx] if num_sheets > 1 else axes[0]

            # Draw sheet boundary
            sheet_rect = patches.Rectangle((0, 0), self.sheet_width, self.sheet_height,
                                           linewidth=2, edgecolor='black', facecolor='lightgray', alpha=0.3)
            ax.add_patch(sheet_rect)

            # Calculate efficiency
            total_area_used = sum(rect.width * rect.height for rect in sheet)
            sheet_area = self.sheet_width * self.sheet_height
            efficiency = (total_area_used / sheet_area) * 100

            # Draw rectangles
            for i, rect in enumerate(sheet):
                color = self.colors[i % len(self.colors)]

                rectangle = patches.Rectangle(
                    (rect.x, rect.y), rect.width, rect.height,
                    linewidth=1, edgecolor='black', facecolor=color, alpha=0.7
                )
                ax.add_patch(rectangle)

                # Add rectangle ID
                center_x = rect.x + rect.width / 2
                center_y = rect.y + rect.height / 2

                # Check for rotation marker
                rotation_marker = ""
                if rectangles:
                    original = next((r for r in rectangles if r.id == rect.id), None)
                    if original and rect.width != original.width:
                        rotation_marker = "↻"

                ax.text(center_x, center_y, f'{rect.id}{rotation_marker}',
                        ha='center', va='center', fontsize=10, fontweight='bold', color='white')

            # Set axis properties
            ax.set_xlim(-2, self.sheet_width + 2)
            ax.set_ylim(-2, self.sheet_height + 2)
            ax.set_aspect('equal')
            ax.grid(True, alpha=0.3)
            ax.set_title(f'Sheet {sheet_idx + 1}\n{efficiency:.1f}% efficient',
                         fontsize=12, fontweight='bold')

        # Hide unused subplots
        for i in range(num_sheets, len(axes)):
            axes[i].set_visible(False)

        plt.tight_layout()
        plt.suptitle(f'All Sheets Overview ({num_sheets} sheets total)',
                     fontsize=16, fontweight='bold', y=1.02)

        if save_directory:
            import os
            os.makedirs(save_directory, exist_ok=True)
            plt.savefig(f"{save_directory}/all_sheets_overview.png", dpi=300, bbox_inches='tight')
            print(f"Overview saved to {save_directory}/all_sheets_overview.png")

        plt.show()

        # Optionally create individual detailed sheets
        if save_directory:
            for sheet_idx, sheet in enumerate(sheets):
                save_path = f"{save_directory}/sheet_{sheet_idx + 1}_detailed.png"
                self.visualize_sheet(sheet, sheet_idx + 1, rectangles, save_path=save_path)

    def create_cutting_diagram(self, sheets: List[List[PlacedRectangle]],
                               rectangles: List[Rectangle] = None,
                               save_path: str = None) -> None:
        """
        Create a technical cutting diagram suitable for workshop use
        """
        num_sheets = len(sheets)
        fig, axes = plt.subplots(1, num_sheets, figsize=(8 * num_sheets, 6))

        if num_sheets == 1:
            axes = [axes]

        for sheet_idx, sheet in enumerate(sheets):
            ax = axes[sheet_idx]

            # Draw sheet outline (thicker for cutting reference)
            sheet_rect = patches.Rectangle((0, 0), self.sheet_width, self.sheet_height,
                                           linewidth=3, edgecolor='black', facecolor='none')
            ax.add_patch(sheet_rect)

            # Draw rectangles with technical styling
            for rect in sheet:
                rectangle = patches.Rectangle(
                    (rect.x, rect.y), rect.width, rect.height,
                    linewidth=2, edgecolor='red', facecolor='lightblue', alpha=0.3,
                    linestyle='--'
                )
                ax.add_patch(rectangle)

                # Add detailed measurements and position info
                center_x = rect.x + rect.width / 2
                center_y = rect.y + rect.height / 2

                # Rectangle ID and position
                ax.text(center_x, center_y + rect.height * 0.2, f'#{rect.id}',
                        ha='center', va='center', fontsize=14, fontweight='bold')
                ax.text(center_x, center_y, f'{rect.width} × {rect.height}',
                        ha='center', va='center', fontsize=10)
                ax.text(center_x, center_y - rect.height * 0.2, f'@({rect.x}, {rect.y})',
                        ha='center', va='center', fontsize=8, style='italic')

                # Add dimension lines (optional - can be toggled)
                # Left edge dimension
                ax.annotate('', xy=(rect.x, rect.y), xytext=(rect.x, rect.y + rect.height),
                            arrowprops=dict(arrowstyle='<->', color='blue', lw=1))
                ax.text(rect.x - 3, center_y, f'{rect.height}',
                        ha='right', va='center', fontsize=8, rotation=90, color='blue')

                # Bottom edge dimension
                ax.annotate('', xy=(rect.x, rect.y), xytext=(rect.x + rect.width, rect.y),
                            arrowprops=dict(arrowstyle='<->', color='blue', lw=1))
                ax.text(center_x, rect.y - 3, f'{rect.width}',
                        ha='center', va='top', fontsize=8, color='blue')

            # Technical drawing styling
            ax.set_xlim(-10, self.sheet_width + 10)
            ax.set_ylim(-10, self.sheet_height + 10)
            ax.set_aspect('equal')
            ax.grid(True, alpha=0.5, linestyle=':')
            ax.set_xlabel('Width (mm)', fontsize=12)
            ax.set_ylabel('Height (mm)', fontsize=12)
            ax.set_title(f'CUTTING SHEET {sheet_idx + 1}\n{self.sheet_width} × {self.sheet_height} mm',
                         fontsize=14, fontweight='bold')

            # Add sheet dimensions
            # ax.text(self.sheet_width / 2, -15, f'Sheet Width: {self.sheet_width} mm',
            #         ha='center', fontsize=10, fontweight='bold')
            # ax.text(-15, self.sheet_height / 2, f'Sheet Height: {self.sheet_height} mm',
            #         ha='center', va='center', rotation=90, fontsize=10, fontweight='bold')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Cutting diagram saved to {save_path}")

        plt.show()
