"""Cabinet component models with grain direction support."""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any
from enum import Enum

from .base import Component, ComponentType, ValidationError, Dimensions
from .geometry import Rectangle, GrainDirection
from src.config.constants import (
    MIN_DIMENSION,
    MAX_DIMENSION,
    MIN_THICKNESS,
    MAX_THICKNESS,
    MAX_SHELVES,
    MAX_DRAWERS,
    DRAWER_RUNNER_CLEARANCE,
    DRAWER_SIDE_CLEARANCE,
    DRAWER_GROOVE_ALLOWANCE,
    DOOR_INSET_HEIGHT_CLEARANCE,
    DEFAULT_FACE_FRAME_THICKNESS,
    DEFAULT_FACE_FRAME_BORDER,
    DEFAULT_FACE_FRAME_BOTTOM_HEIGHT
)


class MaterialType(Enum):
    """Available material types."""
    LAMINATE = "Laminate"
    MDF = "MDF"
    VENEER = "Veneer"
    HARDWOOD = "Hardwood"
    MELAMINE = "Melamine"
    PLYWOOD = "Plywood"


class DoorType(Enum):
    """Available door types."""
    SHAKER = "Shaker"
    FLAT = "Flat"


class DoorPosition(Enum):
    """Door position options."""
    OVERLAY = "Overlay"
    INSET = "Inset"


def get_grain_direction_for_material(material: str) -> GrainDirection:
    """Get the appropriate grain direction constraint for a material.

    Args:
        material: Material name

    Returns:
        Grain direction constraint
    """
    # Materials that have grain direction requirements
    grain_materials = {"veneer", "hardwood", "laminate", "plywood"}

    material_lower = material.lower()
    for grain_mat in grain_materials:
        if grain_mat in material_lower:
            return GrainDirection.WITH_WIDTH  # Default grain runs with width

    # MDF, Melamine, etc. have no grain direction
    return GrainDirection.NONE


@dataclass
class Carcass(Component):
    """Represents the main cabinet body structure.

    Attributes:
        name: Unique name for this carcass
        height: Total height in mm
        width: Total width in mm
        depth: Total depth in mm
        material: Material type
        material_thickness: Thickness of material in mm
        shelves: Number of internal shelves
        has_back: Whether carcass has a back panel
    """
    name: str
    height: float
    width: float
    depth: float
    material: str
    material_thickness: float
    shelves: int = 0
    has_back: bool = True

    def __post_init__(self):
        """Validate carcass after creation."""
        self.validate()

    def validate(self) -> None:
        """Validate carcass specifications."""
        # Validate dimensions
        for value, name in [
            (self.height, "Height"),
            (self.width, "Width"),
            (self.depth, "Depth")
        ]:
            if not MIN_DIMENSION <= value <= MAX_DIMENSION:
                raise ValidationError(
                    f"{name} must be between {MIN_DIMENSION} and "
                    f"{MAX_DIMENSION}mm (got {value}mm)"
                )

        # Validate thickness
        if not MIN_THICKNESS <= self.material_thickness <= MAX_THICKNESS:
            raise ValidationError(
                f"Material thickness must be between {MIN_THICKNESS} and "
                f"{MAX_THICKNESS}mm (got {self.material_thickness}mm)"
            )

        # Validate shelves
        if not 0 <= self.shelves <= MAX_SHELVES:
            raise ValidationError(
                f"Number of shelves must be between 0 and {MAX_SHELVES} "
                f"(got {self.shelves})"
            )

        # Validate name
        if not self.name or not self.name.strip():
            raise ValidationError("Carcass name cannot be empty")

        # Check internal space for shelves
        internal_height = self.height - 2 * self.material_thickness
        if self.shelves > 0:
            space_per_shelf = internal_height / (self.shelves + 1)
            if space_per_shelf < 100:  # Minimum 100mm between shelves
                raise ValidationError(
                    f"Not enough space for {self.shelves} shelves"
                )

    def get_parts(self) -> List[Rectangle]:
        """Generate all rectangular parts for the carcass with grain direction."""
        parts = []
        grain_direction = get_grain_direction_for_material(self.material)

        # Back panel - height should align with sheet width (grain direction)
        if self.has_back:
            parts.append(Rectangle(
                width=self.width,
                height=self.height,
                id=f"{self.name}_back",
                grain_direction=GrainDirection.WITH_HEIGHT,  # Height aligns with sheet width
                component_type="carcass_back"
            ))

        # Side panels - height should align with sheet width (grain direction)
        effective_depth = self.depth - (self.material_thickness if self.has_back else 0)

        for i in range(2):
            parts.append(Rectangle(
                width=effective_depth,
                height=self.height,
                id=f"{self.name}_side_{i+1}",
                grain_direction=GrainDirection.WITH_HEIGHT,  # Height aligns with sheet width
                component_type="carcass_side"
            ))

        # Top and bottom panels - height should align with sheet height
        internal_width = self.width - 2 * self.material_thickness
        for panel_type in ["top", "bottom"]:
            parts.append(Rectangle(
                width=internal_width,
                height=effective_depth,
                id=f"{self.name}_{panel_type}",
                grain_direction=GrainDirection.WITH_WIDTH,  # Height aligns with sheet height
                component_type=f"carcass_{panel_type}"
            ))

        # Shelves - height should align with sheet height
        for i in range(self.shelves):
            parts.append(Rectangle(
                width=internal_width,
                height=effective_depth,
                id=f"{self.name}_shelf_{i+1}",
                grain_direction=GrainDirection.WITH_WIDTH,  # Height aligns with sheet height
                component_type="carcass_shelf"
            ))

        return parts

    def get_total_area(self) -> float:
        """Calculate total material area needed for the carcass."""
        return sum(part.area() for part in self.get_parts())

    @property
    def internal_dimensions(self) -> Dimensions:
        """Get internal dimensions."""
        return Dimensions(
            height=self.height - 2 * self.material_thickness,
            width=self.width - 2 * self.material_thickness,
            depth=self.depth - (self.material_thickness if self.has_back else 0)
        )

    @property
    def component_type(self) -> ComponentType:
        """Get component type."""
        return ComponentType.CARCASS

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'type': self.component_type.value,
            'name': self.name,
            'height': self.height,
            'width': self.width,
            'depth': self.depth,
            'material': self.material,
            'material_thickness': self.material_thickness,
            'shelves': self.shelves,
            'has_back': self.has_back
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Carcass':
        """Create from dictionary."""
        data = data.copy()
        data.pop('type', None)  # Remove type field if present
        return cls(**data)


