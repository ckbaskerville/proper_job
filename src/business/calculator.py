"""Quote calculation business logic with grain direction support."""

import logging
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict
from dataclasses import dataclass

from src.models.components import Component
from src.models.project import Cabinet
from src.models.geometry import Rectangle
from src.algorithms.bin_packing_ga import BinPackingGA
from src.algorithms.optimization import SheetOptimizer, OptimizerConfig
from .material_manager import MaterialManager
from .labor_manager import LaborManager
from ..config import SettingsManager

logger = logging.getLogger(__name__)


@dataclass
class MaterialGroup:
    """Groups parts by material and thickness with grain awareness."""
    material: str
    thickness: float
    parts: List[Rectangle]
    has_grain: bool = False

    @property
    def key(self) -> Tuple[str, float]:
        """Get unique key for this material group."""
        return (self.material, self.thickness)

    @property
    def total_area(self) -> float:
        """Calculate total area of all parts."""
        return sum(part.area() for part in self.parts)

    @property
    def grain_statistics(self) -> Dict[str, int]:
        """Get statistics about grain directions in this group."""
        stats = defaultdict(int)
        for part in self.parts:
            stats[part.grain_direction.value] += 1
        return dict(stats)


@dataclass
class QuoteResult:
    """Complete quote calculation results with grain compliance info."""
    units_count: int
    total_sheets: int
    sheets_breakdown: Dict[Tuple[str, float], Dict]
    material_cost: float
    runner_cost: float
    hinge_cost: float
    labor_hours: float
    labor_cost: float
    subtotal: float
    markup: float
    total: float
    materials_used: List[Tuple[str, float]]
    grain_compliance: Dict[Tuple[str, float], bool] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        result = {
            'units': self.units_count,
            'total_sheets_required': self.total_sheets,
            'sheets_breakdown': self.sheets_breakdown,
            'material_cost': self.material_cost,
            'runner_cost': self.runner_cost,
            'hinge_cost': self.hinge_cost,
            'labor_hours': self.labor_hours,
            'labor_cost': self.labor_cost,
            'subtotal': self.subtotal,
            'markup': self.markup,
            'total': self.total,
            'materials_used': self.materials_used
        }

        if self.grain_compliance:
            result['grain_compliance'] = {
                f"{mat}_{thick}mm": compliant
                for (mat, thick), compliant in self.grain_compliance.items()
            }

        return result

@dataclass
class ComponentBreakdown:
    """Detailed breakdown for a single component."""
    component_name: str
    material: str
    thickness: float
    dimensions: str
    parts_count: int
    total_area: float
    material_cost: float
    labor_hours: float
    labor_cost: float
    total_cost: float
    notes: str = ""


@dataclass
class UnitBreakdown:
    """Complete breakdown for a cabinet unit."""
    unit_name: str
    unit_index: int
    quantity: int
    components: List[ComponentBreakdown]

    @property
    def unit_material_cost(self) -> float:
        """Total material cost for one unit."""
        return sum(comp.material_cost for comp in self.components)

    @property
    def unit_labor_hours(self) -> float:
        """Total labor hours for one unit."""
        return sum(comp.labor_hours for comp in self.components)

    @property
    def unit_labor_cost(self) -> float:
        """Total labor cost for one unit."""
        return sum(comp.labor_cost for comp in self.components)

    @property
    def unit_subtotal(self) -> float:
        """Subtotal for one unit."""
        return self.unit_material_cost + self.unit_labor_cost

    @property
    def total_with_quantity(self) -> float:
        """Total cost including quantity."""
        return self.unit_subtotal * self.quantity

