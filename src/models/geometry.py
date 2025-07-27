"""Geometric models for the kitchen cabinet system."""

from dataclasses import dataclass
from typing import Optional, Tuple, List
import math


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

    def __post_init__(self):
        """Validate rectangle dimensions."""
        if self.width <= 0 or self.height <= 0:
            raise ValueError(
                f"Rectangle dimensions must be positive: "
                f"{self.width}x{self.height}"
            )

    def area(self) -> float:
        """Calculate the area of the rectangle."""
        return self.width * self.height

    def perimeter(self) -> float:
        """Calculate the perimeter of the rectangle."""
        return 2 * (self.width + self.height)

    def diagonal(self) -> float:
        """Calculate the diagonal length of the rectangle."""
        return math.sqrt(self.width ** 2 + self.height ** 2)

    def aspect_ratio(self) -> float:
        """Calculate the aspect ratio (width/height)."""
        return self.width / self.height

    def rotated(self) -> 'Rectangle':
        """Return a rotated version of this rectangle."""
        return Rectangle(
            width=self.height,
            height=self.width,
            id=self.id
        )

    def can_fit_in(self, max_width: float, max_height: float) -> bool:
        """Check if rectangle can fit in given dimensions.

        Args:
            max_width: Maximum available width
            max_height: Maximum available height

        Returns:
            True if rectangle fits (considering rotation)
        """
        return (
                (self.width <= max_width and self.height <= max_height) or
                (self.height <= max_width and self.width <= max_height)
        )

    def scale(self, factor: float) -> 'Rectangle':
        """Return a scaled version of this rectangle.

        Args:
            factor: Scaling factor

        Returns:
            New Rectangle with scaled dimensions
        """
        return Rectangle(
            width=self.width * factor,
            height=self.height * factor,
            id=f"{self.id}_scaled_{factor}"
        )

    def __str__(self) -> str:
        return f"Rectangle({self.width:.0f}x{self.height:.0f}, id={self.id})"

    def __repr__(self) -> str:
        return f"Rectangle(width={self.width}, height={self.height}, id='{self.id}')"


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

    def __post_init__(self):
        """Validate placed rectangle."""
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Rectangle dimensions must be positive")
        if self.x < 0 or self.y < 0:
            raise ValueError("Rectangle position cannot be negative")

    @property
    def left(self) -> float:
        """Get the left edge coordinate."""
        return self.x

    @property
    def right(self) -> float:
        """Get the right edge coordinate."""
        return self.x + self.width

    @property
    def bottom(self) -> float:
        """Get the bottom edge coordinate."""
        return self.y

    @property
    def top(self) -> float:
        """Get the top edge coordinate."""
        return self.y + self.height

    @property
    def center(self) -> Tuple[float, float]:
        """Get the center point of the rectangle."""
        return (self.x + self.width / 2, self.y + self.height / 2)

    @property
    def corners(self) -> List[Tuple[float, float]]:
        """Get all four corners of the rectangle."""
        return [
            (self.left, self.bottom),  # Bottom-left
            (self.right, self.bottom),  # Bottom-right
            (self.right, self.top),  # Top-right
            (self.left, self.top)  # Top-left
        ]

    def area(self) -> float:
        """Calculate the area of the rectangle."""
        return self.width * self.height

    def overlaps(self, other: 'PlacedRectangle') -> bool:
        """Check if this rectangle overlaps with another.

        Args:
            other: Another PlacedRectangle to check overlap with

        Returns:
            True if rectangles overlap, False otherwise
        """
        return not (
                self.right <= other.left or
                other.right <= self.left or
                self.top <= other.bottom or
                other.top <= self.bottom
        )

    def contains_point(self, x: float, y: float) -> bool:
        """Check if a point is inside this rectangle.

        Args:
            x: X coordinate of point
            y: Y coordinate of point

        Returns:
            True if point is inside rectangle
        """
        return (
                self.left <= x <= self.right and
                self.bottom <= y <= self.top
        )

    def contains_rectangle(self, other: 'PlacedRectangle') -> bool:
        """Check if this rectangle completely contains another.

        Args:
            other: Rectangle to check

        Returns:
            True if other is completely inside this rectangle
        """
        return (
                self.left <= other.left and
                self.right >= other.right and
                self.bottom <= other.bottom and
                self.top >= other.top
        )

    def intersection(self, other: 'PlacedRectangle') -> Optional['PlacedRectangle']:
        """Calculate the intersection with another rectangle.

        Args:
            other: Another rectangle

        Returns:
            Intersection rectangle or None if no overlap
        """
        if not self.overlaps(other):
            return None

        x = max(self.left, other.left)
        y = max(self.bottom, other.bottom)
        right = min(self.right, other.right)
        top = min(self.top, other.top)

        return PlacedRectangle(
            x=x,
            y=y,
            width=right - x,
            height=top - y,
            id=f"{self.id}_∩_{other.id}"
        )

    def distance_to(self, other: 'PlacedRectangle') -> float:
        """Calculate the minimum distance to another rectangle.

        Args:
            other: Another rectangle

        Returns:
            Minimum distance between rectangles
        """
        if self.overlaps(other):
            return 0.0

        # Calculate distances between edges
        dx = max(0, max(self.left - other.right, other.left - self.right))
        dy = max(0, max(self.bottom - other.top, other.bottom - self.top))

        return math.sqrt(dx ** 2 + dy ** 2)

    def translate(self, dx: float, dy: float) -> 'PlacedRectangle':
        """Create a translated copy of this rectangle.

        Args:
            dx: Translation in X direction
            dy: Translation in Y direction

        Returns:
            New PlacedRectangle at translated position
        """
        return PlacedRectangle(
            x=self.x + dx,
            y=self.y + dy,
            width=self.width,
            height=self.height,
            id=self.id
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'id': self.id
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'PlacedRectangle':
        """Create from dictionary."""
        return cls(**data)

    def __str__(self) -> str:
        return (
            f"PlacedRectangle({self.width:.0f}x{self.height:.0f} "
            f"at ({self.x:.0f}, {self.y:.0f}), id={self.id})"
        )