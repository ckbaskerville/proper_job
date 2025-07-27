"""Utility functions for algorithms module."""

import logging
from typing import List, Tuple, Dict
from collections import defaultdict

from src.models.geometry import Rectangle, PlacedRectangle

logger = logging.getLogger(__name__)


def calculate_total_area(rectangles: List[Rectangle]) -> float:
    """Calculate total area of all rectangles.

    Args:
        rectangles: List of rectangles

    Returns:
        Total area
    """
    return sum(rect.area() for rect in rectangles)


def calculate_bin_utilization(
        bin_items: List[PlacedRectangle],
        bin_width: float,
        bin_height: float
) -> float:
    """Calculate utilization percentage of a bin.

    Args:
        bin_items: Items placed in the bin
        bin_width: Width of the bin
        bin_height: Height of the bin

    Returns:
        Utilization percentage (0.0 to 100.0)
    """
    if not bin_items:
        return 0.0

    used_area = sum(item.width * item.height for item in bin_items)
    total_area = bin_width * bin_height

    return (used_area / total_area) * 100 if total_area > 0 else 0.0


def get_packing_statistics(
        bins: List[List[PlacedRectangle]],
        bin_width: float,
        bin_height: float
) -> Dict[str, float]:
    """Get comprehensive statistics about a packing solution.

    Args:
        bins: List of bins with placed items
        bin_width: Width of each bin
        bin_height: Height of each bin

    Returns:
        Dictionary with statistics
    """
    if not bins:
        return {
            'num_bins': 0,
            'total_items': 0,
            'average_utilization': 0.0,
            'min_utilization': 0.0,
            'max_utilization': 0.0,
            'total_area_used': 0.0,
            'total_area_available': 0.0,
            'overall_efficiency': 0.0
        }

    utilizations = []
    total_items = 0
    total_area_used = 0.0

    for bin_items in bins:
        util = calculate_bin_utilization(bin_items, bin_width, bin_height)
        utilizations.append(util)
        total_items += len(bin_items)
        total_area_used += sum(item.width * item.height for item in bin_items)

    total_area_available = len(bins) * bin_width * bin_height

    return {
        'num_bins': len(bins),
        'total_items': total_items,
        'average_utilization': sum(utilizations) / len(utilizations),
        'min_utilization': min(utilizations),
        'max_utilization': max(utilizations),
        'total_area_used': total_area_used,
        'total_area_available': total_area_available,
        'overall_efficiency': (total_area_used / total_area_available * 100
                               if total_area_available > 0 else 0.0)
    }


def validate_packing(
        bins: List[List[PlacedRectangle]],
        rectangles: List[Rectangle],
        bin_width: float,
        bin_height: float
) -> Tuple[bool, List[str]]:
    """Validate that a packing solution is correct.

    Args:
        bins: Packing solution
        rectangles: Original rectangles
        bin_width: Bin width
        bin_height: Bin height

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Check all rectangles are placed
    placed_ids = set()
    for bin_items in bins:
        for item in bin_items:
            placed_ids.add(item.id)

    original_ids = {rect.id for rect in rectangles}
    missing_ids = original_ids - placed_ids
    extra_ids = placed_ids - original_ids

    if missing_ids:
        errors.append(f"Missing rectangles: {missing_ids}")
    if extra_ids:
        errors.append(f"Extra rectangles: {extra_ids}")

    # Check no overlaps and bounds
    for bin_idx, bin_items in enumerate(bins):
        # Check bounds
        for item in bin_items:
            if item.x < 0 or item.y < 0:
                errors.append(
                    f"Bin {bin_idx}: Rectangle {item.id} has negative position"
                )
            if item.right > bin_width or item.top > bin_height:
                errors.append(
                    f"Bin {bin_idx}: Rectangle {item.id} exceeds bin bounds"
                )

        # Check overlaps
        for i, item1 in enumerate(bin_items):
            for item2 in bin_items[i + 1:]:
                if item1.overlaps(item2):
                    errors.append(
                        f"Bin {bin_idx}: Rectangles {item1.id} and "
                        f"{item2.id} overlap"
                    )

    return len(errors) == 0, errors


def group_rectangles_by_size(
        rectangles: List[Rectangle],
        tolerance: float = 0.01
) -> Dict[Tuple[float, float], List[Rectangle]]:
    """Group rectangles by similar dimensions.

    Args:
        rectangles: List of rectangles
        tolerance: Relative tolerance for grouping

    Returns:
        Dictionary mapping (width, height) to list of rectangles
    """
    groups = defaultdict(list)

    for rect in rectangles:
        # Find matching group
        found_group = False
        for (w, h), group_rects in groups.items():
            if (abs(rect.width - w) / w < tolerance and
                    abs(rect.height - h) / h < tolerance):
                groups[(w, h)].append(rect)
                found_group = True
                break

        if not found_group:
            groups[(rect.width, rect.height)].append(rect)

    return dict(groups)