class QuoteCalculator:
    """Main business logic for quote calculation with grain direction support."""

    def __init__(
            self,
            material_manager: MaterialManager,
            labor_manager: LaborManager,
            sheet_width: float = 2440,
            sheet_height: float = 1220
    ):
        """Initialize the quote calculator.

        Args:
            material_manager: Manager for material pricing and grain info
            labor_manager: Manager for labor costs
            sheet_width: Standard sheet width in mm
            sheet_height: Standard sheet height in mm
        """
        self.material_manager = material_manager
        self.labor_manager = labor_manager
        self.sheet_width = sheet_width
        self.sheet_height = sheet_height
        self.units: List[Cabinet] = []

        # Caches for optimization results
        self._optimizers: Dict[Tuple[str, float], SheetOptimizer] = {}
        self._solutions: Dict[Tuple[str, float], object] = {}
        self._sheets_by_material: Dict[Tuple[str, float], List] = {}
        self._grain_compliance: Dict[Tuple[str, float], bool] = {}

        logger.info(
            f"QuoteCalculator initialized with sheet size: "
            f"{sheet_width}x{sheet_height}mm"
        )

    def add_unit(self, unit: Cabinet) -> None:
        """Add a cabinet unit to the quote."""
        self.units.append(unit)
        self._clear_caches()
        logger.info(f"Added unit: {unit.carcass.name}")

    def remove_unit(self, index: int) -> None:
        """Remove a cabinet unit by index."""
        if 0 <= index < len(self.units):
            removed = self.units.pop(index)
            self._clear_caches()
            logger.info(f"Removed unit: {removed.carcass.name}")
        else:
            raise IndexError(f"Invalid unit index: {index}")

    def _clear_caches(self) -> None:
        """Clear optimization caches when units change."""
        self._optimizers.clear()
        self._solutions.clear()
        self._sheets_by_material.clear()
        self._grain_compliance.clear()

    def _group_parts_by_material(self) -> Dict[Tuple[str, float], MaterialGroup]:
        """Group all parts by material type and thickness with grain awareness."""
        groups = defaultdict(list)

        for unit in self.units:
            # Process each component type
            self._add_component_parts(
                unit.carcass,
                unit.quantity,
                groups
            )

            for drawer in unit.drawers:
                self._add_component_parts(
                    drawer,
                    unit.quantity,
                    groups
                )

            if unit.doors and unit.doors.quantity > 0:
                self._add_component_parts(
                    unit.doors,
                    unit.quantity,
                    groups
                )

            if unit.face_frame and unit.face_frame.material:
                self._add_component_parts(
                    unit.face_frame,
                    unit.quantity,
                    groups,
                    material_override=unit.face_frame.material,
                    thickness_override=unit.face_frame.thickness
                )

        # Convert to MaterialGroup objects with grain information
        result = {}
        for (material, thickness), parts in groups.items():
            has_grain = self.material_manager.has_grain_direction(material)
            result[(material, thickness)] = MaterialGroup(
                material=material,
                thickness=thickness,
                parts=parts,
                has_grain=has_grain
            )

        return result

    def _add_component_parts(
            self,
            component: Component,
            quantity: int,
            groups: Dict,
            material_override: Optional[str] = None,
            thickness_override: Optional[float] = None
    ) -> None:
        """Add component parts to material groups."""
        parts = component.get_parts()

        # Determine material and thickness
        if hasattr(component, 'material'):
            material = material_override or component.material
        else:
            material = material_override

        if hasattr(component, 'material_thickness'):
            thickness = thickness_override or component.material_thickness
        elif hasattr(component, 'thickness'):
            thickness = thickness_override or component.thickness
        else:
            thickness = thickness_override

        if material and thickness:
            key = (material, thickness)
            for _ in range(quantity):
                groups[key].extend(parts)

    def _optimize_material_usage(
            self,
            material_groups: Dict[Tuple[str, float], MaterialGroup]
    ) -> Dict[Tuple[str, float], Dict]:
        """Optimize sheet usage for each material group with grain awareness."""
        optimization_results = {}

        for key, group in material_groups.items():
            if not group.parts:
                continue

            material, thickness = key
            logger.info(
                f"Optimizing {len(group.parts)} parts for "
                f"{material} {thickness}mm (grain: {group.has_grain})"
            )

            # Log grain statistics for this group
            if group.has_grain:
                grain_stats = group.grain_statistics
                logger.info(f"Grain distribution: {grain_stats}")

            # Create optimizer configuration based on material properties
            config = OptimizerConfig(
                sheet_width=self.sheet_width,
                sheet_height=self.sheet_height,
                material_type=material,
                allow_rotation=not group.has_grain  # Disable rotation for grain materials
            )

            # Create or get cached optimizer
            if key not in self._optimizers:
                self._optimizers[key] = SheetOptimizer(group.parts, config)

            optimizer = self._optimizers[key]

            # Run optimization
            best_solution, sheets = optimizer.optimize()

            # Validate grain compliance
            grain_compliant = True
            if group.has_grain:
                is_compliant, violations = optimizer.packer.validate_grain_compliance(sheets)
                grain_compliant = is_compliant
                if violations:
                    logger.warning(f"Grain violations for {material}: {violations}")

            # Store results
            self._solutions[key] = best_solution
            self._sheets_by_material[key] = sheets
            self._grain_compliance[key] = grain_compliant

            # Calculate efficiency
            sheet_area = self.sheet_width * self.sheet_height
            total_sheet_area = len(sheets) * sheet_area
            efficiency = group.total_area / total_sheet_area if total_sheet_area > 0 else 0

            optimization_results[key] = {
                'sheets_required': len(sheets),
                'sheet_price': self.material_manager.get_sheet_price(
                    material, thickness
                ),
                'material_cost': self._calculate_material_cost(
                    len(sheets), material, thickness
                ),
                'sheets_detail': sheets,
                'parts_count': len(group.parts),
                'efficiency': efficiency,
                'total_area': group.total_area,
                'has_grain': group.has_grain,
                'grain_compliant': grain_compliant,
                'grain_statistics': group.grain_statistics
            }

            status = "✓ grain compliant" if grain_compliant else "✗ grain violations"
            logger.info(
                f"Optimization complete: {len(sheets)} sheets, "
                f"{efficiency:.1%} efficiency, {status if group.has_grain else 'no grain constraints'}"
            )

        return optimization_results

    def _calculate_material_cost(
            self,
            num_sheets: int,
            material: str,
            thickness: float
    ) -> float:
        """Calculate material cost including waste factor.

        Args:
            num_sheets: Number of sheets required
            material: Material type
            thickness: Material thickness in mm

        Returns:
            Total material cost including waste
        """
        WASTE_FACTOR = 1.1  # 10% waste allowance
        sheet_price = self.material_manager.get_sheet_price(material, thickness)
        return num_sheets * sheet_price * WASTE_FACTOR

    def calculate_quote(self) -> QuoteResult:
        """Calculate complete quote for all units with grain compliance.

        Returns:
            QuoteResult with all cost breakdowns and grain compliance info
        """
        if not self.units:
            logger.warning("No units to quote")
            return self._empty_quote()

        # Validate material combinations
        all_materials = []
        for unit in self.units:
            all_materials.append(unit.carcass.material)
            for drawer in unit.drawers:
                all_materials.append(drawer.material)
            if unit.doors:
                all_materials.append(unit.doors.material)
            if unit.face_frame:
                all_materials.append(unit.face_frame.material)

        is_valid, warnings = self.material_manager.validate_material_combination(
            list(set(all_materials))
        )
        if warnings:
            for warning in warnings:
                logger.warning(warning)

        # Group and optimize materials
        material_groups = self._group_parts_by_material()
        optimization_results = self._optimize_material_usage(material_groups)

        # Calculate costs
        total_material_cost = sum(
            result['material_cost']
            for result in optimization_results.values()
        )

        total_sheets = sum(
            result['sheets_required']
            for result in optimization_results.values()
        )

        # Calculate runner costs
        runner_cost = self._calculate_runner_costs()
        total_material_cost += runner_cost

        hinge_cost = self._calculate_hinge_cost()
        total_material_cost += hinge_cost

        # Calculate labor
        labor_hours = self._calculate_total_labor_hours()
        labor_cost = labor_hours * self.labor_manager.hourly_rate

        # Calculate totals
        subtotal = total_material_cost + labor_cost
        markup = subtotal * (self.labor_manager.markup_percentage / 100)
        total = subtotal + markup

        return QuoteResult(
            units_count=len(self.units),
            total_sheets=total_sheets,
            sheets_breakdown=optimization_results,
            material_cost=total_material_cost,
            runner_cost=runner_cost,
            labor_hours=labor_hours,
            labor_cost=labor_cost,
            subtotal=subtotal,
            markup=markup,
            total=total,
            materials_used=list(material_groups.keys()),
            hinge_cost=hinge_cost,
            grain_compliance=self._grain_compliance.copy()
        )

    def _empty_quote(self) -> QuoteResult:
        """Return empty quote result."""
        return QuoteResult(
            units_count=0,
            total_sheets=0,
            sheets_breakdown={},
            material_cost=0.0,
            runner_cost=0.0,
            labor_hours=0.0,
            labor_cost=0.0,
            subtotal=0.0,
            markup=0.0,
            total=0.0,
            materials_used=[],
            hinge_cost=0.0,
            grain_compliance={}
        )

    def _calculate_runner_costs(self) -> float:
        """Calculate total cost for all drawer runners."""
        total_cost = 0.0

        for unit in self.units:
            for drawer in unit.drawers:
                total_cost += drawer.get_total_runner_cost() * unit.quantity

        return total_cost

    def _calculate_hinge_cost(self) -> float:
        total_cost = 0.0
        for unit in self.units:
            if unit.doors:
                total_cost += unit.doors.hinge_price * unit.doors.hinges_per_door * unit.quantity

        return total_cost

    def _calculate_total_labor_hours(self) -> float:
        """Calculate total labor hours for all units."""
        total_hours = 0.0

        for unit in self.units:
            unit_hours = self._calculate_unit_labor_hours(unit)
            total_hours += unit_hours * unit.quantity

        return total_hours

    def _calculate_unit_labor_hours(self, unit: Cabinet) -> float:
        """Calculate labor hours for a single unit."""
        hours = 0.0

        # Carcass labor
        hours += self.labor_manager.get_carcass_hours(
            unit.carcass.material,
            unit.carcass.shelves
        )

        # Drawer labor
        for drawer in unit.drawers:
            hours += self.labor_manager.get_drawer_hours(drawer.material)

        # Door labor
        if unit.doors and unit.doors.quantity > 0:
            door_hours = self.labor_manager.get_door_hours(
                unit.doors.material,
                unit.doors.door_type,
                unit.doors.moulding,
                unit.doors.cut_handle,
                unit.doors.sprayed
            )
            hours += door_hours * unit.doors.quantity

        # Face frame labor
        if unit.face_frame and unit.face_frame.material:
            hours += self.labor_manager.get_face_frame_hours(
                unit.face_frame.material,
                unit.face_frame.moulding
            )

        return hours

    def get_grain_compliance_report(self) -> Dict[str, Any]:
        """Get detailed report on grain direction compliance.

        Returns:
            Dictionary with grain compliance information
        """
        report = {
            'total_materials': 0,
            'grain_materials': 0,
            'compliant_materials': 0,
            'non_compliant_materials': 0,
            'details': []
        }

        material_groups = self._group_parts_by_material()

        for (material, thickness), group in material_groups.items():
            material_info = {
                'material': material,
                'thickness': thickness,
                'has_grain': group.has_grain,
                'parts_count': len(group.parts),
                'grain_statistics': group.grain_statistics,
                'compliant': self._grain_compliance.get((material, thickness), True)
            }

            report['details'].append(material_info)
            report['total_materials'] += 1

            if group.has_grain:
                report['grain_materials'] += 1
                if material_info['compliant']:
                    report['compliant_materials'] += 1
                else:
                    report['non_compliant_materials'] += 1

        return report

    def get_optimization_summary(self) -> Dict[str, Any]:
        """Get summary of optimization results including grain information.

        Returns:
            Dictionary with optimization summary
        """
        material_groups = self._group_parts_by_material()

        summary = {
            'total_materials': len(material_groups),
            'materials_with_grain': 0,
            'materials_without_grain': 0,
            'total_parts': 0,
            'grain_constrained_parts': 0,
            'rotation_disabled_materials': [],
            'rotation_enabled_materials': [],
            'efficiency_by_material': {}
        }

        for (material, thickness), group in material_groups.items():
            key = f"{material}_{thickness}mm"

            if group.has_grain:
                summary['materials_with_grain'] += 1
                summary['rotation_disabled_materials'].append(key)
                summary['grain_constrained_parts'] += len(group.parts)
            else:
                summary['materials_without_grain'] += 1
                summary['rotation_enabled_materials'].append(key)

            summary['total_parts'] += len(group.parts)

            # Get efficiency if optimization has run
            if hasattr(self, '_sheets_by_material') and (material, thickness) in self._sheets_by_material:
                sheets = self._sheets_by_material[(material, thickness)]
                if sheets:
                    sheet_area = self.sheet_width * self.sheet_height
                    total_sheet_area = len(sheets) * sheet_area
                    efficiency = group.total_area / total_sheet_area if total_sheet_area > 0 else 0
                    summary['efficiency_by_material'][key] = efficiency

        return summary