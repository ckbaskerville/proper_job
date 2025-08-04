"""Labor cost management."""

import logging
from typing import Dict, Optional, Any

from src.business.material_manager import MaterialManager

logger = logging.getLogger(__name__)


class LaborManager:
    """Manages labor costs and calculations."""

    def __init__(self, labor_data: Dict[str, Any], materials_manager: MaterialManager):
        """Initialize the labor manager.

        Args:
            labor_data: Labor cost configuration data
        """
        self.labor_data = labor_data
        self.materials_manager = materials_manager
        self.hourly_rate = self.labor_data['labor_rate']
        self.markup_percentage = self.labor_data['markup_percentage']

    def get_carcass_hours(
            self,
            material: str,
            shelves: int = 0
    ) -> float:
        """Get labor hours for a carcass.

        Args:
            material: Carcass material
            shelves: Number of shelves

        Returns:
            Labor hours required
        """
        material_type = self.materials_manager.get_material_type(material)
        base_hours = self.labor_data.get('Carcass', {}).get(
            material_type, 0.0
        )

        # Add time for shelves (estimated)
        shelf_hours = shelves * 0.25

        return base_hours + shelf_hours

    def get_drawer_hours(self, material: str) -> float:
        """Get labor hours for a drawer.

        Args:
            material: Drawer material

        Returns:
            Labor hours required
        """
        material_type = self.materials_manager.get_material_type(material)
        return self.labor_data.get('Drawers', {}).get(
            material_type, 0.0
        )

    def get_door_hours(
            self,
            material: str,
            door_type: str,
            has_moulding: bool = False,
            has_cut_handle: bool = False,
            sprayed: bool = False
    ) -> float:
        """Get labor hours for a door.

        Args:
            material: Door material
            door_type: Type of door (Shaker, Flat)
            has_moulding: Whether door has moulding
            has_cut_handle: Whether door has cut handle

        Returns:
            Labor hours per door
        """
        material_type = self.materials_manager.get_material_type(material)

        # Sprayed MDF hack
        if sprayed and self.materials_manager.sprayable(material):
            material_type = f"Sprayed {material_type}"

        # Find matching door configuration
        for door_config in self.labor_data.get('Doors', []):
            if (door_config.get('Material') == material_type and
                    door_config.get('Type') == door_type):

                hours = door_config.get('Per Door (hours)', 0.0)

                if has_moulding:
                    hours += door_config.get('Moulding', 0.0)

                if has_cut_handle:
                    hours += door_config.get('Cut Handle', 0.0)

                return hours

        logger.warning(
            f"No labor data found for {material_type} {door_type} door"
        )
        return 0.0

    def get_face_frame_hours(
            self,
            material: str,
            has_moulding: bool = False
    ) -> float:
        """Get labor hours for a face frame.

        Args:
            material: Face frame material
            has_moulding: Whether frame has moulding

        Returns:
            Labor hours required
        """
        material_type = self.materials_manager.get_material_type(material)
        face_frame_data = self.labor_data.get('Face Frames', {}).get(
            material_type, {}
        )

        hours = face_frame_data.get('Per Frame (hours)', 0.0)

        if has_moulding:
            hours += face_frame_data.get('Moulding', 0.0)

        return hours

    def calculate_labor_cost(self, hours: float) -> float:
        """Calculate labor cost from hours.

        Args:
            hours: Number of labor hours

        Returns:
            Labor cost in currency
        """
        return hours * self.hourly_rate

    def calculate_markup(self, subtotal: float) -> float:
        """Calculate markup amount.

        Args:
            subtotal: Subtotal before markup

        Returns:
            Markup amount
        """
        return subtotal * (self.markup_percentage / 100)

    def set_hourly_rate(self, rate: float) -> None:
        """Set the hourly labor rate.

        Args:
            rate: New hourly rate

        Raises:
            ValueError: If rate is negative
        """
        if rate < 0:
            raise ValueError("Hourly rate cannot be negative")

        self.hourly_rate = rate
        logger.info(f"Hourly rate set to {rate}")

    def set_markup_percentage(self, percentage: float) -> None:
        """Set the markup percentage.

        Args:
            percentage: New markup percentage

        Raises:
            ValueError: If percentage is negative
        """
        if percentage < 0:
            raise ValueError("Markup percentage cannot be negative")

        self.markup_percentage = percentage
        logger.info(f"Markup percentage set to {percentage}%")
