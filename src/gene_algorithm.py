import random
from typing import List, Tuple, Optional
from proper_job_dataclasses import Rectangle, PlacedRectangle


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

        # Create list of unused rectangles from other parent in order
        unused_genes = []
        for rect_idx, rotation in other_parent.genes:
            if rect_idx not in used_rects:
                unused_genes.append((rect_idx, rotation))

        # Fill remaining None positions
        unused_idx = 0
        for i in range(length):
            if child.genes[i] is None:
                if unused_idx < len(unused_genes):
                    child.genes[i] = unused_genes[unused_idx]
                    unused_idx += 1
                else:
                    # Fallback: this should never happen if crossover is correct
                    # but just in case, fill with a random unused rectangle
                    all_rect_indices = set(range(len(child.rectangles)))
                    truly_used = {gene[0] for gene in child.genes if gene is not None}
                    remaining = list(all_rect_indices - truly_used)
                    if remaining:
                        child.genes[i] = (remaining[0], False)

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