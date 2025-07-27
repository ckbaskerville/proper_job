"""Main optimization module combining genetic algorithm with bin packing."""

import logging
import random
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass

from src.models.geometry import Rectangle, PlacedRectangle
from .genetic_algorithm import GeneticAlgorithm, Individual
from .packing import BinPacker, BottomLeftFillPacker

logger = logging.getLogger(__name__)


@dataclass
class PackingGene:
    """Gene representation for packing problem.

    Attributes:
        rectangle_index: Index of rectangle in original list
        is_rotated: Whether rectangle is rotated
    """
    rectangle_index: int
    is_rotated: bool


class PackingIndividual(Individual[PackingGene]):
    """Individual for the packing problem."""

    def __init__(self, rectangles: List[Rectangle]):
        """Initialize with random genes.

        Args:
            rectangles: List of rectangles to pack
        """
        # Create random order with random rotations
        genes = [
            PackingGene(i, random.choice([True, False]))
            for i in range(len(rectangles))
        ]
        random.shuffle(genes)
        super().__init__(genes)

        # Store reference to rectangles
        self.rectangles = rectangles
        self.bins_used: Optional[int] = None

    def mutate(self, mutation_rate: float) -> None:
        """Mutate this individual.

        Args:
            mutation_rate: Probability of mutation
        """
        for i in range(len(self.genes)):
            if random.random() < mutation_rate:
                if random.random() < 0.5:
                    # Flip rotation
                    self.genes[i].is_rotated = not self.genes[i].is_rotated
                else:
                    # Swap with another position
                    j = random.randint(0, len(self.genes) - 1)
                    self.genes[i], self.genes[j] = self.genes[j], self.genes[i]

        # Invalidate fitness cache
        self.fitness = None
        self.bins_used = None


@dataclass
class OptimizerConfig:
    """Configuration for the sheet optimizer."""
    sheet_width: float
    sheet_height: float
    population_size: int = 50
    generations: int = 100
    mutation_rate: float = 0.1
    tournament_size: int = 3
    elite_percentage: float = 0.1
    allow_rotation: bool = True