@dataclass
class Drawer(Component):
    """Represents a drawer component.

    Attributes:
        height: Drawer box height in mm
        thickness: Material thickness in mm
        material: Material type
        runner_model: Brand/model of drawer runners
        runner_size: Length of runners in mm
        runner_capacity: Weight capacity in kg
        carcass: Parent carcass for dimension calculations
        runner_price: Cost per runner
    """
    height: int
    thickness: int
    material: str
    runner_model: str
    runner_size: int
    runner_capacity: int
    carcass: Carcass
    runner_price: float

    def __post_init__(self):
        """Validate drawer after creation."""
        self.validate()

    def validate(self) -> None:
        """Validate drawer specifications."""
        if self.height <= 0 or self.height > 500:
            raise ValidationError(
                f"Drawer height must be between 1 and 500mm "
                f"(got {self.height}mm)"
            )

        if not MIN_THICKNESS <= self.thickness <= MAX_THICKNESS:
            raise ValidationError(
                f"Drawer thickness must be between {MIN_THICKNESS} and "
                f"{MAX_THICKNESS}mm (got {self.thickness}mm)"
            )

        if self.runner_size <= 0:
            raise ValidationError("Runner size must be positive")

        if self.runner_capacity <= 0:
            raise ValidationError("Runner capacity must be positive")

        if self.runner_price < 0:
            raise ValidationError("Runner price cannot be negative")

        # Check if drawer fits in carcass
        drawer_depth, drawer_width = self.calculate_drawer_dimensions()
        if drawer_width <= 0 or drawer_depth <= 0:
            raise ValidationError(
                "Drawer dimensions are invalid for the carcass size"
            )

    def calculate_drawer_dimensions(self) -> Tuple[float, float]:
        """Calculate actual drawer box dimensions.

        Returns:
            Tuple of (depth, width) in mm
        """
        drawer_depth = self.runner_size - DRAWER_RUNNER_CLEARANCE
        drawer_width = (self.carcass.width -
                       2 * self.carcass.material_thickness -
                       DRAWER_SIDE_CLEARANCE)

        return drawer_depth, drawer_width

    def get_parts(self) -> List[Rectangle]:
        """Generate all rectangular parts for the drawer with grain direction."""
        drawer_depth, drawer_width = self.calculate_drawer_dimensions()

        # Internal dimensions accounting for material thickness
        internal_width = drawer_width - 2 * self.thickness
        internal_depth = drawer_depth - 2 * self.thickness

        parts = []
        grain_direction = get_grain_direction_for_material(self.material)

        # Front and back panels - height should align with sheet width
        for panel_type in ["front", "back"]:
            parts.append(Rectangle(
                width=internal_width,
                height=self.height,
                id=f"{self.carcass.name}_drawer_{self.height}_{panel_type}",
                grain_direction=GrainDirection.WITH_WIDTH,  # Height aligns with sheet width
                component_type=f"drawer_{panel_type}"
            ))

        # Side panels - height should align with sheet width
        for i in range(2):
            parts.append(Rectangle(
                width=drawer_depth,
                height=self.height,
                id=f"{self.carcass.name}_drawer_{self.height}_side_{i+1}",
                grain_direction=GrainDirection.WITH_WIDTH,  # Height aligns with sheet width
                component_type="drawer_side"
            ))

        # Base panel - can use either direction (typically with width for efficiency)
        parts.append(Rectangle(
            width=internal_width + DRAWER_GROOVE_ALLOWANCE,
            height=internal_depth + DRAWER_GROOVE_ALLOWANCE,
            id=f"{self.carcass.name}_drawer_{self.height}_base",
            grain_direction=GrainDirection.WITH_WIDTH if grain_direction != GrainDirection.NONE else GrainDirection.NONE,
            component_type="drawer_base"
        ))

        return parts

    def get_total_area(self) -> float:
        """Calculate total material area for the drawer."""
        return sum(part.area() for part in self.get_parts())

    def get_total_runner_cost(self) -> float:
        """Calculate total cost for drawer runners (pair)."""
        return 2 * self.runner_price

    @property
    def component_type(self) -> ComponentType:
        """Get component type."""
        return ComponentType.DRAWER

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'type': self.component_type.value,
            'height': self.height,
            'thickness': self.thickness,
            'material': self.material,
            'runner_model': self.runner_model,
            'runner_size': self.runner_size,
            'runner_capacity': self.runner_capacity,
            'runner_price': self.runner_price,
            'carcass_name': self.carcass.name  # Store reference
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], carcass: Carcass) -> 'Drawer':
        """Create from dictionary."""
        data = data.copy()
        data.pop('type', None)
        data.pop('carcass_name', None)
        data['carcass'] = carcass
        return cls(**data)


