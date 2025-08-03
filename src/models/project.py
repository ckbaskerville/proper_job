"""Updated Cabinet model in src/models/project.py - partial update."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from pathlib import Path

from .base import ValidationError
from .components import Carcass, Drawer, Doors, FaceFrame, DBCDrawer
from .geometry import Rectangle
from src.config import MAX_DRAWERS


@dataclass
class Cabinet:
    """Complete cabinet unit with all components.

    Attributes:
        carcass: Main cabinet body
        drawers: List of custom drawer components
        dbc_drawers: List of pre-made DBC drawer components
        quantity: Number of identical units
        doors: Door component (if any)
        face_frame: Face frame component (if any)
        hardware: Dictionary of hardware specifications
        notes: Additional notes about the cabinet
    """
    carcass: Carcass
    drawers: List[Drawer] = field(default_factory=list)
    dbc_drawers: List[DBCDrawer] = field(default_factory=list)  # New field for DBC drawers
    quantity: int = 1
    doors: Optional[Doors] = None
    face_frame: Optional[FaceFrame] = None
    hardware: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    def __post_init__(self):
        """Validate cabinet after creation."""
        self.validate()

    def validate(self) -> None:
        """Validate cabinet configuration."""
        if self.quantity <= 0:
            raise ValidationError("Cabinet quantity must be positive")

        if self.quantity > 100:
            raise ValidationError("Cabinet quantity cannot exceed 100")

        # Validate total drawer count (custom + DBC)
        total_drawers = len(self.drawers) + len(self.dbc_drawers)
        if total_drawers > MAX_DRAWERS:
            raise ValidationError(
                f"Total number of drawers (custom + DBC) cannot exceed {MAX_DRAWERS}"
            )

        # Validate drawer fit
        if self.drawers or self.dbc_drawers:
            # Calculate total height for custom drawers
            custom_drawer_height = sum(d.height for d in self.drawers)
            # Calculate total height for DBC drawers
            dbc_drawer_height = sum(d.height for d in self.dbc_drawers)
            total_drawer_height = custom_drawer_height + dbc_drawer_height

            # Add clearances between drawers (minimum 50mm)
            total_clearance = (total_drawers + 1) * 50
            available_height = self.carcass.internal_dimensions.height

            if total_drawer_height + total_clearance > available_height:
                raise ValidationError(
                    f"Total drawer height ({total_drawer_height}mm) plus "
                    f"clearances exceeds available space ({available_height}mm)"
                )

        # Validate door and drawer combination
        if self.doors and self.doors.quantity > 0 and total_drawers > 0:
            # Check if doors and drawers conflict
            if self.doors.position == "Inset" and total_drawers > 2:
                raise ValidationError(
                    "Inset doors limit drawer count to 2"
                )

    def get_parts(self) -> List[Rectangle]:
        """Get all parts for this cabinet (excludes DBC drawers as they're pre-made)."""
        all_parts = []

        # Carcass parts
        all_parts.extend(self.carcass.get_parts())

        # Custom drawer parts (only)
        for drawer in self.drawers:
            all_parts.extend(drawer.get_parts())

        # DBC drawers don't contribute parts (they're purchased complete)

        # Door parts
        if self.doors:
            all_parts.extend(self.doors.get_parts())

        # Face frame parts
        if self.face_frame:
            all_parts.extend(self.face_frame.get_parts())

        return all_parts

    def get_total_area(self) -> float:
        """Get total material area for one unit (excludes DBC drawers)."""
        return sum(part.area() for part in self.get_parts())

    def get_dbc_drawer_cost(self) -> float:
        """Get total cost of DBC drawers for one unit."""
        return sum(drawer.price for drawer in self.dbc_drawers)

    def get_unit_cost_estimate(
            self,
            material_costs: Dict[str, float],
            labor_rate: float
    ) -> float:
        """Estimate cost for one unit.

        Args:
            material_costs: Dictionary of material costs per sq meter
            labor_rate: Labor cost per hour

        Returns:
            Estimated cost for one unit
        """
        # This is a simplified estimate
        material_area = self.get_total_area() / 1_000_000  # Convert to sq meters

        # Get primary material cost
        primary_material = self.carcass.material
        material_cost = material_area * material_costs.get(primary_material, 50.0)

        # Add hardware costs
        hardware_cost = 0

        # Custom drawer runner costs
        if self.drawers:
            hardware_cost += sum(d.get_total_runner_cost() for d in self.drawers)

        # DBC drawer costs
        if self.dbc_drawers:
            hardware_cost += self.get_dbc_drawer_cost()

        if self.doors and self.doors.quantity > 0:
            # Estimate hinge cost
            hardware_cost += self.doors.quantity * 2 * 5.0  # 2 hinges per door @ £5

        # Estimate labor (very simplified)
        labor_hours = 2.0  # Base assembly time
        if self.drawers:
            labor_hours += len(self.drawers) * 0.5
        if self.dbc_drawers:
            labor_hours += len(self.dbc_drawers) * 0.25  # Less time for pre-made
        if self.doors:
            labor_hours += self.doors.quantity * 0.5
        if self.face_frame:
            labor_hours += 1.0

        labor_cost = labor_hours * labor_rate

        return material_cost + hardware_cost + labor_cost

    @property
    def display_name(self) -> str:
        """Get display name for the cabinet."""
        components = []
        if self.drawers:
            components.append(f"{len(self.drawers)}D")
        if self.dbc_drawers:
            components.append(f"{len(self.dbc_drawers)}DBC")
        if self.doors and self.doors.quantity > 0:
            components.append(f"{self.doors.quantity}Dr")

        comp_str = "+".join(components) if components else "Base"
        return f"{self.carcass.name} ({comp_str})"

    @property
    def dimensions_str(self) -> str:
        """Get formatted dimensions string."""
        return (
            f"{self.carcass.height:.0f} × "
            f"{self.carcass.width:.0f} × "
            f"{self.carcass.depth:.0f}mm"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'carcass': self.carcass.to_dict(),
            'drawers': [d.to_dict() for d in self.drawers],
            'dbc_drawers': [d.to_dict() for d in self.dbc_drawers],  # Include DBC drawers
            'quantity': self.quantity,
            'doors': self.doors.to_dict() if self.doors else None,
            'face_frame': self.face_frame.to_dict() if self.face_frame else None,
            'hardware': self.hardware,
            'notes': self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Cabinet':
        """Create from dictionary."""
        # Recreate carcass first
        carcass = Carcass.from_dict(data['carcass'])

        # Recreate custom drawers with carcass reference
        drawers = [
            Drawer.from_dict(d, carcass)
            for d in data.get('drawers', [])
        ]

        # Recreate DBC drawers
        dbc_drawers = [
            DBCDrawer.from_dict(d)
            for d in data.get('dbc_drawers', [])
        ]

        # Recreate doors and face frame if present
        doors = None
        if data.get('doors'):
            doors = Doors.from_dict(data['doors'], carcass)

        face_frame = None
        if data.get('face_frame'):
            face_frame = FaceFrame.from_dict(data['face_frame'], carcass)

        return cls(
            carcass=carcass,
            drawers=drawers,
            dbc_drawers=dbc_drawers,
            quantity=data.get('quantity', 1),
            doors=doors,
            face_frame=face_frame,
            hardware=data.get('hardware', {}),
            notes=data.get('notes', '')
        )


@dataclass
class ProjectSettings:
    """Project-wide settings and configuration.

    Attributes:
        sheet_width: Standard sheet width in mm
        sheet_height: Standard sheet height in mm
        labor_rate: Labor cost per hour
        markup_percentage: Markup percentage for quotes
        currency_symbol: Currency symbol to use
        company_name: Company name for quotes
        default_material_thickness: Default thickness for new components
    """
    sheet_width: float = 2440
    sheet_height: float = 1220
    labor_rate: float = 40.0
    markup_percentage: float = 20.0
    currency_symbol: str = "£"
    company_name: str = ""
    default_material_thickness: float = 18.0

    def validate(self) -> None:
        """Validate project settings."""
        if self.sheet_width <= 0 or self.sheet_height <= 0:
            raise ValidationError("Sheet dimensions must be positive")

        if self.labor_rate < 0:
            raise ValidationError("Labor rate cannot be negative")

        if self.markup_percentage < 0:
            raise ValidationError("Markup percentage cannot be negative")

        if self.default_material_thickness <= 0:
            raise ValidationError("Default thickness must be positive")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'sheet_width': self.sheet_width,
            'sheet_height': self.sheet_height,
            'labor_rate': self.labor_rate,
            'markup_percentage': self.markup_percentage,
            'currency_symbol': self.currency_symbol,
            'company_name': self.company_name,
            'default_material_thickness': self.default_material_thickness
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectSettings':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class Project:
    """Complete project containing cabinets and settings.

    Attributes:
        name: Project name
        cabinets: List of cabinet units
        settings: Project settings
        created_date: When project was created
        modified_date: When project was last modified
        customer_info: Customer information
        notes: Project notes
        version: Project file version
    """
    name: str
    cabinets: List[Cabinet] = field(default_factory=list)
    settings: ProjectSettings = field(default_factory=ProjectSettings)
    created_date: datetime = field(default_factory=datetime.now)
    modified_date: datetime = field(default_factory=datetime.now)
    customer_info: Dict[str, str] = field(default_factory=dict)
    notes: str = ""
    version: str = "2.0"

    def add_cabinet(self, cabinet: Cabinet) -> None:
        """Add a cabinet to the project."""
        self.cabinets.append(cabinet)
        self.modified_date = datetime.now()

    def remove_cabinet(self, index: int) -> None:
        """Remove a cabinet by index."""
        if 0 <= index < len(self.cabinets):
            self.cabinets.pop(index)
            self.modified_date = datetime.now()
        else:
            raise IndexError(f"Invalid cabinet index: {index}")

    def duplicate_cabinet(self, index: int) -> None:
        """Duplicate a cabinet."""
        if 0 <= index < len(self.cabinets):
            import copy
            cabinet = copy.deepcopy(self.cabinets[index])

            # Update name to avoid duplicates
            base_name = cabinet.carcass.name
            counter = 1
            new_name = f"{base_name} (copy)"

            # Find unique name
            existing_names = {c.carcass.name for c in self.cabinets}
            while new_name in existing_names:
                counter += 1
                new_name = f"{base_name} (copy {counter})"

            cabinet.carcass.name = new_name
            self.cabinets.append(cabinet)
            self.modified_date = datetime.now()
        else:
            raise IndexError(f"Invalid cabinet index: {index}")

    def get_all_parts(self) -> List[Rectangle]:
        """Get all parts from all cabinets."""
        all_parts = []
        for cabinet in self.cabinets:
            for _ in range(cabinet.quantity):
                all_parts.extend(cabinet.get_parts())
        return all_parts

    def get_material_summary(self) -> Dict[str, float]:
        """Get summary of materials used.

        Returns:
            Dictionary mapping material names to total area in sq meters
        """
        from collections import defaultdict
        material_areas = defaultdict(float)

        for cabinet in self.cabinets:
            # Carcass material
            area = cabinet.carcass.get_total_area() / 1_000_000  # to sq meters
            material_areas[cabinet.carcass.material] += area * cabinet.quantity

            # Drawer materials
            for drawer in cabinet.drawers:
                area = drawer.get_total_area() / 1_000_000
                material_areas[drawer.material] += area * cabinet.quantity

            # Door materials
            if cabinet.doors and cabinet.doors.quantity > 0:
                area = cabinet.doors.get_total_area() / 1_000_000
                material_areas[cabinet.doors.material] += area * cabinet.quantity

            # Face frame materials
            if cabinet.face_frame:
                area = cabinet.face_frame.get_total_area() / 1_000_000
                material_areas[cabinet.face_frame.material] += area * cabinet.quantity

        return dict(material_areas)

    def save_to_file(self, filepath: Path) -> None:
        """Save project to JSON file.

        Args:
            filepath: Path to save file
        """
        self.modified_date = datetime.now()

        data = {
            'version': self.version,
            'name': self.name,
            'cabinets': [c.to_dict() for c in self.cabinets],
            'settings': self.settings.to_dict(),
            'created_date': self.created_date.isoformat(),
            'modified_date': self.modified_date.isoformat(),
            'customer_info': self.customer_info,
            'notes': self.notes
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load_from_file(cls, filepath: Path) -> 'Project':
        """Load project from JSON file.

        Args:
            filepath: Path to load from

        Returns:
            Loaded Project instance
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Check version compatibility
        version = data.get('version', '1.0')
        if not version.startswith('2.'):
            raise ValueError(
                f"Incompatible project version: {version}. "
                "This version requires 2.x projects."
            )

        # Create project
        project = cls(
            name=data['name'],
            cabinets=[Cabinet.from_dict(c) for c in data['cabinets']],
            settings=ProjectSettings.from_dict(data['settings']),
            created_date=datetime.fromisoformat(data['created_date']),
            modified_date=datetime.fromisoformat(data['modified_date']),
            customer_info=data.get('customer_info', {}),
            notes=data.get('notes', ''),
            version=version
        )

        return project

    @property
    def total_units(self) -> int:
        """Get total number of units in project."""
        return sum(c.quantity for c in self.cabinets)

    @property
    def unique_cabinets(self) -> int:
        """Get number of unique cabinet designs."""
        return len(self.cabinets)