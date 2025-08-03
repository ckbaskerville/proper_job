"""Data access layer for the application."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

from src.config.constants import (
    RUNNERS_FILE,
    MATERIALS_FILE,
    HINGES_FILE,
    LABOR_COSTS_FILE,
    DBC_DRAWERS_OAK_FILE,
    DBC_DRAWERS_WALNUT_FILE
)

logger = logging.getLogger(__name__)


class DataRepository:
    """Repository for accessing application data."""

    def __init__(self, base_path: Optional[Path] = None):
        """Initialize the repository.

        Args:
            base_path: Base path for data files (defaults to config paths)
        """
        self.base_path = base_path

    def _get_file_path(self, filename: Path) -> Path:
        """Get the full path for a data file."""
        if self.base_path:
            return self.base_path / filename.name
        return filename

    def _load_json_file(self, filepath: Path) -> Any:
        """Load data from a JSON file.

        Args:
            filepath: Path to the JSON file

        Returns:
            Parsed JSON data

        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If file is not valid JSON
        """
        full_path = self._get_file_path(filepath)

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Loaded data from {full_path}")
                return data
        except FileNotFoundError:
            logger.error(f"File not found: {full_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {full_path}: {e}")
            raise

    def _save_json_file(self, data: Any, filepath: Path) -> None:
        """Save data to a JSON file.

        Args:
            data: Data to save
            filepath: Path to save to

        Raises:
            IOError: If file cannot be written
        """
        full_path = self._get_file_path(filepath)

        try:
            # Ensure directory exists
            full_path.parent.mkdir(parents=True, exist_ok=True)

            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                logger.info(f"Saved data to {full_path}")
        except IOError as e:
            logger.error(f"Failed to save to {full_path}: {e}")
            raise

    def load_runners(self) -> List[Dict[str, Any]]:
        """Load runner configurations.

        Returns:
            List of runner brand configurations
        """
        return self._load_json_file(RUNNERS_FILE)

    def save_runners(self, data: List[Dict[str, Any]]) -> None:
        """Save runner configurations."""
        self._save_json_file(data, RUNNERS_FILE)


    def load_dbc_drawers(self) -> Dict[str, Any]:
        """Load DBC drawer configurations.

        Returns:
            Dictionary containing DBC drawer data
        """
        try:
            # Load both files and merge them
            oak_data = self._load_json_file(DBC_DRAWERS_OAK_FILE)
            walnut_data = self._load_json_file(DBC_DRAWERS_WALNUT_FILE)

            # Combine into a single dictionary
            return {
                "Oak": oak_data,
                "Walnut": walnut_data
            }

        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load DBC drawers: {e}")
            raise

    def load_hinges(self) -> Dict[str, Any]:
        """Load hinge data from file.

        Returns:
            Dictionary containing hinge data

        Raises:
            FileNotFoundError: If hinge file doesn't exist
            JSONDecodeError: If file contains invalid JSON
        """
        try:
            with open(HINGES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Handle both list and dict formats
            if isinstance(data, list) and data:
                return data[0]
            elif isinstance(data, dict):
                return data
            else:
                # Return default structure if empty
                return {"Hinges": []}

        except FileNotFoundError:
            logger.warning(f"Hinges file not found: {HINGES_FILE}")
            # Return default structure
            return {"Hinges": []}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in hinges file: {e}")
            raise

    def save_hinges(self, hinges_data: Dict[str, Any]) -> None:
        """Save hinge data to file.

        Args:
            hinges_data: Dictionary containing hinge data

        Raises:
            OSError: If file cannot be written
            JSONDecodeError: If data cannot be serialized
        """
        try:
            # Ensure directory exists
            Path(HINGES_FILE).parent.mkdir(parents=True, exist_ok=True)

            # Save as list format to match other resource files
            data_to_save = [hinges_data] if isinstance(hinges_data, dict) else hinges_data

            with open(HINGES_FILE, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved hinges data to {HINGES_FILE}")

        except (OSError, json.JSONEncodeError) as e:
            logger.error(f"Failed to save hinges data: {e}")
            raise

    def load_materials(self) -> Dict[str, Any]:
        """Load material configurations.

        Returns:
            Material configuration dictionary
        """
        # File contains a list with one dict
        data = self._load_json_file(MATERIALS_FILE)
        return data[0] if isinstance(data, list) else data

    def save_materials(self, data: Dict[str, Any]) -> None:
        """Save material configurations."""
        # Maintain original file format
        self._save_json_file([data], MATERIALS_FILE)

    def load_labor_costs(self) -> Dict[str, Any]:
        """Load labor cost configurations.

        Returns:
            Labor cost configuration dictionary
        """
        # File contains a list with one dict
        data = self._load_json_file(LABOR_COSTS_FILE)
        return data[0] if isinstance(data, list) else data

    def save_labor_costs(self, data: Dict[str, Any]) -> None:
        """Save labor cost configurations."""
        # Maintain original file format
        self._save_json_file([data], LABOR_COSTS_FILE)


class ProjectRepository:
    """Repository for project save/load operations."""

    @staticmethod
    def save_project(
            filepath: Path,
            units: List[Any],
            settings: Dict[str, Any]
    ) -> None:
        """Save a project to file.

        Args:
            filepath: Path to save project to
            units: List of cabinet units
            settings: Project settings
        """
        project_data = {
            'version': '2.0',
            'units': [ProjectRepository._serialize_unit(unit) for unit in units],
            'settings': settings
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(project_data, f, indent=2)

        logger.info(f"Project saved to {filepath}")

    @staticmethod
    def load_project(filepath: Path) -> Dict[str, Any]:
        """Load a project from file.

        Args:
            filepath: Path to load project from

        Returns:
            Project data dictionary
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        logger.info(f"Project loaded from {filepath}")
        return data

    @staticmethod
    def _serialize_unit(unit: Any) -> Dict[str, Any]:
        """Serialize a cabinet unit for saving."""
        # Implementation depends on Cabinet structure
        return {}
