import random
import math
from typing import List, Tuple, Optional
from dataclasses import dataclass
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import ListedColormap
import numpy as np


@dataclass
class Rectangle:
    """Represents a rectangle to be packed"""
    width: float
    height: float
    id: int = 0

    def area(self) -> float:
        return self.width * self.height

    def rotated(self) -> 'Rectangle':
        """Returns a rotated version of this rectangle"""
        return Rectangle(self.height, self.width, self.id)


@dataclass
class PlacedRectangle:
    """Represents a rectangle that has been placed on a sheet"""
    x: float
    y: float
    width: float
    height: float
    id: int

    def overlaps(self, other: 'PlacedRectangle') -> bool:
        """Check if this rectangle overlaps with another"""
        return not (self.x + self.width <= other.x or
                    other.x + other.width <= self.x or
                    self.y + self.height <= other.y or
                    other.y + other.height <= self.y)


class Individual:
    """Represents one solution in the genetic algorithm"""

    def __init__(self, rectangles: List[Rectangle]):
        self.rectangles = rectangles.copy()
        # Each gene is (rectangle_index, is_rotated)
        self.genes = [(i, random.choice([True, False]))
                      for i in range(len(rectangles))]
        random.shuffle(self.genes)  # Random order
        self.fitness = None
        self.sheets_used = None

    def mutate(self, mutation_rate: float = 0.1):
        """Mutate this individual by changing order or rotations"""
        for i in range(len(self.genes)):
            if random.random() < mutation_rate:
                if random.random() < 0.5:
                    # Flip rotation
                    rect_idx, is_rotated = self.genes[i]
                    self.genes[i] = (rect_idx, not is_rotated)
                else:
                    # Swap with another position
                    j = random.randint(0, len(self.genes) - 1)
                    self.genes[i], self.genes[j] = self.genes[j], self.genes[i]
        self.fitness = None  # Invalidate fitness cache


