"""Material pricing and management with grain direction support."""

import logging
from typing import Dict, List, Tuple, Optional, Any

from src.config.constants import WASTE_FACTOR
from src.models.geometry import GrainDirection

logger = logging.getLogger(__name__)


class MaterialManager:
    """Manages material configurations and pricing with grain direction awareness."""

    def __init__(self, materials_data: Dict[str, Any]):
        """Initialize the material manager.

        Args:
            materials_data: Material configuration data
        """
        self.materials_data = materials_data
        self._price_cache: Dict[Tuple[str, float], float] = {}
        self._grain_cache: Dict[str, bool] = {}
        self._build_caches()

    def _build_caches(self) -> None:
        """Build the price and grain lookup caches."""
        vat_rate = self.materials_data.get('VAT', 0.2)

        for material in self.materials_data.get('Materials', []):
            material_name = material['Material']

            # Cache grain information
            self._grain_cache[material_name] = self._material_has_grain(material_name)

            # Build price cache
            for thickness_data in material.get('Cost', []):
                thickness = thickness_data['Thickness']
                base_cost = thickness_data['Sheet Cost (exc. VAT)']

                # Calculate price including VAT
                price_with_vat = base_cost * (1 + vat_rate)
                self._price_cache[(material_name, thickness)] = price_with_vat

        logger.info(f"Built price cache with {len(self._price_cache)} entries")
        logger.info(f"Built grain cache with {len(self._grain_cache)} entries")

    def _material_has_grain(self, material_name: str) -> bool:
        """Check if a material has grain direction constraints.

        Args:
            material_name: Name of the material

        Returns:
            True if material has grain constraints
        """
        grain_materials = {"veneer", "hardwood", "laminate", "plywood"}
        material_lower = material_name.lower()
        return any(grain_mat in material_lower for grain_mat in grain_materials)

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

    def has_grain_direction(self, material: str) -> bool:
        """Check if a material has grain direction constraints.

        Args:
            material: Material name

        Returns:
            True if material has grain direction constraints
        """
        return self._grain_cache.get(material, False)

    def requires_grain_optimization(self, material: str) -> bool:
        """Check if a material requires grain-aware optimization.

        Args:
            material: Material name

        Returns:
            True if optimization should consider grain direction
        """
        return self.has_grain_direction(material)

    def get_grain_direction_for_material(self, material: str) -> GrainDirection:
        """Get the default grain direction for a material.

        Args:
            material: Material name

        Returns:
            Default grain direction for the material
        """
        if self.has_grain_direction(material):
            return GrainDirection.WITH_WIDTH  # Standard grain direction
        return GrainDirection.NONE

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

    def get_materials_by_grain_type(self, has_grain: bool) -> List[str]:
        """Get materials filtered by grain requirements.

        Args:
            has_grain: True to get materials with grain, False for materials without

        Returns:
            List of material names matching grain requirement
        """
        materials = []

        for material_name in self._grain_cache:
            if self._grain_cache[material_name] == has_grain:
                materials.append(material_name)

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

    def sprayable(self, material: str) -> bool:
        """Check if a material is sprayable."""
        for mat in self.materials_data.get('Materials', []):
            if mat['Material'] == material:
                return mat.get('Sprayable', False)
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

    def get_material_type(self, material: str, sprayed: bool = False) -> str:
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
        else:
            if sprayed:
                return "Sprayed"
            return material

    def get_optimization_config(self, material: str) -> Dict[str, Any]:
        """Get optimization configuration for a material.

        Args:
            material: Material name

        Returns:
            Dictionary with optimization settings
        """
        has_grain = self.has_grain_direction(material)

        return {
            'has_grain': has_grain,
            'allow_rotation': not has_grain,
            'grain_direction': self.get_grain_direction_for_material(material),
            'material_type': self.get_material_type(material),
            'requires_grain_optimization': self.requires_grain_optimization(material)
        }

    def validate_material_combination(
        self,
        materials: List[str]
    ) -> Tuple[bool, List[str]]:
        """Validate that materials in a combination are compatible for optimization.

        Args:
            materials: List of material names used in the same optimization

        Returns:
            Tuple of (is_valid, list_of_warnings)
        """
        warnings = []

        grain_materials = [mat for mat in materials if self.has_grain_direction(mat)]
        non_grain_materials = [mat for mat in materials if not self.has_grain_direction(mat)]

        if grain_materials and non_grain_materials:
            warnings.append(
                f"Mixing grain materials ({grain_materials}) with non-grain materials "
                f"({non_grain_materials}) in the same optimization may lead to "
                f"suboptimal results."
            )

        # Check for different grain requirements within grain materials
        if len(grain_materials) > 1:
            # For now, assume all grain materials have the same requirements
            # This could be expanded for materials with different grain directions
            pass

        return len(warnings) == 0, warnings