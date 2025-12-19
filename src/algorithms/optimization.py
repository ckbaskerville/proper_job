"""Main optimization module combining genetic algorithm with bin packing and grain direction."""

import logging
import random
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass

from src.models.geometry import Rectangle, PlacedRectangle, GrainDirection
from .genetic_algorithm import GeneticAlgorithm, Individual
from .packing import BinPacker, BottomLeftFillPacker

logger = logging.getLogger(__name__)


@dataclass
class PackingGene:
    """Gene representation for packing problem with grain awareness.

    Attributes:
        rectangle_index: Index of rectangle in original list
        is_rotated: Whether rectangle is rotated (may be ignored for grain materials)
    """
    rectangle_index: int
    is_rotated: bool


class PackingIndividual(Individual[PackingGene]):
    """Individual for the packing problem with grain direction support."""

    def __init__(self, rectangles: List[Rectangle], allow_rotation: bool = True):
        """Initialize with random genes.

        Args:
            rectangles: List of rectangles to pack
            allow_rotation: Whether rotation is allowed for this material
        """
        self.allow_rotation = allow_rotation

        # Create random order with random rotations (if allowed)
        genes = []
        for i in range(len(rectangles)):
            rect = rectangles[i]

            # Only allow rotation if:
            # 1. Rotation is globally allowed for this material
            # 2. This specific rectangle allows rotation (grain constraints)
            can_rotate = (
                allow_rotation and
                rect.is_rotation_allowed() and
                rect.width != rect.height  # Don't bother with squares
            )

            is_rotated = random.choice([True, False]) if can_rotate else False
            genes.append(PackingGene(i, is_rotated))

        random.shuffle(genes)
        super().__init__(genes)

        # Store reference to rectangles
        self.rectangles = rectangles
        self.bins_used: Optional[int] = None

    def mutate(self, mutation_rate: float) -> None:
        """Mutate this individual respecting grain constraints.

        Args:
            mutation_rate: Probability of mutation
        """
        for i in range(len(self.genes)):
            if random.random() < mutation_rate:
                gene = self.genes[i]
                rect = self.rectangles[gene.rectangle_index]

                if random.random() < 0.5:
                    # Try to flip rotation (only if allowed)
                    can_rotate = (
                        self.allow_rotation and
                        rect.is_rotation_allowed() and
                        rect.width != rect.height
                    )
                    if can_rotate:
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
    material_type: str = "MDF"
    population_size: int = 50
    generations: int = 100
    mutation_rate: float = 0.1
    tournament_size: int = 3
    elite_percentage: float = 0.1
    allow_rotation: bool = True  # Will be overridden based on material type
    cutting_margin: float = 3.0  # Margin between rectangles in mm


