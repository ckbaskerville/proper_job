"""Material pricing and management."""

import logging
from typing import Dict, List, Tuple, Optional, Any

from src.config.constants import WASTE_FACTOR

logger = logging.getLogger(__name__)


class MaterialManager:
    """Manages material configurations and pricing."""

    def __init__(self, materials_data: Dict[str, Any]):
        """Initialize the material manager.

        Args:
            materials_data: Material configuration data
        """
        self.materials_data = materials_data
        self._price_cache: Dict[Tuple[str, float], float] = {}
        self._build_price_cache()

    def _build_price_cache(self) -> None:
        """Build the price lookup cache."""
        vat_rate = self.materials_data.get('VAT', 0.2)

        for material in self.materials_data.get('Materials', []):
            material_name = material['Material']

            for thickness_data in material.get('Cost', []):
                thickness = thickness_data['Thickness']
                base_cost = thickness_data['Sheet Cost (exc. VAT)']

                # Calculate price including VAT
                price_with_vat = base_cost * (1 + vat_rate)
                self._price_cache[(material_name, thickness)] = price_with_vat

        logger.info(f"Built price cache with {len(self._price_cache)} entries")

    def get_sheet_price(self, material: str, thickness: float) -> float:
        """Get the price for a sheet of material.

        Args:
            material: Material name
            thickness: Material thickness in mm

        Returns:
            Price per sheet including VAT
        """
        price = self._price_cache.get((material, thickness), 0.0)
        if price == 0.0:
            logger.warning(
                f"No price found for {material} {thickness}mm"
            )
        return price

    def get_materials_for_component(self, component_type: str) -> List[str]:
        """Get available materials for a component type.

        Args:
            component_type: Type of component (Carcass, Door, Face Frame)

        Returns:
            List of material names
        """
        materials = []

        for material in self.materials_data.get('Materials', []):
            if material.get(component_type, False):
                materials.append(material['Material'])

        return materials

    def get_available_thicknesses(self, material: str) -> List[float]:
        """Get available thicknesses for a material.

        Args:
            material: Material name

        Returns:
            List of available thicknesses
        """
        for mat in self.materials_data.get('Materials', []):
            if mat['Material'] == material:
                return [
                    cost['Thickness']
                    for cost in mat.get('Cost', [])
                ]
        return []

    def is_veneer(self, material: str) -> bool:
        """Check if a material is veneer."""
        for mat in self.materials_data.get('Materials', []):
            if mat['Material'] == material:
                return mat.get('Veneer', False)
        return False

    def is_hardwood(self, material: str) -> bool:
        """Check if a material is hardwood."""
        for mat in self.materials_data.get('Materials', []):
            if mat['Material'] == material:
                return mat.get('Hardwood', False)
        return False

    def get_additional_costs(self) -> Dict[str, float]:
        """Get additional material costs."""
        return {
            'veneer_lacquer': self.materials_data.get(
                'Veneer Lacquer Cost', 7.5
            ),
            'veneer_edging': self.materials_data.get(
                'Veneer Edging Cost', 4.0
            ),
            'veneer_screw': self.materials_data.get(
                'Veneer Screw Cost', 3.0
            )
        }

    def get_material_type(self, material: str) -> str:
        """Get the type of material (Veneer, Hardwood, etc.).

        Args:
            material: Material name

        Returns:
            Material type
        """
        if self.is_veneer(material):
            return "Veneer"
        elif self.is_hardwood(material):
            return "Hardwood"
        elif material == "Sprayed MDF":
            return "MDF"
        else:
            return material