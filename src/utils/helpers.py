"""General utility functions."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def format_currency(amount: float, symbol: str = "£") -> str:
    """Format a number as currency.

    Args:
        amount: Amount to format
        symbol: Currency symbol

    Returns:
        Formatted currency string
    """
    return f"{symbol}{amount:,.2f}"


def format_percentage(value: float, decimal_places: int = 1) -> str:
    """Format a number as percentage.

    Args:
        value: Value to format (0.1 = 10%)
        decimal_places: Number of decimal places

    Returns:
        Formatted percentage string
    """
    return f"{value * 100:.{decimal_places}f}%"


def format_dimensions(
        height: float,
        width: float,
        depth: Optional[float] = None
) -> str:
    """Format dimensions as string.

    Args:
        height: Height in mm
        width: Width in mm
        depth: Optional depth in mm

    Returns:
        Formatted dimension string
    """
    if depth is not None:
        return f"{height:.0f} × {width:.0f} × {depth:.0f} mm"
    return f"{height:.0f} × {width:.0f} mm"


def ensure_directory(path: Path) -> None:
    """Ensure a directory exists, creating if necessary.

    Args:
        path: Directory path to ensure exists
    """
    path.mkdir(parents=True, exist_ok=True)


def backup_file(filepath: Path) -> Optional[Path]:
    """Create a backup of a file.

    Args:
        filepath: File to backup

    Returns:
        Path to backup file or None if source doesn't exist
    """
    if not filepath.exists():
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = filepath.with_suffix(f".{timestamp}.bak")

    try:
        import shutil
        shutil.copy2(filepath, backup_path)
        logger.info(f"Created backup: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        return None


def merge_dicts(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries.

    Args:
        base: Base dictionary
        update: Dictionary with updates

    Returns:
        Merged dictionary (new object)
    """
    import copy
    result = copy.deepcopy(base)

    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = copy.deepcopy(value)

    return result


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to float.

    Args:
        value: Value to convert
        default: Default if conversion fails

    Returns:
        Float value or default
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert a value to int.

    Args:
        value: Value to convert
        default: Default if conversion fails

    Returns:
        Integer value or default
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split a list into chunks.

    Args:
        lst: List to chunk
        chunk_size: Size of each chunk

    Returns:
        List of chunks
    """
    return [
        lst[i:i + chunk_size]
        for i in range(0, len(lst), chunk_size)
    ]


def calculate_efficiency(used_area: float, total_area: float) -> float:
    """Calculate efficiency percentage.

    Args:
        used_area: Area actually used
        total_area: Total area available

    Returns:
        Efficiency as a decimal (0.0 to 1.0)
    """
    if total_area <= 0:
        return 0.0

    efficiency = used_area / total_area
    return min(1.0, max(0.0, efficiency))  # Clamp to 0-1