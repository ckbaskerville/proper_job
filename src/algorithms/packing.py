"""Bin packing algorithms for 2D rectangle packing with grain direction support."""

import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Set
from dataclasses import dataclass

from src.models.geometry import Rectangle, PlacedRectangle, GrainDirection

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
    """Bottom-Left Fill algorithm for 2D bin packing with grain direction support.

    This algorithm places each rectangle as far bottom and left as possible,
    while respecting grain direction constraints.
    """

    def __init__(
        self,
        allow_rotation: bool = True,
        sheet_grain_direction: GrainDirection = GrainDirection.WITH_WIDTH,
        cutting_margin: float = 3.0
    ):
        """Initialize the packer.

        Args:
            allow_rotation: Whether rectangles can be rotated (overridden by grain constraints)
            sheet_grain_direction: Direction of grain on the sheet material
            cutting_margin: Margin between rectangles in mm
        """
        self.allow_rotation = allow_rotation
        self.sheet_grain_direction = sheet_grain_direction
        self.cutting_margin = cutting_margin

    def pack(
            self,
            rectangles: List[Rectangle],
            bin_width: float,
            bin_height: float
    ) -> List[List[PlacedRectangle]]:
        """Pack rectangles using Bottom-Left Fill algorithm with grain constraints.

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
                        f"with grain {rect.grain_direction.value} "
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
        """Try to place a rectangle in a bin respecting grain constraints.

        Args:
            rect: Rectangle to place
            bin_items: Current items in the bin
            bin_width: Bin width
            bin_height: Bin height

        Returns:
            True if rectangle was placed
        """
        # Get the correct orientation for this rectangle based on grain direction
        oriented_rect = rect.get_correct_orientation_for_grain(self.sheet_grain_direction)

        # Try the correctly oriented rectangle first
        position = self._find_bottom_left_position(
            oriented_rect.width, oriented_rect.height, bin_items, bin_width, bin_height
        )

        if position:
            x, y = position
            placed_rect = PlacedRectangle(
                x=x, y=y,
                width=oriented_rect.width,
                height=oriented_rect.height,
                id=rect.id,
                grain_direction=oriented_rect.grain_direction,
                component_type=rect.component_type
            )
            bin_items.append(placed_rect)
            return True

        # Try rotation only if allowed and grain constraints permit
        if (self.allow_rotation and
            rect.is_rotation_allowed(self.sheet_grain_direction) and
            rect.width != rect.height):  # Don't bother rotating squares

            rotated_rect = oriented_rect.rotated()
            position = self._find_bottom_left_position(
                rotated_rect.width, rotated_rect.height, bin_items, bin_width, bin_height
            )

            if position:
                x, y = position
                placed_rect = PlacedRectangle(
                    x=x, y=y,
                    width=rotated_rect.width,
                    height=rotated_rect.height,
                    id=rect.id,
                    grain_direction=rotated_rect.grain_direction,
                    component_type=rect.component_type
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
        # Check bin boundaries (no margin needed at edges)
        if x + width > bin_width or y + height > bin_height:
            return False

        margin = self.cutting_margin
        
        # Check overlaps with existing rectangles (with margin between rectangles only)
        # Margin is only needed between rectangles, not at sheet edges
        for rect in placed:
            # Calculate actual positions and sizes
            test_left = x
            test_bottom = y
            test_right = x + width
            test_top = y + height
            
            rect_left = rect.x
            rect_bottom = rect.y
            rect_right = rect.x + rect.width
            rect_top = rect.y + rect.height
            
            # Check if rectangles overlap (without margin) - if they do, placement is invalid
            if not (test_right <= rect_left or rect_right <= test_left or
                    test_top <= rect_bottom or rect_top <= test_bottom):
                # They overlap - invalid placement
                return False
            
            # Calculate horizontal gap (0 if they overlap horizontally)
            if test_right <= rect_left:
                # Test is to the left of placed rect
                h_gap = rect_left - test_right
            elif test_left >= rect_right:
                # Test is to the right of placed rect
                h_gap = test_left - rect_right
            else:
                # They overlap horizontally
                h_gap = 0
            
            # Calculate vertical gap (0 if they overlap vertically)
            if test_top <= rect_bottom:
                # Test is below placed rect
                v_gap = rect_bottom - test_top
            elif test_bottom >= rect_top:
                # Test is above placed rect
                v_gap = test_bottom - rect_top
            else:
                # They overlap vertically
                v_gap = 0
            
            # For axis-aligned rectangles, if they don't overlap, at least one gap is > 0
            # The minimum distance is the non-zero gap (or 0 if they overlap)
            # We need at least 'margin' distance between rectangles
            if h_gap > 0 and v_gap > 0:
                # Diagonally separated - need margin in at least one direction
                # Actually, for cutting, we need margin in the direction of separation
                # If separated diagonally, we need margin in both directions
                if h_gap < margin or v_gap < margin:
                    return False
            elif h_gap > 0:
                # Horizontally separated - need at least margin horizontal gap
                if h_gap < margin:
                    return False
            elif v_gap > 0:
                # Vertically separated - need at least margin vertical gap
                if v_gap < margin:
                    return False
            # If both gaps are 0, they overlap (already checked above)

        return True


class BinPacker:
    """High-level bin packing interface with grain direction support."""

    def __init__(
            self,
            bin_width: float,
            bin_height: float,
            strategy: Optional[PackingStrategy] = None,
            material_type: str = "MDF",
            cutting_margin: float = 3.0
    ):
        """Initialize the bin packer.

        Args:
            bin_width: Width of bins
            bin_height: Height of bins
            strategy: Packing strategy to use
            material_type: Type of material to determine grain constraints
            cutting_margin: Margin between rectangles in mm
        """
        self.bin_width = bin_width
        self.bin_height = bin_height
        self.material_type = material_type
        self.cutting_margin = cutting_margin

        # Determine if this material has grain direction constraints
        grain_materials = {"veneer", "hardwood", "laminate", "plywood"}
        has_grain = any(grain_mat in material_type.lower() for grain_mat in grain_materials)

        # Default strategy based on material
        if strategy is None:
            self.strategy = BottomLeftFillPacker(
                allow_rotation=not has_grain,  # Don't allow rotation for grain materials
                sheet_grain_direction=GrainDirection.WITH_WIDTH,
                cutting_margin=cutting_margin
            )
        else:
            self.strategy = strategy
            # Update strategy margin if it supports it
            if hasattr(self.strategy, 'cutting_margin'):
                self.strategy.cutting_margin = cutting_margin

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

    def validate_grain_compliance(
            self,
            bins: List[List[PlacedRectangle]]
    ) -> Tuple[bool, List[str]]:
        """Validate that all placed rectangles comply with grain direction requirements.

        Args:
            bins: List of bins with placed rectangles

        Returns:
            Tuple of (is_compliant, list_of_violations)
        """
        violations = []

        for bin_idx, bin_items in enumerate(bins):
            for rect in bin_items:
                if rect.grain_direction == GrainDirection.NONE:
                    continue  # No constraints

                if rect.grain_direction == GrainDirection.EITHER:
                    continue  # Any orientation OK

                # Check if grain direction is respected
                # For standard sheet orientation (grain with width):
                if rect.grain_direction == GrainDirection.WITH_WIDTH:
                    # Rectangle's width should be the primary grain direction
                    if rect.width < rect.height:
                        violations.append(
                            f"Bin {bin_idx}: Rectangle {rect.id} violates grain direction "
                            f"(width {rect.width} < height {rect.height} but grain should run with width)"
                        )
                elif rect.grain_direction == GrainDirection.WITH_HEIGHT:
                    # Rectangle's height should be the primary grain direction
                    if rect.height < rect.width:
                        violations.append(
                            f"Bin {bin_idx}: Rectangle {rect.id} violates grain direction "
                            f"(height {rect.height} < width {rect.width} but grain should run with height)"
                        )

        return len(violations) == 0, violations