class SheetOptimizer(GeneticAlgorithm[PackingGene]):
    """Genetic algorithm for optimizing sheet usage in 2D bin packing."""

    def __init__(
            self,
            rectangles: List[Rectangle],
            config: OptimizerConfig
    ):
        """Initialize the optimizer.

        Args:
            rectangles: List of rectangles to pack
            config: Optimizer configuration
        """
        super().__init__(
            population_size=config.population_size,
            mutation_rate=config.mutation_rate,
            tournament_size=config.tournament_size,
            elite_percentage=config.elite_percentage
        )

        self.rectangles = rectangles
        self.config = config

        # Create bin packer
        self.packer = BinPacker(
            bin_width=config.sheet_width,
            bin_height=config.sheet_height,
            strategy=BottomLeftFillPacker(allow_rotation=config.allow_rotation)
        )

        # Cache for packing results
        self._packing_cache: Dict[str, Tuple[int, List[List[PlacedRectangle]]]] = {}

    def create_individual(self) -> PackingIndividual:
        """Create a new random individual.

        Returns:
            New PackingIndividual
        """
        return PackingIndividual(self.rectangles)

    def evaluate_fitness(self, individual: PackingIndividual) -> float:
        """Evaluate fitness by packing rectangles.

        Args:
            individual: Individual to evaluate

        Returns:
            Number of bins used (lower is better)
        """
        # Get rectangles in order specified by genes
        ordered_rects = []
        for gene in individual.genes:
            rect = self.rectangles[gene.rectangle_index]
            if gene.is_rotated and self.config.allow_rotation:
                rect = rect.rotated()
            ordered_rects.append(rect)

        # Pack rectangles
        bins = self.packer.pack(ordered_rects)

        # Store number of bins for later use
        individual.bins_used = len(bins)

        # Fitness is number of bins (minimize)
        # Add small penalty for wasted space to break ties
        fitness = len(bins)
        if bins:
            avg_efficiency = sum(
                self.packer.get_bin_efficiency(bin_items)
                for bin_items in bins
            ) / len(bins)
            fitness += (1 - avg_efficiency) * 0.1

        return fitness

    def crossover(
            self,
            parent1: PackingIndividual,
            parent2: PackingIndividual
    ) -> Tuple[PackingIndividual, PackingIndividual]:
        """Create offspring using order crossover (OX).

        Args:
            parent1: First parent
            parent2: Second parent

        Returns:
            Two offspring
        """
        length = len(parent1.genes)

        # Choose crossover points
        start = random.randint(0, length - 1)
        end = random.randint(start, length - 1)

        # Create offspring
        child1 = PackingIndividual(self.rectangles)
        child2 = PackingIndividual(self.rectangles)

        # Initialize genes
        child1.genes = [None] * length
        child2.genes = [None] * length

        # Copy segment from parents
        child1.genes[start:end + 1] = parent1.genes[start:end + 1]
        child2.genes[start:end + 1] = parent2.genes[start:end + 1]

        # Fill remaining positions
        self._fill_remaining_ox(child1, parent2.genes, start, end)
        self._fill_remaining_ox(child2, parent1.genes, start, end)

        return child1, child2

    def _fill_remaining_ox(
            self,
            child: PackingIndividual,
            other_parent_genes: List[PackingGene],
            start: int,
            end: int
    ) -> None:
        """Fill remaining positions in order crossover.

        Args:
            child: Child to fill
            other_parent_genes: Genes from other parent
            start: Crossover start point
            end: Crossover end point
        """
        used_indices = {
            gene.rectangle_index
            for gene in child.genes[start:end + 1]
            if gene is not None
        }

        # Get unused genes from other parent in order
        unused_genes = [
            gene for gene in other_parent_genes
            if gene.rectangle_index not in used_indices
        ]

        # Fill remaining positions
        unused_idx = 0
        for i in range(len(child.genes)):
            if child.genes[i] is None:
                child.genes[i] = unused_genes[unused_idx]
                unused_idx += 1

    def mutate_individual(self, individual: PackingIndividual) -> None:
        """Mutate an individual.

        Args:
            individual: Individual to mutate
        """
        individual.mutate(self.mutation_rate)

    def optimize(
            self,
            generations: Optional[int] = None,
            target_bins: Optional[int] = None
    ) -> Tuple[PackingIndividual, List[List[PlacedRectangle]]]:
        """Run optimization and return best solution.

        Args:
            generations: Number of generations (uses config if None)
            target_bins: Stop if this many bins achieved

        Returns:
            Tuple of (best individual, bin packing layout)
        """
        generations = generations or self.config.generations

        logger.info(
            f"Starting optimization for {len(self.rectangles)} rectangles "
            f"on {self.config.sheet_width}x{self.config.sheet_height} sheets"
        )

        # Run genetic algorithm
        best = self.evolve(
            generations=generations,
            target_fitness=target_bins
        )

        # Get final packing
        ordered_rects = []
        for gene in best.genes:
            rect = self.rectangles[gene.rectangle_index]
            if gene.is_rotated and self.config.allow_rotation:
                rect = rect.rotated()
            ordered_rects.append(rect)

        bins = self.packer.pack(ordered_rects)

        logger.info(
            f"Optimization complete. Best solution uses {len(bins)} sheets "
            f"with {self.packer.calculate_efficiency(bins):.1%} efficiency"
        )

        return best, bins

    def create_heuristic_individual(self, strategy: str) -> PackingIndividual:
        """Create an individual using a heuristic strategy.

        Args:
            strategy: Strategy name ('area', 'height', 'width', 'perimeter')

        Returns:
            Individual with heuristic ordering
        """
        individual = PackingIndividual(self.rectangles)

        # Sort indices by strategy
        indices = list(range(len(self.rectangles)))

        if strategy == 'area':
            indices.sort(
                key=lambda i: self.rectangles[i].area(),
                reverse=True
            )
        elif strategy == 'height':
            indices.sort(
                key=lambda i: max(
                    self.rectangles[i].width,
                    self.rectangles[i].height
                ),
                reverse=True
            )
        elif strategy == 'width':
            indices.sort(
                key=lambda i: self.rectangles[i].width,
                reverse=True
            )
        elif strategy == 'perimeter':
            indices.sort(
                key=lambda i: (
                        self.rectangles[i].width +
                        self.rectangles[i].height
                ),
                reverse=True
            )

        # Set genes with optimal rotation
        individual.genes = []
        for i in indices:
            rect = self.rectangles[i]
            # Choose rotation that fits better
            if self.config.allow_rotation:
                is_rotated = rect.height > rect.width
            else:
                is_rotated = False

            individual.genes.append(PackingGene(i, is_rotated))

        return individual

    def create_initial_population(self) -> None:
        """Create initial population with heuristic individuals."""
        logger.info(f"Creating initial population of {self.population_size}")

        self.population = []

        # Add heuristic individuals
        strategies = ['area', 'height', 'width', 'perimeter']
        for strategy in strategies:
            if len(self.population) < self.population_size:
                individual = self.create_heuristic_individual(strategy)
                individual.fitness = self.evaluate_fitness(individual)
                self.population.append(individual)

        # Fill rest with random individuals
        while len(self.population) < self.population_size:
            individual = self.create_individual()
            individual.fitness = self.evaluate_fitness(individual)
            self.population.append(individual)

        # Sort by fitness
        self.population.sort(key=lambda ind: ind.fitness)

        best_fitness = self.population[0].fitness
        logger.info(
            f"Initial population created. Best fitness: {best_fitness} bins"
        )