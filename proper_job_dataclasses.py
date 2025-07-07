from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Rectangle:
    """Represents a rectangle to be packed"""
    width: float
    height: float
    id: str

    def area(self) -> float:
        return self.width * self.height

    def rotated(self) -> 'Rectangle':
        """Returns a rotated version of this rectangle"""
        return Rectangle(self.height, self.width, self.id)


# Define data structures
@dataclass
class Carcass:
    name: str
    height: float
    width: float
    depth: float
    material: str
    material_thickness: float
    shelves: int = 0


    def get_parts(self) -> List[Tuple[float, float, str]]:
        """Returns a list of parts needed for this unit as (length, width, part_name)"""
        parts = []
        # Back
        parts.append(Rectangle(self.height, self.width, f"{self.name} - Back"))

        # Sides
        parts.append(Rectangle(self.height, self.depth - self.material_thickness, f"{self.name} - Side 1"))
        parts.append(Rectangle(self.height, self.depth - self.material_thickness, f"{self.name} - Side 2"))

        # Top and Base
        parts.append(Rectangle(self.width - 2 * self.material_thickness, self.depth - self.material_thickness,
                      f"{self.name} - Base"))
        parts.append(Rectangle(self.width - 2 * self.material_thickness, self.depth - self.material_thickness,
                      f"{self.name} - Top"))

        # Shelves
        for i in range(self.shelves):
            parts.append(Rectangle(self.width - 2 * self.material_thickness, self.depth - self.material_thickness, f"{self.name}_shelf {i+1}"))

        return parts

    def get_total_area(self) -> float:
        """Calculate the total area of material needed for this unit"""
        total_area = 0
        for part in self.get_parts():
            total_area += part[0] * part[1]
        return total_area

@dataclass
class Drawer:
    height: int
    thickness: int
    material: str
    runner_model: str
    runner_size: int
    runner_capacity: int
    carcass: Carcass
    runner_price: float

    def calculate_draw_dims(self):
        drawer_depth = self.runner_size - 10
        drawer_width = self.carcass.width - (2 * self.carcass.material_thickness) - 43
        return drawer_depth, drawer_width

    def get_parts(self) -> List[Tuple[float, float, str]]:
        drawer_depth, drawer_width = self.calculate_draw_dims()

        internal_drawer_width = drawer_width - (2*self.thickness)
        internal_drawer_depth = drawer_depth - (2*self.thickness)

        parts = []

        # Front & Back
        front = Rectangle(internal_drawer_width, self.height, f"{self.carcass.name}_drawer_{self.height}_front")
        back = Rectangle(internal_drawer_width, self.height, f"{self.carcass.name}_drawer_{self.height}_back")
        parts.append(front)
        parts.append(back)

        # Sides
        side = Rectangle(drawer_depth, self.height, f"{self.carcass.name}_drawer_{self.height}_side")
        parts.append(side)
        parts.append(side)


        # Base
        # internal width + 15 * internal depth + 15
        base = Rectangle(internal_drawer_width + 15, internal_drawer_depth + 15, f"{self.carcass.name}_drawer_{self.height}_base")

        parts.append(base)
        return parts

    def get_total_runners_price(self):
        return 2 * self.runner_price



@dataclass
class FaceFrame:
    carcass: Carcass
    type: str
    moulding: bool
    thickness: int = 25
    frame_border: int = 36
    bottom_piece_height: int = 100

    def get_parts(self):
        parts = []
        internal_carcass_height = self.carcass.height - (2 * self.carcass.material_thickness)
        internal_carcass_width = self.carcass.width - (2 * self.carcass.material_thickness)

        # Top
        parts.append(Rectangle(internal_carcass_width, self.frame_border, f"{self.carcass.name}_face_frame_top"))

        # Bottom
        parts.append(Rectangle(internal_carcass_width, self.bottom_piece_height, f"{self.carcass.name}_face_frame_bottom"))

        # Sides
        for i in range(2):
            parts.append(Rectangle(self.frame_border,
                                   (internal_carcass_height+self.carcass.material_thickness+self.bottom_piece_height),
                                    f"{self.carcass.name}_face_frame_side"))

        return parts



@dataclass
class Doors:
    carcass: Carcass
    material: str
    type: str
    material_thickness: int
    moulding: bool
    cut_handle: bool
    quantity: int
    position: str
    margin: int
    inter_door_margin: int = 1

    def get_parts(self) -> List[Tuple[float, float, str]]:
        parts = []
        if self.position == "Overlay":
            door_height = self.carcass.height
            door_width = self.carcass.width - self.margin
        elif self.position == "Inset":
            internal_carcass_height = self.carcass.height - (2*self.carcass.material_thickness)
            internal_carcass_width = self.carcass.width - (2*self.carcass.material_thickness)
            door_height = internal_carcass_height - 22
            door_width = internal_carcass_width - self.margin
        else:
            return []

        for i in range(self.quantity):
            parts.append(Rectangle((door_width/self.quantity) - self.inter_door_margin, door_height, f"{self.carcass.name}_door_{i}"))

        return parts



@dataclass
class Cabinet:
    carcass: Carcass
    drawers: List[Drawer]
    quantity: int
    doors: Doors
    face_frame: FaceFrame



    def get_parts(self):
        all_parts = self.carcass.get_parts() + [drawer.get_parts() for drawer in self.drawers]
        if self.doors is not None:
            all_parts += self.doors.get_parts()
        if self.face_frame is not None:
            all_parts += self.face_frame.get_parts()
        return

    def get_total_area(self):
        return self.quantity * sum([part.area() for part in self.get_parts()])

    def get_unit_area(self):
        return sum([part.area() for part in self.get_parts()])


@dataclass
class PlacedRectangle:
    """Represents a rectangle that has been placed on a sheet"""
    x: float
    y: float
    width: float
    height: float
    id: int

    def overlaps(self, other: 'PlacedRectangle') -> bool:
        """Check if this rectangle overlaps with another"""
        return not (self.x + self.width <= other.x or
                    other.x + other.width <= self.x or
                    self.y + self.height <= other.y or
                    other.y + other.height <= self.y)