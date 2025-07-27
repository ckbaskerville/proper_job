"""Genetic algorithm implementation for optimization problems."""

import random
import logging
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Generic, TypeVar, Callable
from dataclasses import dataclass, field

from src.config.constants import (
    GA_POPULATION_SIZE,
    GA_MUTATION_RATE,
    GA_GENERATIONS,
    GA_TOURNAMENT_SIZE,
    GA_ELITE_PERCENTAGE
)

logger = logging.getLogger(__name__)

# Type variable for generic individual
T = TypeVar('T')


@dataclass
class Individual(Generic[T]):
    """Represents one solution in the genetic algorithm.

    Attributes:
        genes: The genetic representation of the solution
        fitness: Cached fitness value (None if not evaluated)
    """
    genes: List[T]
    fitness: Optional[float] = None

    def __post_init__(self):
        """Validate individual after creation."""
        if not self.genes:
            raise ValueError("Individual must have at least one gene")

    def mutate(self, mutation_rate: float) -> None:
        """Mutate this individual's genes.

        Args:
            mutation_rate: Probability of mutation for each gene
        """
        raise NotImplementedError("Subclasses must implement mutate()")

    def __lt__(self, other: 'Individual') -> bool:
        """Compare individuals by fitness (for sorting)."""
        if self.fitness is None or other.fitness is None:
            return False
        return self.fitness < other.fitness