class SheetOptimizer(GeneticAlgorithm[PackingGene]):
    """Genetic algorithm for optimizing sheet usage in 2D bin packing with grain direction."""

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

        # Determine if this material has grain constraints
        self.material_has_grain = self._material_has_grain(config.material_type)

        # Override rotation setting based on material
        if self.material_has_grain:
            self.config.allow_rotation = False
            logger.info(f"Material {config.material_type} has grain - rotation disabled")
        else:
            logger.info(f"Material {config.material_type} has no grain - rotation enabled")

        # Create bin packer with appropriate settings
        self.packer = BinPacker(
            bin_width=config.sheet_width,
            bin_height=config.sheet_height,
            material_type=config.material_type,
            cutting_margin=config.cutting_margin
        )

        # Cache for packing results
        self._packing_cache: Dict[str, Tuple[int, List[List[PlacedRectangle]]]] = {}

    def _material_has_grain(self, material_type: str) -> bool:
        """Check if a material has grain direction constraints.

        Args:
            material_type: Type of material

        Returns:
            True if material has grain constraints
        """
        grain_materials = {"veneer", "hardwood", "laminate", "plywood"}
        return any(grain_mat in material_type.lower() for grain_mat in grain_materials)

    def create_individual(self) -> PackingIndividual:
        """Create a new random individual.

        Returns:
            New PackingIndividual
        """
        return PackingIndividual(self.rectangles, self.config.allow_rotation)

    def evaluate_fitness(self, individual: PackingIndividual) -> float:
        """Evaluate fitness by packing rectangles with grain constraints.

        Args:
            individual: Individual to evaluate

        Returns:
            Number of bins used (lower is better)
        """
        # Get rectangles in order specified by genes
        ordered_rects = []
        for gene in individual.genes:
            rect = self.rectangles[gene.rectangle_index]

            # Apply rotation only if allowed and beneficial
            if (gene.is_rotated and
                self.config.allow_rotation and
                rect.is_rotation_allowed()):

                rect = rect.rotated()

            # Ensure correct grain orientation
            rect = rect.get_correct_orientation_for_grain()
            ordered_rects.append(rect)

        # Pack rectangles
        bins = self.packer.pack(ordered_rects)

        # Validate grain compliance if material has grain
        if self.material_has_grain:
            is_compliant, violations = self.packer.validate_grain_compliance(bins)
            if not is_compliant:
                logger.warning(f"Grain violations in individual: {violations}")
                # Penalize individuals that violate grain constraints
                return len(bins) + 10  # Heavy penalty

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
        """Create offspring using order crossover (OX) with grain awareness.

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
        child1 = PackingIndividual(self.rectangles, self.config.allow_rotation)
        child2 = PackingIndividual(self.rectangles, self.config.allow_rotation)

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
                if unused_idx < len(unused_genes):
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
            f"on {self.config.sheet_width}x{self.config.sheet_height} sheets "
            f"(material: {self.config.material_type}, grain constraints: {self.material_has_grain})"
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

            # Apply rotation only if allowed
            if (gene.is_rotated and
                self.config.allow_rotation and
                rect.is_rotation_allowed()):
                rect = rect.rotated()

            # Ensure correct grain orientation
            rect = rect.get_correct_orientation_for_grain()
            ordered_rects.append(rect)

        bins = self.packer.pack(ordered_rects)

        # Final validation for grain compliance
        if self.material_has_grain:
            is_compliant, violations = self.packer.validate_grain_compliance(bins)
            if not is_compliant:
                logger.error(f"Final solution has grain violations: {violations}")
            else:
                logger.info("Final solution respects all grain direction constraints")

        efficiency = self.packer.calculate_efficiency(bins)
        logger.info(
            f"Optimization complete. Best solution uses {len(bins)} sheets "
            f"with {efficiency:.1%} efficiency"
        )

        return best, bins

    def create_heuristic_individual(self, strategy: str) -> PackingIndividual:
        """Create an individual using a heuristic strategy with grain awareness.

        Args:
            strategy: Strategy name ('area', 'height', 'width', 'perimeter')

        Returns:
            Individual with heuristic ordering
        """
        individual = PackingIndividual(self.rectangles, self.config.allow_rotation)

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

        # Set genes with optimal rotation considering grain
        individual.genes = []
        for i in indices:
            rect = self.rectangles[i]

            # Determine best rotation considering grain constraints
            is_rotated = False
            if (self.config.allow_rotation and
                rect.is_rotation_allowed() and
                rect.width != rect.height):

                # For materials without grain, choose rotation that fits better
                if not self.material_has_grain:
                    # Simple heuristic: prefer orientation where larger dimension
                    # aligns with larger sheet dimension
                    if self.config.sheet_width > self.config.sheet_height:
                        is_rotated = rect.height > rect.width
                    else:
                        is_rotated = rect.width > rect.height
                # For grain materials, rotation will be determined by grain constraints

            individual.genes.append(PackingGene(i, is_rotated))

        return individual

    def create_initial_population(self) -> None:
        """Create initial population with heuristic individuals and grain awareness."""
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

    def get_grain_statistics(self) -> Dict[str, int]:
        """Get statistics about grain direction requirements.

        Returns:
            Dictionary with grain direction statistics
        """
        stats = {
            'none': 0,
            'with_width': 0,
            'with_height': 0,
            'either': 0
        }

        for rect in self.rectangles:
            stats[rect.grain_direction.value] += 1

        return stats