@dataclass
class Doors(Component):
    """Represents cabinet doors.

    Attributes:
        carcass: Parent carcass for dimensions
        material: Door material type
        door_type: Style of door
        material_thickness: Door thickness in mm
        moulding: Whether to include decorative moulding
        cut_handle: Whether to cut integrated handles
        quantity: Number of doors
        position: Overlay or inset mounting
        margin: Gap around doors in mm
        inter_door_margin: Gap between multiple doors
        hinge_bore_diameter: Diameter of hinge cup bore
    """
    carcass: Carcass
    material: str
    door_type: str
    material_thickness: int
    moulding: bool
    cut_handle: bool
    quantity: int
    position: str
    margin: int
    hinge_type: str
    hinges_per_door: int
    sprayed: bool
    hinge_price: float = 0.0
    inter_door_margin: int = 1
    hinge_bore_diameter: int = 35

    def __post_init__(self):
        """Validate doors after creation."""
        self.validate()

    def validate(self) -> None:
        """Validate door specifications."""
        if not 0 <= self.quantity <= 4:  # Updated to allow up to 4 doors
            raise ValidationError(
                f"Door quantity must be between 0 and 4 (got {self.quantity})"
            )

        if self.quantity == 0:
            return  # No further validation needed

        if not MIN_THICKNESS <= self.material_thickness <= MAX_THICKNESS:
            raise ValidationError(
                f"Door thickness must be between {MIN_THICKNESS} and "
                f"{MAX_THICKNESS}mm"
            )

        if self.margin < 0:
            raise ValidationError("Door margin cannot be negative")

        if self.inter_door_margin < 0:
            raise ValidationError("Inter-door margin cannot be negative")

        try:
            DoorPosition(self.position)
        except ValueError:
            raise ValidationError(f"Invalid door position: {self.position}")

        # Validate door width
        total_door_width = self._calculate_total_door_width()
        if total_door_width <= 0:
            raise ValidationError("Invalid door dimensions for carcass")

    def _calculate_total_door_width(self) -> float:
        """Calculate total width available for doors."""
        if self.position == DoorPosition.OVERLAY.value:
            return self.carcass.width - self.margin
        elif self.position == DoorPosition.INSET.value:
            internal_width = self.carcass.internal_dimensions.width
            return internal_width - self.margin
        else:
            return self.carcass.width - self.margin

    def get_parts(self) -> List[Rectangle]:
        """Generate all rectangular parts for doors with grain direction."""
        if self.quantity == 0:
            return []

        parts = []
        grain_direction = get_grain_direction_for_material(self.material)

        if self.position == DoorPosition.INSET.value:
            door_height = self.carcass.internal_dimensions.height - DOOR_INSET_HEIGHT_CLEARANCE
        else:
            door_height = self.carcass.height

        door_width = self._calculate_total_door_width()

        # Calculate individual door width for multiple doors
        total_margins = (self.quantity - 1) * self.inter_door_margin
        individual_door_width = (door_width - total_margins) / self.quantity

        # Doors typically have grain running vertically (with height)
        # But for materials without grain, use NONE
        door_grain_direction = GrainDirection.WITH_HEIGHT if grain_direction != GrainDirection.NONE else GrainDirection.NONE

        for i in range(self.quantity):
            parts.append(Rectangle(
                width=individual_door_width,
                height=door_height,
                id=f"{self.carcass.name}_door_{i+1}",
                grain_direction=door_grain_direction,
                component_type="door"
            ))

        return parts

    def get_total_area(self) -> float:
        """Calculate total material area for doors."""
        return sum(part.area() for part in self.get_parts())

    @property
    def component_type(self) -> ComponentType:
        """Get component type."""
        return ComponentType.DOOR

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'type': self.component_type.value,
            'material': self.material,
            'door_type': self.door_type,
            'material_thickness': self.material_thickness,
            'moulding': self.moulding,
            'cut_handle': self.cut_handle,
            'quantity': self.quantity,
            'position': self.position,
            'margin': self.margin,
            'hinge_type': self.hinge_type,
            'hinges_per_door': self.hinges_per_door,
            'hinge_price': self.hinge_price,
            'inter_door_margin': self.inter_door_margin,
            'hinge_bore_diameter': self.hinge_bore_diameter,
            'carcass_name': self.carcass.name,
            'sprayed': self.sprayed
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], carcass: Carcass) -> 'Doors':
        """Create from dictionary."""
        data = data.copy()
        data.pop('type', None)
        data.pop('carcass_name', None)
        data['carcass'] = carcass
        return cls(**data)