class GeneticAlgorithm(ABC, Generic[T]):
    """Abstract base class for genetic algorithms.

    This class provides the framework for genetic algorithms and must be
    subclassed with specific implementations for the problem domain.
    """

    def __init__(
            self,
            population_size: int = GA_POPULATION_SIZE,
            mutation_rate: float = GA_MUTATION_RATE,
            tournament_size: int = GA_TOURNAMENT_SIZE,
            elite_percentage: float = GA_ELITE_PERCENTAGE
    ):
        """Initialize the genetic algorithm.

        Args:
            population_size: Number of individuals in population
            mutation_rate: Probability of mutation
            tournament_size: Size of tournament for selection
            elite_percentage: Percentage of population to keep as elite
        """
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.tournament_size = tournament_size
        self.elite_percentage = elite_percentage
        self.population: List[Individual[T]] = []
        self.generation = 0

        # Validate parameters
        if population_size < 2:
            raise ValueError("Population size must be at least 2")
        if not 0 <= mutation_rate <= 1:
            raise ValueError("Mutation rate must be between 0 and 1")
        if tournament_size < 1:
            raise ValueError("Tournament size must be at least 1")
        if not 0 <= elite_percentage <= 1:
            raise ValueError("Elite percentage must be between 0 and 1")

    @abstractmethod
    def create_individual(self) -> Individual[T]:
        """Create a new random individual.

        Returns:
            A new Individual instance
        """
        pass

    @abstractmethod
    def evaluate_fitness(self, individual: Individual[T]) -> float:
        """Evaluate the fitness of an individual.

        Args:
            individual: Individual to evaluate

        Returns:
            Fitness value (lower is better for minimization)
        """
        pass

    @abstractmethod
    def crossover(
            self,
            parent1: Individual[T],
            parent2: Individual[T]
    ) -> Tuple[Individual[T], Individual[T]]:
        """Create offspring from two parents.

        Args:
            parent1: First parent
            parent2: Second parent

        Returns:
            Tuple of two offspring
        """
        pass

    @abstractmethod
    def mutate_individual(self, individual: Individual[T]) -> None:
        """Mutate an individual.

        Args:
            individual: Individual to mutate
        """
        pass

    def create_initial_population(self) -> None:
        """Create the initial population."""
        logger.info(f"Creating initial population of {self.population_size}")

        self.population = []
        for _ in range(self.population_size):
            individual = self.create_individual()
            individual.fitness = self.evaluate_fitness(individual)
            self.population.append(individual)

        # Sort by fitness
        self.population.sort(key=lambda ind: ind.fitness)

        best_fitness = self.population[0].fitness
        logger.info(f"Initial population created. Best fitness: {best_fitness}")

    def tournament_selection(self) -> Individual[T]:
        """Select an individual using tournament selection.

        Returns:
            Selected individual
        """
        tournament = random.sample(self.population, self.tournament_size)
        return min(tournament, key=lambda ind: ind.fitness)

    def evolve_generation(self) -> None:
        """Evolve the population by one generation."""
        new_population = []

        # Keep elite individuals
        elite_size = max(1, int(self.population_size * self.elite_percentage))
        elite = self.population[:elite_size]
        new_population.extend(elite)

        # Generate rest of population through crossover and mutation
        while len(new_population) < self.population_size:
            # Selection
            parent1 = self.tournament_selection()
            parent2 = self.tournament_selection()

            # Crossover
            child1, child2 = self.crossover(parent1, parent2)

            # Mutation
            if random.random() < self.mutation_rate:
                self.mutate_individual(child1)
            if random.random() < self.mutation_rate:
                self.mutate_individual(child2)

            # Evaluate fitness
            child1.fitness = self.evaluate_fitness(child1)
            child2.fitness = self.evaluate_fitness(child2)

            # Add to population
            new_population.extend([child1, child2])

        # Trim to exact population size
        self.population = new_population[:self.population_size]

        # Sort by fitness
        self.population.sort(key=lambda ind: ind.fitness)

        self.generation += 1

    def evolve(
            self,
            generations: int = GA_GENERATIONS,
            target_fitness: Optional[float] = None,
            progress_callback: Optional[Callable[[int, float], None]] = None
    ) -> Individual[T]:
        """Run the genetic algorithm for multiple generations.

        Args:
            generations: Number of generations to evolve
            target_fitness: Stop if this fitness is achieved
            progress_callback: Optional callback for progress updates

        Returns:
            Best individual found
        """
        logger.info(f"Starting evolution for {generations} generations")

        # Create initial population if needed
        if not self.population:
            self.create_initial_population()

        best_overall = self.population[0]
        generations_without_improvement = 0

        for gen in range(generations):
            # Evolve one generation
            self.evolve_generation()

            # Check for improvement
            current_best = self.population[0]
            if current_best.fitness < best_overall.fitness:
                best_overall = current_best
                generations_without_improvement = 0
                logger.info(
                    f"Generation {self.generation}: "
                    f"New best fitness = {best_overall.fitness}"
                )
            else:
                generations_without_improvement += 1

            # Progress callback
            if progress_callback:
                progress_callback(self.generation, best_overall.fitness)

            # Check termination conditions
            if target_fitness and best_overall.fitness <= target_fitness:
                logger.info(
                    f"Target fitness {target_fitness} achieved at "
                    f"generation {self.generation}"
                )
                break

            # Early stopping if no improvement
            if generations_without_improvement > generations * 0.2:
                logger.info(
                    f"Early stopping at generation {self.generation} - "
                    f"no improvement for {generations_without_improvement} generations"
                )
                break

        logger.info(
            f"Evolution complete. Best fitness: {best_overall.fitness}"
        )
        return best_overall

    def get_population_stats(self) -> dict:
        """Get statistics about the current population.

        Returns:
            Dictionary with population statistics
        """
        if not self.population:
            return {
                'generation': 0,
                'size': 0,
                'best_fitness': None,
                'worst_fitness': None,
                'average_fitness': None
            }

        fitnesses = [ind.fitness for ind in self.population if ind.fitness is not None]

        return {
            'generation': self.generation,
            'size': len(self.population),
            'best_fitness': min(fitnesses) if fitnesses else None,
            'worst_fitness': max(fitnesses) if fitnesses else None,
            'average_fitness': sum(fitnesses) / len(fitnesses) if fitnesses else None
        }