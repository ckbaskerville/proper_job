"""Base classes and interfaces for models."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass

from .geometry import Rectangle


class ValidationError(Exception):
    """Raised when model validation fails."""
    pass


class ComponentType(Enum):
    """Types of cabinet components."""
    CARCASS = "carcass"
    DRAWER = "drawer"
    DOOR = "door"
    FACE_FRAME = "face_frame"
    SHELF = "shelf"


class Component(ABC):
    """Abstract base class for cabinet components."""

    @abstractmethod
    def get_parts(self) -> List[Rectangle]:
        """Get all rectangular parts for this component.

        Returns:
            List of Rectangle objects representing parts to cut
        """
        pass

    @abstractmethod
    def get_total_area(self) -> float:
        """Calculate total material area needed.

        Returns:
            Total area in square millimeters
        """
        pass

    @abstractmethod
    def validate(self) -> None:
        """Validate component specifications.

        Raises:
            ValidationError: If component specifications are invalid
        """
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert component to dictionary for serialization.

        Returns:
            Dictionary representation of component
        """
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Component':
        """Create component from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            Component instance
        """
        pass

    @property
    @abstractmethod
    def component_type(self) -> ComponentType:
        """Get the type of this component."""
        pass

    def get_material_volume(self) -> float:
        """Calculate material volume for cost estimation.

        Returns:
            Volume in cubic millimeters
        """
        # Default implementation - can be overridden
        return self.get_total_area() * getattr(self, 'thickness', 18.0)


@dataclass
class Dimensions:
    """Standard dimensions for components."""
    height: float
    width: float
    depth: float

    def __post_init__(self):
        """Validate dimensions."""
        if self.height <= 0 or self.width <= 0 or self.depth <= 0:
            raise ValidationError("All dimensions must be positive")

    def to_string(self) -> str:
        """Format dimensions as string."""
        return f"{self.height:.0f} × {self.width:.0f} × {self.depth:.0f}mm"

    @property
    def volume(self) -> float:
        """Calculate volume."""
        return self.height * self.width * self.depth
