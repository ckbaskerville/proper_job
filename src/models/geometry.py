"""Geometric models for the kitchen cabinet system with grain direction support."""

from dataclasses import dataclass
from typing import Optional, Tuple, List
from enum import Enum
import math


class GrainDirection(Enum):
    """Enum for wood grain direction requirements."""
    NONE = "none"  # No grain direction requirement (MDF, etc.)
    WITH_WIDTH = "with_width"  # Grain should run with the width dimension
    WITH_HEIGHT = "with_height"  # Grain should run with the height dimension
    EITHER = "either"  # Grain can run either direction


@dataclass
class Rectangle:
    """Represents a rectangle to be packed with grain direction constraints.

    Attributes:
        width: Width of the rectangle in mm
        height: Height of the rectangle in mm
        id: Unique identifier for the rectangle
        grain_direction: Required grain direction for this piece
        component_type: Type of component this rectangle represents
    """
    width: float
    height: float
    id: str
    grain_direction: GrainDirection = GrainDirection.NONE
    component_type: Optional[str] = None

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
        """Return a rotated version of this rectangle.

        Note: Grain direction is preserved but the meaning changes
        when the rectangle is rotated.
        """
        # When rotating, we need to adjust grain direction
        new_grain_direction = self.grain_direction
        if self.grain_direction == GrainDirection.WITH_WIDTH:
            new_grain_direction = GrainDirection.WITH_HEIGHT
        elif self.grain_direction == GrainDirection.WITH_HEIGHT:
            new_grain_direction = GrainDirection.WITH_WIDTH

        return Rectangle(
            width=self.height,
            height=self.width,
            id=self.id,
            grain_direction=new_grain_direction,
            component_type=self.component_type
        )

    def can_fit_in(
        self,
        max_width: float,
        max_height: float,
        sheet_grain_direction: GrainDirection = GrainDirection.WITH_WIDTH
    ) -> bool:
        """Check if rectangle can fit in given dimensions considering grain direction.

        Args:
            max_width: Maximum available width
            max_height: Maximum available height
            sheet_grain_direction: Direction of grain on the sheet

        Returns:
            True if rectangle fits (considering rotation and grain constraints)
        """
        # Check if it fits in current orientation
        fits_current = (self.width <= max_width and self.height <= max_height)

        # Check if it fits when rotated
        fits_rotated = (self.height <= max_width and self.width <= max_height)

        # If no grain constraints, return if it fits either way
        if self.grain_direction == GrainDirection.NONE:
            return fits_current or fits_rotated

        # If grain can go either direction, return if it fits either way
        if self.grain_direction == GrainDirection.EITHER:
            return fits_current or fits_rotated

        # Check grain direction constraints
        # Assume sheet grain runs with width (standard for most sheet materials)
        if sheet_grain_direction == GrainDirection.WITH_WIDTH:
            if self.grain_direction == GrainDirection.WITH_WIDTH:
                # Rectangle's width should align with sheet's width (grain direction)
                return fits_current
            elif self.grain_direction == GrainDirection.WITH_HEIGHT:
                # Rectangle's height should align with sheet's width (grain direction)
                return fits_rotated

        return False

    def is_rotation_allowed(
        self,
        sheet_grain_direction: GrainDirection = GrainDirection.WITH_WIDTH
    ) -> bool:
        """Check if this rectangle can be rotated given grain constraints.

        Args:
            sheet_grain_direction: Direction of grain on the sheet

        Returns:
            True if rotation is allowed
        """
        # No constraints - rotation allowed
        if self.grain_direction == GrainDirection.NONE:
            return True

        # Either direction OK - rotation allowed
        if self.grain_direction == GrainDirection.EITHER:
            return True

        # Specific grain direction required - rotation not allowed
        return False

    def get_correct_orientation_for_grain(
        self,
        sheet_grain_direction: GrainDirection = GrainDirection.WITH_WIDTH
    ) -> 'Rectangle':
        """Get the rectangle in the correct orientation for grain direction.

        Args:
            sheet_grain_direction: Direction of grain on the sheet

        Returns:
            Rectangle in correct orientation
        """
        # No grain constraints - return as is
        if self.grain_direction == GrainDirection.NONE:
            return self

        # Either direction OK - return as is
        if self.grain_direction == GrainDirection.EITHER:
            return self

        # For sheet grain running with width (standard)
        if sheet_grain_direction == GrainDirection.WITH_WIDTH:
            if self.grain_direction == GrainDirection.WITH_WIDTH:
                # Rectangle should be oriented so its grain (width) aligns with sheet grain
                return self
            elif self.grain_direction == GrainDirection.WITH_HEIGHT:
                # Rectangle should be rotated so its grain (height) aligns with sheet grain
                return self.rotated()

        return self

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
            id=f"{self.id}_scaled_{factor}",
            grain_direction=self.grain_direction,
            component_type=self.component_type
        )

    def __str__(self) -> str:
        grain_str = f", grain={self.grain_direction.value}" if self.grain_direction != GrainDirection.NONE else ""
        return f"Rectangle({self.width:.0f}x{self.height:.0f}, id={self.id}{grain_str})"

    def __repr__(self) -> str:
        return (f"Rectangle(width={self.width}, height={self.height}, id='{self.id}', "
                f"grain_direction={self.grain_direction}, component_type='{self.component_type}')")


@dataclass
class PlacedRectangle:
    """Represents a rectangle that has been placed on a sheet.

    Attributes:
        x: X-coordinate of bottom-left corner
        y: Y-coordinate of bottom-left corner
        width: Width of the placed rectangle
        height: Height of the placed rectangle
        id: Identifier linking to original rectangle
        grain_direction: Grain direction of the placed rectangle
        component_type: Type of component this rectangle represents
    """
    x: float
    y: float
    width: float
    height: float
    id: str
    grain_direction: GrainDirection = GrainDirection.NONE
    component_type: Optional[str] = None

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
            id=f"{self.id}_∩_{other.id}",
            grain_direction=self.grain_direction,
            component_type=self.component_type
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
            id=self.id,
            grain_direction=self.grain_direction,
            component_type=self.component_type
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'id': self.id,
            'grain_direction': self.grain_direction.value,
            'component_type': self.component_type
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'PlacedRectangle':
        """Create from dictionary."""
        data_copy = data.copy()
        if 'grain_direction' in data_copy:
            data_copy['grain_direction'] = GrainDirection(data_copy['grain_direction'])
        return cls(**data_copy)

    def __str__(self) -> str:
        grain_str = f", grain={self.grain_direction.value}" if self.grain_direction != GrainDirection.NONE else ""
        return (
            f"PlacedRectangle({self.width:.0f}x{self.height:.0f} "
            f"at ({self.x:.0f}, {self.y:.0f}), id={self.id}{grain_str})"
        )