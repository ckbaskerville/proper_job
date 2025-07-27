"""Geometric models for the kitchen cabinet system."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Rectangle:
    """Represents a rectangle to be packed.

    Attributes:
        width: Width of the rectangle in mm
        height: Height of the rectangle in mm
        id: Unique identifier for the rectangle
    """
    width: float
    height: float
    id: str

    def area(self) -> float:
        """Calculate the area of the rectangle."""
        return self.width * self.height

    def rotated(self) -> 'Rectangle':
        """Return a rotated version of this rectangle."""
        return Rectangle(
            width=self.height,
            height=self.width,
            id=self.id
        )

    def can_fit_in(self, max_width: float, max_height: float) -> bool:
        """Check if rectangle can fit in given dimensions."""
        return (self.width <= max_width and self.height <= max_height)

    def __str__(self) -> str:
        return f"Rectangle({self.width}x{self.height}, id={self.id})"


@dataclass
class PlacedRectangle:
    """Represents a rectangle that has been placed on a sheet.

    Attributes:
        x: X-coordinate of bottom-left corner
        y: Y-coordinate of bottom-left corner
        width: Width of the placed rectangle
        height: Height of the placed rectangle
        id: Identifier linking to original rectangle
    """
    x: float
    y: float
    width: float
    height: float
    id: str

    @property
    def right(self) -> float:
        """Get the right edge coordinate."""
        return self.x + self.width

    @property
    def top(self) -> float:
        """Get the top edge coordinate."""
        return self.y + self.height

    def overlaps(self, other: 'PlacedRectangle') -> bool:
        """Check if this rectangle overlaps with another.

        Args:
            other: Another PlacedRectangle to check overlap with

        Returns:
            True if rectangles overlap, False otherwise
        """
        return not (
                self.right <= other.x or
                other.right <= self.x or
                self.top <= other.y or
                other.top <= self.y
        )

    def contains_point(self, x: float, y: float) -> bool:
        """Check if a point is inside this rectangle."""
        return (
                self.x <= x <= self.right and
                self.y <= y <= self.top
        )