class BinPackingGA:
    """Genetic Algorithm for 2D bin packing using Bottom-Left Fill"""

    def __init__(self, sheet_width: float, sheet_height: float,
                 population_size: int = 50, mutation_rate: float = 0.1):
        self.sheet_width = sheet_width
        self.sheet_height = sheet_height
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.population = []

    def bottom_left_fill(self, rectangles: List[Rectangle],
                         order_and_rotations: List[Tuple[int, bool]]) -> int:
        """
        Place rectangles using Bottom-Left Fill algorithm
        Returns number of sheets used
        """
        sheets = []  # List of lists of PlacedRectangles

        for rect_idx, is_rotated in order_and_rotations:
            rect = rectangles[rect_idx]
            if is_rotated:
                rect = rect.rotated()

            placed = False

            # Try to place on existing sheets
            for sheet_idx, sheet in enumerate(sheets):
                position = self._find_bottom_left_position(rect, sheet)
                if position:
                    x, y = position
                    placed_rect = PlacedRectangle(x, y, rect.width, rect.height, rect.id)
                    sheet.append(placed_rect)
                    placed = True
                    break

            # If couldn't place on any existing sheet, create new one
            if not placed:
                new_sheet = [PlacedRectangle(0, 0, rect.width, rect.height, rect.id)]
                sheets.append(new_sheet)

        return len(sheets)

    def get_detailed_solution(self, rectangles: List[Rectangle],
                              order_and_rotations: List[Tuple[int, bool]]) -> List[List[PlacedRectangle]]:
        """
        Place rectangles and return detailed sheet layout information
        Returns list of sheets, each containing list of PlacedRectangles
        """
        sheets = []  # List of lists of PlacedRectangles

        for rect_idx, is_rotated in order_and_rotations:
            rect = rectangles[rect_idx]
            if is_rotated:
                rect = rect.rotated()

            placed = False

            # Try to place on existing sheets
            for sheet_idx, sheet in enumerate(sheets):
                position = self._find_bottom_left_position(rect, sheet)
                if position:
                    x, y = position
                    placed_rect = PlacedRectangle(x, y, rect.width, rect.height, rect.id)
                    sheet.append(placed_rect)
                    placed = True
                    break

            # If couldn't place on any existing sheet, create new one
            if not placed:
                new_sheet = [PlacedRectangle(0, 0, rect.width, rect.height, rect.id)]
                sheets.append(new_sheet)

        return sheets

    def _find_bottom_left_position(self, rect: Rectangle,
                                   sheet: List[PlacedRectangle]) -> Optional[Tuple[float, float]]:
        """
        Find the bottom-left position where a rectangle can be placed
        Returns None if rectangle doesn't fit anywhere
        """
        if not sheet:
            # Empty sheet
            if rect.width <= self.sheet_width and rect.height <= self.sheet_height:
                return (0, 0)
            return None

        # Generate candidate positions
        candidates = [(0, 0)]  # Always try bottom-left corner

        # Add positions at corners of existing rectangles
        for placed in sheet:
            candidates.extend([
                (placed.x + placed.width, placed.y),  # Right edge
                (placed.x, placed.y + placed.height),  # Top edge
                (placed.x + placed.width, placed.y + placed.height)  # Top-right corner
            ])

        # Remove duplicates and sort by bottom-left preference
        candidates = list(set(candidates))
        candidates.sort(key=lambda pos: (pos[1], pos[0]))  # Sort by y, then x

        # Test each candidate position
        for x, y in candidates:
            if self._can_place_at(rect, x, y, sheet):
                return (x, y)

        return None

    def _can_place_at(self, rect: Rectangle, x: float, y: float,
                      sheet: List[PlacedRectangle]) -> bool:
        """Check if rectangle can be placed at given position"""
        # Check sheet boundaries
        if x + rect.width > self.sheet_width or y + rect.height > self.sheet_height:
            return False

        # Check overlaps with existing rectangles
        test_rect = PlacedRectangle(x, y, rect.width, rect.height, -1)
        for placed in sheet:
            if test_rect.overlaps(placed):
                return False

        return True

    def evaluate_fitness(self, individual: Individual, rectangles: List[Rectangle]) -> float:
        """Evaluate fitness of an individual (lower is better - fewer sheets)"""
        if individual.fitness is not None:
            return individual.fitness

        sheets_used = self.bottom_left_fill(rectangles, individual.genes)
        individual.sheets_used = sheets_used
        individual.fitness = sheets_used
        return sheets_used

    def create_initial_population(self, rectangles: List[Rectangle]) -> List[Individual]:
        """Create initial population with various strategies"""
        population = []

        # Strategy 1: Random individuals
        for _ in range(self.population_size // 3):
            population.append(Individual(rectangles))

        # Strategy 2: Sort by area (largest first)
        sorted_rects = sorted(rectangles, key=lambda r: r.area(), reverse=True)
        for _ in range(self.population_size // 3):
            individual = Individual(rectangles)
            # Create genes based on sorted order but with random rotations
            individual.genes = [(sorted_rects.index(rect), random.choice([True, False]))
                                for rect in rectangles]
            population.append(individual)

        # Strategy 3: Sort by height (tallest first)
        sorted_by_height = sorted(rectangles, key=lambda r: max(r.width, r.height), reverse=True)
        for _ in range(self.population_size - len(population)):
            individual = Individual(rectangles)
            individual.genes = [(sorted_by_height.index(rect), random.choice([True, False]))
                                for rect in rectangles]
            population.append(individual)

        return population

    def tournament_selection(self, population: List[Individual],
                             rectangles: List[Rectangle], tournament_size: int = 3) -> Individual:
        """Select individual using tournament selection"""
        tournament = random.sample(population, tournament_size)
        best = min(tournament, key=lambda ind: self.evaluate_fitness(ind, rectangles))
        return best

    def crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        """Create two offspring using order crossover (OX)"""
        length = len(parent1.genes)

        # Choose crossover points
        start = random.randint(0, length - 1)
        end = random.randint(start, length - 1)

        # Create offspring
        child1 = Individual(parent1.rectangles)
        child2 = Individual(parent2.rectangles)

        # Copy segment from parents
        child1.genes = [None] * length
        child2.genes = [None] * length

        # Copy the selected segment
        child1.genes[start:end + 1] = parent1.genes[start:end + 1]
        child2.genes[start:end + 1] = parent2.genes[start:end + 1]

        # Fill remaining positions
        self._fill_remaining_positions(child1, parent2, start, end)
        self._fill_remaining_positions(child2, parent1, start, end)

        return child1, child2

    def _fill_remaining_positions(self, child: Individual, other_parent: Individual,
                                  start: int, end: int):
        """Helper method for crossover - fill remaining positions"""
        length = len(child.genes)
        used_rects = {gene[0] for gene in child.genes[start:end + 1] if gene is not None}

        fill_idx = 0
        for i in range(length):
            if child.genes[i] is None:
                # Find next unused rectangle from other parent
                while fill_idx < length:
                    rect_idx, rotation = other_parent.genes[fill_idx]
                    fill_idx += 1
                    if rect_idx not in used_rects:
                        child.genes[i] = (rect_idx, rotation)
                        used_rects.add(rect_idx)
                        break

    def evolve(self, rectangles: List[Rectangle], generations: int = 100) -> Individual:
        """Main evolution loop"""
        print(f"Starting evolution with {len(rectangles)} rectangles...")

        # Create initial population
        self.population = self.create_initial_population(rectangles)

        # Evaluate initial population
        for individual in self.population:
            self.evaluate_fitness(individual, rectangles)

        best_individual = min(self.population, key=lambda ind: ind.fitness)
        print(f"Initial best: {best_individual.fitness} sheets")

        for generation in range(generations):
            new_population = []

            # Elitism - keep best 10% of population
            elite_size = max(1, self.population_size // 10)
            elite = sorted(self.population, key=lambda ind: ind.fitness)[:elite_size]
            new_population.extend(elite)

            # Generate rest of population through crossover and mutation
            while len(new_population) < self.population_size:
                parent1 = self.tournament_selection(self.population, rectangles)
                parent2 = self.tournament_selection(self.population, rectangles)

                child1, child2 = self.crossover(parent1, parent2)

                child1.mutate(self.mutation_rate)
                child2.mutate(self.mutation_rate)

                new_population.extend([child1, child2])

            # Trim to exact population size
            new_population = new_population[:self.population_size]
            self.population = new_population

            # Evaluate new population
            for individual in self.population:
                if individual.fitness is None:
                    self.evaluate_fitness(individual, rectangles)

            # Track best solution
            current_best = min(self.population, key=lambda ind: ind.fitness)
            if current_best.fitness < best_individual.fitness:
                best_individual = current_best
                print(f"Generation {generation}: New best solution with {best_individual.fitness} sheets")

        return best_individual


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


# Example usage
if __name__ == "__main__":
    # Create some example rectangles
    rectangles = [
        Rectangle(1000, 500, 1),
        Rectangle(1000, 500, 2),
        Rectangle(1000, 700, 3),
        Rectangle(1000, 700, 4),
        Rectangle(700, 500, 5),
        Rectangle(700, 500, 6),
        Rectangle(1000, 500, 7),
        Rectangle(1000, 500, 8),
        Rectangle(1000, 700, 9),
        Rectangle(1000, 700, 10),
        Rectangle(700, 500, 11),
        Rectangle(700, 500, 12),
    ]

    # Create and run GA
    ga = BinPackingGA(sheet_width=1220, sheet_height=2440, population_size=30)
    best_solution = ga.evolve(rectangles, generations=50)

    print(f"\nBest solution uses {best_solution.fitness} sheets")

    # Get detailed layout
    sheets = ga.get_detailed_solution(rectangles, best_solution.genes)

    print("\nDetailed Solution:")
    print("=" * 50)

    for sheet_num, sheet in enumerate(sheets, 1):
        print(f"\nSheet {sheet_num}:")
        print("-" * 30)

        total_area_used = 0
        for rect in sheet:
            original_rect = next(r for r in rectangles if r.id == rect.id)
            was_rotated = (rect.width != original_rect.width)
            rotation_info = " (rotated)" if was_rotated else ""

            print(f"  Rectangle {rect.id}: position ({rect.x}, {rect.y}), "
                  f"size {rect.width}x{rect.height}{rotation_info}")
            total_area_used += rect.width * rect.height

        sheet_area = ga.sheet_width * ga.sheet_height
        efficiency = (total_area_used / sheet_area) * 100
        print(f"  Sheet efficiency: {efficiency:.1f}% ({total_area_used}/{sheet_area})")

    # Calculate overall efficiency
    total_rect_area = sum(r.area() for r in rectangles)
    total_sheet_area = len(sheets) * ga.sheet_width * ga.sheet_height
    overall_efficiency = (total_rect_area / total_sheet_area) * 100
    print(f"\nOverall material efficiency: {overall_efficiency:.1f}%")
    print(f"Total rectangle area: {total_rect_area}")
    print(f"Total sheet area used: {total_sheet_area}")
    print(f"Waste: {total_sheet_area - total_rect_area}")

    print("\nRectangle placement order:")
    for i, (rect_idx, is_rotated) in enumerate(best_solution.genes):
        rect = rectangles[rect_idx]
        rotation_str = "rotated" if is_rotated else "normal"
        print(f"{i + 1}. Rectangle {rect.id} ({rect.width}x{rect.height}) - {rotation_str}")

    # Create visualizations
    print("\n" + "=" * 50)
    print("CREATING VISUALIZATIONS")
    print("=" * 50)

    # Create visualizer
    visualizer = SheetVisualizer(ga.sheet_width, ga.sheet_height)

    # Show overview of all sheets
    print("\nShowing overview of all sheets...")
    visualizer.visualize_all_sheets(sheets, rectangles)

    # Show detailed view of each sheet
    print("\nShowing detailed view of each sheet...")
    for sheet_idx, sheet in enumerate(sheets):
        visualizer.visualize_sheet(sheet, sheet_idx + 1, rectangles)

    # Create technical cutting diagram
    print("\nCreating technical cutting diagram...")
    visualizer.create_cutting_diagram(sheets, rectangles)

    print("\nVisualization complete!")

    # Create and run GA
    ga = BinPackingGA(sheet_width=200, sheet_height=150, population_size=30)
    best_solution = ga.evolve(rectangles, generations=50)

    print(f"\nBest solution uses {best_solution.fitness} sheets")

    # Get detailed layout
    sheets = ga.get_detailed_solution(rectangles, best_solution.genes)

    print("\nDetailed Solution:")
    print("=" * 50)

    for sheet_num, sheet in enumerate(sheets, 1):
        print(f"\nSheet {sheet_num}:")
    print("-" * 30)

    total_area_used = 0
    for rect in sheet:
        original_rect = next(r for r in rectangles if r.id == rect.id)
    was_rotated = (rect.width != original_rect.width)
    rotation_info = " (rotated)" if was_rotated else ""

    print(f"  Rectangle {rect.id}: position ({rect.x}, {rect.y}), "
          f"size {rect.width}x{rect.height}{rotation_info}")
    total_area_used += rect.width * rect.height

    sheet_area = ga.sheet_width * ga.sheet_height
    efficiency = (total_area_used / sheet_area) * 100
    print(f"  Sheet efficiency: {efficiency:.1f}% ({total_area_used}/{sheet_area})")

    # Calculate overall efficiency
    total_rect_area = sum(r.area() for r in rectangles)
    total_sheet_area = len(sheets) * ga.sheet_width * ga.sheet_height
    overall_efficiency = (total_rect_area / total_sheet_area) * 100
    print(f"\nOverall material efficiency: {overall_efficiency:.1f}%")
    print(f"Total rectangle area: {total_rect_area}")
    print(f"Total sheet area used: {total_sheet_area}")
    print(f"Waste: {total_sheet_area - total_rect_area}")

    print("\nRectangle placement order:")
    for i, (rect_idx, is_rotated) in enumerate(best_solution.genes):
        rect = rectangles[rect_idx]
    rotation_str = "rotated" if is_rotated else "normal"
    print(f"{i + 1}. Rectangle {rect.id} ({rect.width}x{rect.height}) - {rotation_str}")