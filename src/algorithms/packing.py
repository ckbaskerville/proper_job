"""Bin packing algorithms for 2D rectangle packing."""

import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Set
from dataclasses import dataclass

from src.models.geometry import Rectangle, PlacedRectangle

logger = logging.getLogger(__name__)


class PackingStrategy(ABC):
    """Abstract base class for packing strategies."""

    @abstractmethod
    def pack(
            self,
            rectangles: List[Rectangle],
            bin_width: float,
            bin_height: float
    ) -> List[List[PlacedRectangle]]:
        """Pack rectangles into bins.

        Args:
            rectangles: List of rectangles to pack
            bin_width: Width of each bin
            bin_height: Height of each bin

        Returns:
            List of bins, each containing placed rectangles
        """
        pass


class BottomLeftFillPacker(PackingStrategy):
    """Bottom-Left Fill algorithm for 2D bin packing.

    This algorithm places each rectangle as far bottom and left as possible.
    """

    def __init__(self, allow_rotation: bool = True):
        """Initialize the packer.

        Args:
            allow_rotation: Whether rectangles can be rotated
        """
        self.allow_rotation = allow_rotation

    def pack(
            self,
            rectangles: List[Rectangle],
            bin_width: float,
            bin_height: float
    ) -> List[List[PlacedRectangle]]:
        """Pack rectangles using Bottom-Left Fill algorithm.

        Args:
            rectangles: List of rectangles to pack
            bin_width: Width of each bin
            bin_height: Height of each bin

        Returns:
            List of bins with placed rectangles
        """
        bins: List[List[PlacedRectangle]] = []

        for rect in rectangles:
            placed = False

            # Try to place in existing bins
            for bin_items in bins:
                if self._try_place_rectangle(rect, bin_items, bin_width, bin_height):
                    placed = True
                    break

            # If not placed, create new bin
            if not placed:
                new_bin = []
                if self._try_place_rectangle(rect, new_bin, bin_width, bin_height):
                    bins.append(new_bin)
                else:
                    logger.warning(
                        f"Rectangle {rect.id} ({rect.width}x{rect.height}) "
                        f"cannot fit in bin ({bin_width}x{bin_height})"
                    )

        return bins

    def _try_place_rectangle(
            self,
            rect: Rectangle,
            bin_items: List[PlacedRectangle],
            bin_width: float,
            bin_height: float
    ) -> bool:
        """Try to place a rectangle in a bin.

        Args:
            rect: Rectangle to place
            bin_items: Current items in the bin
            bin_width: Bin width
            bin_height: Bin height

        Returns:
            True if rectangle was placed
        """
        # Try normal orientation
        position = self._find_bottom_left_position(
            rect.width, rect.height, bin_items, bin_width, bin_height
        )

        if position:
            x, y = position
            placed_rect = PlacedRectangle(
                x=x, y=y,
                width=rect.width,
                height=rect.height,
                id=rect.id
            )
            bin_items.append(placed_rect)
            return True

        # Try rotated orientation if allowed
        if self.allow_rotation and rect.width != rect.height:
            position = self._find_bottom_left_position(
                rect.height, rect.width, bin_items, bin_width, bin_height
            )

            if position:
                x, y = position
                placed_rect = PlacedRectangle(
                    x=x, y=y,
                    width=rect.height,
                    height=rect.width,
                    id=rect.id
                )
                bin_items.append(placed_rect)
                return True

        return False

    def _find_bottom_left_position(
            self,
            width: float,
            height: float,
            placed: List[PlacedRectangle],
            bin_width: float,
            bin_height: float
    ) -> Optional[Tuple[float, float]]:
        """Find the bottom-left position where a rectangle can be placed.

        Args:
            width: Rectangle width
            height: Rectangle height
            placed: Already placed rectangles
            bin_width: Bin width
            bin_height: Bin height

        Returns:
            (x, y) position or None if no position found
        """
        if width > bin_width or height > bin_height:
            return None

        # Generate candidate positions
        candidates = self._generate_candidate_positions(
            placed, bin_width, bin_height
        )

        # Sort by bottom-left preference (y first, then x)
        candidates.sort(key=lambda pos: (pos[1], pos[0]))

        # Test each candidate
        for x, y in candidates:
            if self._can_place_at(
                    x, y, width, height, placed, bin_width, bin_height
            ):
                return (x, y)

        return None

    def _generate_candidate_positions(
            self,
            placed: List[PlacedRectangle],
            bin_width: float,
            bin_height: float
    ) -> List[Tuple[float, float]]:
        """Generate candidate positions for rectangle placement.

        Args:
            placed: Already placed rectangles
            bin_width: Bin width
            bin_height: Bin height

        Returns:
            List of (x, y) candidate positions
        """
        candidates = [(0.0, 0.0)]  # Always try bottom-left corner

        for rect in placed:
            # Right edge of rectangle
            candidates.append((rect.right, rect.y))
            # Top edge of rectangle
            candidates.append((rect.x, rect.top))
            # Top-right corner
            candidates.append((rect.right, rect.top))

        # Remove duplicates and out-of-bounds positions
        unique_candidates = []
        seen = set()

        for x, y in candidates:
            if (x, y) not in seen and x < bin_width and y < bin_height:
                seen.add((x, y))
                unique_candidates.append((x, y))

        return unique_candidates

    def _can_place_at(
            self,
            x: float,
            y: float,
            width: float,
            height: float,
            placed: List[PlacedRectangle],
            bin_width: float,
            bin_height: float
    ) -> bool:
        """Check if a rectangle can be placed at given position.

        Args:
            x: X position
            y: Y position
            width: Rectangle width
            height: Rectangle height
            placed: Already placed rectangles
            bin_width: Bin width
            bin_height: Bin height

        Returns:
            True if rectangle can be placed
        """
        # Check bin boundaries
        if x + width > bin_width or y + height > bin_height:
            return False

        # Check overlaps with existing rectangles
        test_rect = PlacedRectangle(
            x=x, y=y,
            width=width,
            height=height,
            id="test"
        )

        for rect in placed:
            if test_rect.overlaps(rect):
                return False

        return True


