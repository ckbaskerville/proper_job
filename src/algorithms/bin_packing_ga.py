"""Integration module for bin packing with genetic algorithm.

This module provides a compatible interface with the existing system
while using the refactored algorithm components.
"""

import logging
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass

from src.models.geometry import Rectangle, PlacedRectangle
from .optimization import SheetOptimizer, OptimizerConfig, PackingIndividual
from .packing import BinPacker, BottomLeftFillPacker

logger = logging.getLogger(__name__)


class BinPackingGA:
    """Genetic Algorithm for 2D bin packing using Bottom-Left Fill.

    This class provides a compatible interface with the existing system
    while using the refactored optimization components internally.
    """

    def __init__(
            self,
            sheet_width: float,
            sheet_height: float,
            population_size: int = 50,
            mutation_rate: float = 0.1,
            cutting_margin: float = 3.0
    ):
        """Initialize the bin packing genetic algorithm.

        Args:
            sheet_width: Width of sheets in mm
            sheet_height: Height of sheets in mm
            population_size: Size of population for GA
            mutation_rate: Mutation probability
            cutting_margin: Margin between rectangles in mm
        """
        self.sheet_width = sheet_width
        self.sheet_height = sheet_height
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.cutting_margin = cutting_margin

        # Create packer for direct use
        self.packer = BinPacker(
            bin_width=sheet_width,
            bin_height=sheet_height,
            strategy=BottomLeftFillPacker(allow_rotation=True, cutting_margin=cutting_margin),
            cutting_margin=cutting_margin
        )

        # Storage for last optimization
        self.last_optimizer: Optional[SheetOptimizer] = None
        self.last_solution: Optional[PackingIndividual] = None
        self.last_bins: Optional[List[List[PlacedRectangle]]] = None

    def bottom_left_fill(
            self,
            rectangles: List[Rectangle],
            order_and_rotations: List[Tuple[int, bool]]
    ) -> int:
        """Place rectangles using Bottom-Left Fill algorithm.

        This method provides compatibility with the existing interface.

        Args:
            rectangles: List of rectangles to pack
            order_and_rotations: List of (rectangle_index, is_rotated) tuples

        Returns:
            Number of sheets used
        """
        # Create ordered rectangle list
        ordered_rects = []
        for rect_idx, is_rotated in order_and_rotations:
            rect = rectangles[rect_idx]
            if is_rotated:
                rect = rect.rotated()
            ordered_rects.append(rect)

        # Pack rectangles
        bins = self.packer.pack(ordered_rects)
        return len(bins)

    def get_detailed_solution(
            self,
            rectangles: List[Rectangle],
            order_and_rotations: List[Tuple[int, bool]]
    ) -> List[List[PlacedRectangle]]:
        """Get detailed sheet layout information.

        Args:
            rectangles: List of rectangles to pack
            order_and_rotations: List of (rectangle_index, is_rotated) tuples

        Returns:
            List of sheets, each containing list of PlacedRectangles
        """
        # Create ordered rectangle list with proper IDs
        ordered_rects = []
        for rect_idx, is_rotated in order_and_rotations:
            rect = rectangles[rect_idx]
            if is_rotated:
                # Create rotated rectangle preserving ID
                rect = Rectangle(
                    width=rect.height,
                    height=rect.width,
                    id=rect.id
                )
            ordered_rects.append(rect)

        # Pack rectangles
        bins = self.packer.pack(ordered_rects)

        # Store for later use
        self.last_bins = bins

        return bins

    def _find_bottom_left_position(
            self,
            rect: Rectangle,
            sheet: List[PlacedRectangle]
    ) -> Optional[Tuple[float, float]]:
        """Find the bottom-left position where a rectangle can be placed.

        This method provides compatibility with the existing interface.

        Args:
            rect: Rectangle to place
            sheet: Current sheet contents

        Returns:
            (x, y) position or None if rectangle doesn't fit
        """
        # Use the packer's strategy directly
        strategy = self.packer.strategy
        if isinstance(strategy, BottomLeftFillPacker):
            return strategy._find_bottom_left_position(
                rect.width,
                rect.height,
                sheet,
                self.sheet_width,
                self.sheet_height
            )
        return None

    def _can_place_at(
            self,
            rect: Rectangle,
            x: float,
            y: float,
            sheet: List[PlacedRectangle]
    ) -> bool:
        """Check if rectangle can be placed at given position.

        Args:
            rect: Rectangle to place
            x: X position
            y: Y position
            sheet: Current sheet contents

        Returns:
            True if rectangle can be placed
        """
        # Use the packer's strategy directly
        strategy = self.packer.strategy
        if isinstance(strategy, BottomLeftFillPacker):
            return strategy._can_place_at(
                x, y,
                rect.width,
                rect.height,
                sheet,
                self.sheet_width,
                self.sheet_height
            )
        return False

    def evaluate_fitness(
            self,
            individual: 'Individual',
            rectangles: List[Rectangle]
    ) -> float:
        """Evaluate fitness of an individual.

        This method provides compatibility with the existing interface.

        Args:
            individual: Individual with genes attribute
            rectangles: List of rectangles

        Returns:
            Fitness value (number of sheets used)
        """
        sheets_used = self.bottom_left_fill(rectangles, individual.genes)
        individual.sheets_used = sheets_used
        individual.fitness = sheets_used
        return sheets_used

    def create_initial_population(
            self,
            rectangles: List[Rectangle]
    ) -> List['Individual']:
        """Create initial population with various strategies.

        Args:
            rectangles: List of rectangles to pack

        Returns:
            List of individuals
        """
        # Create optimizer config
        config = OptimizerConfig(
            sheet_width=self.sheet_width,
            sheet_height=self.sheet_height,
            population_size=self.population_size,
            mutation_rate=self.mutation_rate,
            cutting_margin=self.cutting_margin
        )

        # Create temporary optimizer
        optimizer = SheetOptimizer(rectangles, config)
        optimizer.create_initial_population()

        # Convert to old-style individuals
        population = []
        for modern_ind in optimizer.population:
            # Create compatible individual
            old_ind = Individual(rectangles)
            old_ind.genes = [
                (gene.rectangle_index, gene.is_rotated)
                for gene in modern_ind.genes
            ]
            old_ind.fitness = modern_ind.fitness
            population.append(old_ind)

        return population

    def tournament_selection(
            self,
            population: List['Individual'],
            rectangles: List[Rectangle],
            tournament_size: int = 3
    ) -> 'Individual':
        """Select individual using tournament selection.

        Args:
            population: Current population
            rectangles: List of rectangles
            tournament_size: Size of tournament

        Returns:
            Selected individual
        """
        import random
        tournament = random.sample(population, tournament_size)
        best = min(
            tournament,
            key=lambda ind: self.evaluate_fitness(ind, rectangles)
        )
        return best

    def crossover(
            self,
            parent1: 'Individual',
            parent2: 'Individual'
    ) -> Tuple['Individual', 'Individual']:
        """Create two offspring using order crossover.

        Args:
            parent1: First parent
            parent2: Second parent

        Returns:
            Two offspring
        """
        import random

        length = len(parent1.genes)

        # Choose crossover points
        start = random.randint(0, length - 1)
        end = random.randint(start, length - 1)

        # Create offspring
        child1 = Individual(parent1.rectangles)
        child2 = Individual(parent2.rectangles)

        # Initialize genes
        child1.genes = [None] * length
        child2.genes = [None] * length

        # Copy segment from parents
        child1.genes[start:end + 1] = parent1.genes[start:end + 1]
        child2.genes[start:end + 1] = parent2.genes[start:end + 1]

        # Fill remaining positions
        self._fill_remaining_positions(child1, parent2, start, end)
        self._fill_remaining_positions(child2, parent1, start, end)

        return child1, child2

    def _fill_remaining_positions(
            self,
            child: 'Individual',
            other_parent: 'Individual',
            start: int,
            end: int
    ) -> None:
        """Fill remaining positions in crossover.

        Args:
            child: Child to fill
            other_parent: Other parent
            start: Crossover start
            end: Crossover end
        """
        length = len(child.genes)
        used_rects = {
            gene[0] for gene in child.genes[start:end + 1]
            if gene is not None
        }

        # Get unused genes from other parent in order
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

    def evolve(
            self,
            rectangles: List[Rectangle],
            generations: int = 100
    ) -> 'Individual':
        """Main evolution loop.

        Args:
            rectangles: List of rectangles to pack
            generations: Number of generations to evolve

        Returns:
            Best individual found
        """
        logger.info(
            f"Starting evolution with {len(rectangles)} rectangles..."
        )

        # Create optimizer
        config = OptimizerConfig(
            sheet_width=self.sheet_width,
            sheet_height=self.sheet_height,
            population_size=self.population_size,
            mutation_rate=self.mutation_rate,
            generations=generations,
            cutting_margin=self.cutting_margin
        )

        self.last_optimizer = SheetOptimizer(rectangles, config)

        # Run optimization
        best_modern, bins = self.last_optimizer.optimize(generations)

        # Store results
        self.last_solution = best_modern
        self.last_bins = bins

        # Convert to old-style individual
        best_individual = Individual(rectangles)
        best_individual.genes = [
            (gene.rectangle_index, gene.is_rotated)
            for gene in best_modern.genes
        ]
        best_individual.fitness = len(bins)
        best_individual.sheets_used = len(bins)

        logger.info(f"Best solution uses {len(bins)} sheets")

        return best_individual


# Compatibility class to match existing interface
class Individual:
    """Compatibility class for existing Individual interface."""

    def __init__(self, rectangles: List[Rectangle]):
        """Initialize individual.

        Args:
            rectangles: List of rectangles
        """
        import random

        self.rectangles = rectangles.copy()
        # Each gene is (rectangle_index, is_rotated)
        self.genes = [
            (i, random.choice([True, False]))
            for i in range(len(rectangles))
        ]
        random.shuffle(self.genes)
        self.fitness = None
        self.sheets_used = None

    def mutate(self, mutation_rate: float = 0.1):
        """Mutate this individual.

        Args:
            mutation_rate: Probability of mutation
        """
        import random

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