"""Quote calculation business logic."""

import logging
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from dataclasses import dataclass

from src.models.components import Component
from src.models.project import Cabinet
from src.models.geometry import Rectangle
from src.algorithms.bin_packing_ga import BinPackingGA
from .material_manager import MaterialManager
from .labor_manager import LaborManager
from ..config import SettingsManager

logger = logging.getLogger(__name__)


@dataclass
class MaterialGroup:
    """Groups parts by material and thickness."""
    material: str
    thickness: float
    parts: List[Rectangle]

    @property
    def key(self) -> Tuple[str, float]:
        """Get unique key for this material group."""
        return (self.material, self.thickness)

    @property
    def total_area(self) -> float:
        """Calculate total area of all parts."""
        return sum(part.area() for part in self.parts)


@dataclass
class QuoteResult:
    """Complete quote calculation results."""
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

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
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
    """Main business logic for quote calculation."""

    def __init__(
            self,
            material_manager: MaterialManager,
            labor_manager: LaborManager,
            sheet_width: float = 2440,
            sheet_height: float = 1220
    ):
        """Initialize the quote calculator.

        Args:
            material_manager: Manager for material pricing
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
        self._optimizers: Dict[Tuple[str, float], BinPackingGA] = {}
        self._solutions: Dict[Tuple[str, float], object] = {}
        self._sheets_by_material: Dict[Tuple[str, float], List] = {}

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

    def _group_parts_by_material(self) -> Dict[Tuple[str, float], MaterialGroup]:
        """Group all parts by material type and thickness."""
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

        # Convert to MaterialGroup objects
        result = {}
        for (material, thickness), parts in groups.items():
            result[(material, thickness)] = MaterialGroup(
                material=material,
                thickness=thickness,
                parts=parts
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
        """Optimize sheet usage for each material group."""
        optimization_results = {}

        for key, group in material_groups.items():
            if not group.parts:
                continue

            logger.info(
                f"Optimizing {len(group.parts)} parts for "
                f"{group.material} {group.thickness}mm"
            )

            # Create optimizer if not cached
            if key not in self._optimizers:
                self._optimizers[key] = BinPackingGA(
                    self.sheet_width,
                    self.sheet_height
                )

            optimizer = self._optimizers[key]

            # Run optimization
            solution = optimizer.evolve(group.parts)
            sheets = optimizer.get_detailed_solution(
                group.parts,
                solution.genes
            )

            # Cache results
            self._solutions[key] = solution
            self._sheets_by_material[key] = sheets

            # Calculate efficiency
            sheet_area = self.sheet_width * self.sheet_height
            total_sheet_area = len(sheets) * sheet_area
            efficiency = group.total_area / total_sheet_area if total_sheet_area > 0 else 0

            optimization_results[key] = {
                'sheets_required': len(sheets),
                'sheet_price': self.material_manager.get_sheet_price(
                    group.material,
                    group.thickness
                ),
                'material_cost': self._calculate_material_cost(
                    len(sheets),
                    group.material,
                    group.thickness
                ),
                'sheets_detail': sheets,
                'parts_count': len(group.parts),
                'efficiency': efficiency,
                'total_area': group.total_area
            }

            logger.info(
                f"Optimization complete: {len(sheets)} sheets, "
                f"{efficiency:.1%} efficiency"
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
        """Calculate complete quote for all units.

        Returns:
            QuoteResult with all cost breakdowns
        """
        if not self.units:
            logger.warning("No units to quote")
            return self._empty_quote()

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
            hinge_cost=hinge_cost
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
            hinge_cost=0.0
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
                unit.doors.cut_handle
            )
            hours += door_hours * unit.doors.quantity

        # Face frame labor
        if unit.face_frame and unit.face_frame.material:
            hours += self.labor_manager.get_face_frame_hours(
                unit.face_frame.material,
                unit.face_frame.moulding
            )

        return hours

    def calculate_unit_breakdown(self) -> List[UnitBreakdown]:
        """Calculate detailed breakdown for each unit.

        Returns:
            List of UnitBreakdown objects with component details
        """
        # First optimize to get efficiency data
        material_groups = self._group_parts_by_material()
        optimization_results = self._optimize_material_usage(material_groups)

        breakdowns = []

        for unit_idx, unit in enumerate(self.units):
            components = []

            # Carcass breakdown
            carcass_breakdown = self._calculate_carcass_breakdown(
                unit,
                optimization_results
            )
            components.append(carcass_breakdown)

            # Drawer breakdowns
            for drawer_idx, drawer in enumerate(unit.drawers):
                drawer_breakdown = self._calculate_drawer_breakdown(
                    unit,
                    drawer,
                    drawer_idx,
                    optimization_results
                )
                components.append(drawer_breakdown)

            # Door breakdown
            if unit.doors and unit.doors.quantity > 0:
                door_breakdown = self._calculate_door_breakdown(
                    unit,
                    optimization_results
                )
                if door_breakdown:
                    components.append(door_breakdown)

            # Face frame breakdown
            if unit.face_frame and unit.face_frame.material:
                face_frame_breakdown = self._calculate_face_frame_breakdown(
                    unit,
                    optimization_results
                )
                components.append(face_frame_breakdown)

            breakdowns.append(UnitBreakdown(
                unit_name=unit.carcass.name,
                unit_index=unit_idx,
                quantity=unit.quantity,
                components=components
            ))

        return breakdowns

    def _calculate_component_material_cost(
            self,
            component: Component,
            material: str,
            thickness: float,
            optimization_results: Dict
    ) -> float:
        """Calculate material cost for a single component."""
        key = (material, thickness)
        if key not in optimization_results:
            return 0.0

        efficiency = optimization_results[key]['efficiency']
        sheet_price = self.material_manager.get_sheet_price(material, thickness)
        sheet_area = self.sheet_width * self.sheet_height
        component_area = component.get_total_area()

        # Cost = (component area / sheet area) * sheet price / efficiency
        cost = (component_area / sheet_area) * sheet_price / efficiency
        return cost * 1.1  # 10% waste factor

    def _calculate_carcass_breakdown(
            self,
            unit: Cabinet,
            optimization_results: Dict
    ) -> ComponentBreakdown:
        """Calculate breakdown for carcass component."""
        carcass = unit.carcass
        material_cost = self._calculate_component_material_cost(
            carcass,
            carcass.material,
            carcass.material_thickness,
            optimization_results
        )

        labor_hours = self.labor_manager.get_carcass_hours(
            carcass.material,
            carcass.shelves
        )
        labor_cost = labor_hours * self.labor_manager.hourly_rate

        notes = f"Includes {carcass.shelves} shelves" if carcass.shelves > 0 else ""

        return ComponentBreakdown(
            component_name="Carcass",
            material=carcass.material,
            thickness=carcass.material_thickness,
            dimensions=f"{carcass.height} × {carcass.width} × {carcass.depth}",
            parts_count=len(carcass.get_parts()),
            total_area=carcass.get_total_area(),
            material_cost=material_cost,
            labor_hours=labor_hours,
            labor_cost=labor_cost,
            total_cost=material_cost + labor_cost,
            notes=notes
        )

    def _calculate_drawer_breakdown(
            self,
            unit: Cabinet,
            drawer: 'Drawer',
            drawer_idx: int,
            optimization_results: Dict
    ) -> ComponentBreakdown:
        """Calculate breakdown for drawer component."""
        material_cost = self._calculate_component_material_cost(
            drawer,
            drawer.material,
            drawer.thickness,
            optimization_results
        )

        # Add runner cost
        runner_cost = drawer.get_total_runner_cost()
        material_cost += runner_cost

        labor_hours = self.labor_manager.get_drawer_hours(drawer.material)
        labor_cost = labor_hours * self.labor_manager.hourly_rate

        drawer_depth, drawer_width = drawer.calculate_drawer_dimensions()

        notes = (
            f"Runners: {drawer.runner_model} {drawer.runner_size}mm, "
            f"{drawer.runner_capacity}kg (£{runner_cost:.2f})"
        )

        return ComponentBreakdown(
            component_name=f"Drawer {drawer_idx + 1}",
            material=drawer.material,
            thickness=drawer.thickness,
            dimensions=f"{drawer.height} × {drawer_width:.0f} × {drawer_depth:.0f}",
            parts_count=len(drawer.get_parts()),
            total_area=drawer.get_total_area(),
            material_cost=material_cost,
            labor_hours=labor_hours,
            labor_cost=labor_cost,
            total_cost=material_cost + labor_cost,
            notes=notes
        )

    def _calculate_door_breakdown(
            self,
            unit: Cabinet,
            optimization_results: Dict
    ) -> Optional[ComponentBreakdown]:
        """Calculate breakdown for door component."""
        doors = unit.doors
        door_parts = doors.get_parts()

        if not door_parts:
            return None

        material_cost = self._calculate_component_material_cost(
            doors,
            doors.material,
            doors.material_thickness,
            optimization_results
        )

        door_labor_hours = self.labor_manager.get_door_hours(
            doors.material,
            doors.door_type,
            doors.moulding,
            doors.cut_handle
        )
        total_labor_hours = door_labor_hours * doors.quantity
        labor_cost = total_labor_hours * self.labor_manager.hourly_rate

        notes_parts = []
        if doors.moulding:
            notes_parts.append("with moulding")
        if doors.cut_handle:
            notes_parts.append("with handle cutout")

        notes = f"{doors.quantity} doors"
        if notes_parts:
            notes += f" {', '.join(notes_parts)}"

        return ComponentBreakdown(
            component_name="Doors",
            material=doors.material,
            thickness=doors.material_thickness,
            dimensions=f"{doors.door_type} style, {doors.position}",
            parts_count=len(door_parts),
            total_area=doors.get_total_area(),
            material_cost=material_cost,
            labor_hours=total_labor_hours,
            labor_cost=labor_cost,
            total_cost=material_cost + labor_cost,
            notes=notes
        )

    def _calculate_face_frame_breakdown(
            self,
            unit: Cabinet,
            optimization_results: Dict
    ) -> ComponentBreakdown:
        """Calculate breakdown for face frame component."""
        face_frame = unit.face_frame

        # Face frames typically use same material as carcass
        material = unit.carcass.material
        thickness = face_frame.thickness

        material_cost = self._calculate_component_material_cost(
            face_frame,
            material,
            thickness,
            optimization_results
        )

        labor_hours = self.labor_manager.get_face_frame_hours(
            face_frame.material,
            face_frame.moulding
        )
        labor_cost = labor_hours * self.labor_manager.hourly_rate

        notes = "with moulding" if face_frame.moulding else ""

        return ComponentBreakdown(
            component_name="Face Frame",
            material=face_frame.material,
            thickness=thickness,
            dimensions=f"{unit.carcass.height} × {unit.carcass.width}",
            parts_count=len(face_frame.get_parts()),
            total_area=face_frame.get_total_area(),
            material_cost=material_cost,
            labor_hours=labor_hours,
            labor_cost=labor_cost,
            total_cost=material_cost + labor_cost,
            notes=notes
        )