@dataclass
class FaceFrame(Component):
    """Represents a decorative face frame.

    Attributes:
        carcass: Parent carcass for dimensions
        material: Material type for frame
        moulding: Whether to include decorative moulding
        thickness: Frame material thickness
        frame_border: Width of frame borders
        bottom_piece_height: Height of bottom rail
    """
    carcass: Carcass
    material: str
    moulding: bool
    sprayed: bool
    thickness: int = DEFAULT_FACE_FRAME_THICKNESS
    frame_border: int = DEFAULT_FACE_FRAME_BORDER
    bottom_piece_height: int = DEFAULT_FACE_FRAME_BOTTOM_HEIGHT

    def __post_init__(self):
        """Validate face frame after creation."""
        self.validate()

    def validate(self) -> None:
        """Validate face frame specifications."""
        if not self.material or not self.material.strip():
            raise ValidationError("Frame type cannot be empty")

        if not MIN_THICKNESS <= self.thickness <= MAX_THICKNESS:
            raise ValidationError(
                f"Frame thickness must be between {MIN_THICKNESS} and "
                f"{MAX_THICKNESS}mm"
            )

        if self.frame_border <= 0 or self.frame_border > 200:
            raise ValidationError(
                "Frame border must be between 1 and 200mm"
            )

        if self.bottom_piece_height <= 0 or self.bottom_piece_height > 300:
            raise ValidationError(
                "Bottom piece height must be between 1 and 300mm"
            )

    def get_parts(self) -> List[Rectangle]:
        """Generate all rectangular parts for the face frame with grain direction."""
        parts = []
        grain_direction = get_grain_direction_for_material(self.material)

        # Get internal carcass dimensions
        internal_dims = self.carcass.internal_dimensions

        # Top rail - grain typically runs with width
        parts.append(Rectangle(
            width=internal_dims.width,
            height=self.frame_border,
            id=f"{self.carcass.name}_face_frame_top",
            grain_direction=GrainDirection.WITH_WIDTH if grain_direction != GrainDirection.NONE else GrainDirection.NONE,
            component_type="face_frame_rail"
        ))

        # Bottom rail (taller) - grain typically runs with width
        parts.append(Rectangle(
            width=internal_dims.width,
            height=self.bottom_piece_height,
            id=f"{self.carcass.name}_face_frame_bottom",
            grain_direction=GrainDirection.WITH_WIDTH if grain_direction != GrainDirection.NONE else GrainDirection.NONE,
            component_type="face_frame_rail"
        ))

        # Side stiles (2 pieces) - grain typically runs with height
        # Height includes overlap with rails
        stile_height = (internal_dims.height +
                       self.carcass.material_thickness +
                       self.bottom_piece_height)

        for i in range(2):
            parts.append(Rectangle(
                width=self.frame_border,
                height=stile_height,
                id=f"{self.carcass.name}_face_frame_side_{i+1}",
                grain_direction=GrainDirection.WITH_HEIGHT if grain_direction != GrainDirection.NONE else GrainDirection.NONE,
                component_type="face_frame_stile"
            ))

        return parts

    def get_total_area(self) -> float:
        """Calculate total material area for the face frame."""
        return sum(part.area() for part in self.get_parts())

    @property
    def component_type(self) -> ComponentType:
        """Get component type."""
        return ComponentType.FACE_FRAME

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'type': self.component_type.value,
            'material': self.material,
            'moulding': self.moulding,
            'sprayed': self.sprayed,
            'thickness': self.thickness,
            'frame_border': self.frame_border,
            'bottom_piece_height': self.bottom_piece_height,
            'carcass_name': self.carcass.name
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], carcass: Carcass) -> 'FaceFrame':
        """Create from dictionary."""
        data = data.copy()
        data.pop('type', None)
        data.pop('carcass_name', None)
        data['carcass'] = carcass
        return cls(**data)