class BinPacker:
    """High-level bin packing interface."""

    def __init__(
            self,
            bin_width: float,
            bin_height: float,
            strategy: Optional[PackingStrategy] = None
    ):
        """Initialize the bin packer.

        Args:
            bin_width: Width of bins
            bin_height: Height of bins
            strategy: Packing strategy to use
        """
        self.bin_width = bin_width
        self.bin_height = bin_height
        self.strategy = strategy or BottomLeftFillPacker()

    def pack(
            self,
            rectangles: List[Rectangle]
    ) -> List[List[PlacedRectangle]]:
        """Pack rectangles into bins.

        Args:
            rectangles: List of rectangles to pack

        Returns:
            List of bins with placed rectangles
        """
        return self.strategy.pack(rectangles, self.bin_width, self.bin_height)

    def calculate_efficiency(
            self,
            bins: List[List[PlacedRectangle]]
    ) -> float:
        """Calculate packing efficiency.

        Args:
            bins: List of bins with placed rectangles

        Returns:
            Overall efficiency (0.0 to 1.0)
        """
        if not bins:
            return 0.0

        total_rect_area = sum(
            rect.width * rect.height
            for bin_items in bins
            for rect in bin_items
        )

        total_bin_area = len(bins) * self.bin_width * self.bin_height

        return total_rect_area / total_bin_area if total_bin_area > 0 else 0.0

    def get_bin_efficiency(
            self,
            bin_items: List[PlacedRectangle]
    ) -> float:
        """Calculate efficiency for a single bin.

        Args:
            bin_items: Rectangles in the bin

        Returns:
            Bin efficiency (0.0 to 1.0)
        """
        rect_area = sum(rect.width * rect.height for rect in bin_items)
        bin_area = self.bin_width * self.bin_height

        return rect_area / bin_area if bin_area > 0 else 0.0