@dataclass
class DBCDrawer(Component):
    """Represents a pre-made drawer from The Drawer Box Company.

    Attributes:
        height: Drawer height in mm
        width: Drawer width in mm
        depth: Drawer depth in mm
        material: Material type (Oak or Walnut)
        price: Price from the DBC pricing table
        carcass_name: Name of parent carcass for reference
    """
    height: int
    width: int
    depth: int
    material: str  # "Oak" or "Walnut"
    price: float
    carcass_name: str

    def __post_init__(self):
        """Validate drawer after creation."""
        self.validate()

    def validate(self) -> None:
        """Validate DBC drawer specifications."""
        if self.material not in ["Oak", "Walnut"]:
            raise ValidationError(f"DBC material must be Oak or Walnut, got {self.material}")

        if self.price < 0:
            raise ValidationError("Price cannot be negative")

        # Validate dimensions are in DBC catalog
        valid_heights = [100, 150, 175, 225, 270, 300]
        valid_widths = [252, 352, 452, 552, 652, 752, 852, 952, 1152]
        valid_depths = [300, 450, 500, 550, 600]

        if self.height not in valid_heights:
            raise ValidationError(f"DBC drawer height {self.height} not available. Valid heights: {valid_heights}")

        if self.width not in valid_widths:
            raise ValidationError(f"DBC drawer width {self.width} not available. Valid widths: {valid_widths}")

        if self.depth not in valid_depths:
            raise ValidationError(f"DBC drawer depth {self.depth} not available. Valid depths: {valid_depths}")

    def get_parts(self) -> List[Rectangle]:
        """DBC drawers don't generate parts for cutting - they're pre-made.

        Returns:
            Empty list since these are purchased complete
        """
        return []

    def get_total_area(self) -> float:
        """Calculate notional area for costing purposes.

        Returns:
            Area in square millimeters (not used for cutting)
        """
        # Return 0 since we don't cut these ourselves
        return 0.0

    def get_total_cost(self) -> float:
        """Get the total cost of this DBC drawer.

        Returns:
            Price of the drawer
        """
        return self.price

    @property
    def component_type(self) -> ComponentType:
        """Get component type."""
        return ComponentType.DRAWER

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'type': 'dbc_drawer',
            'height': self.height,
            'width': self.width,
            'depth': self.depth,
            'material': self.material,
            'price': self.price,
            'carcass_name': self.carcass_name
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DBCDrawer':
        """Create from dictionary."""
        data = data.copy()
        data.pop('type', None)
        return cls(**data)