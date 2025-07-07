import copy
import json
from typing import List, Dict, Tuple
from collections import defaultdict

from gene_algorithm import BinPackingGA
from proper_job_dataclasses import Cabinet, Carcass, Drawer, FaceFrame, Doors


class QuoteCalculator:
    def __init__(self, labour_cost_dict, sheet_materials_dict):
        self.labour_costs_dict = labour_cost_dict
        self.sheet_materials_dict = sheet_materials_dict
        self.units: List[Cabinet] = []
        # Dictionary to store sheet prices by material and thickness
        # Format: {(material, thickness): price}
        self.sheet_prices: Dict[Tuple[str, float], float] = {}
        self.sheet_width: float = 2440  # Standard sheet size in mm
        self.sheet_height: float = 1220  # Standard sheet size in mm
        self.labor_rate: float = 0
        self.markup_percentage: float = 0
        self.optimizers = {}  # Store optimizers for each material/thickness combo
        self.solutions = {}  # Store solutions for each material/thickness combo
        self.sheets_by_material = {}  # Store sheets grouped by material/thickness


    def set_sheet_price(self, material: str, thickness: float, price: float) -> None:
        """Set the price for a specific material and thickness combination"""
        self.sheet_prices[(material, thickness)] = price

    def get_sheet_price(self, material: str, thickness: float) -> float:
        """Get the price for a specific material and thickness combination"""
        return self.sheet_prices.get((material, thickness), 0.0)

    def add_unit(self, unit: Cabinet) -> None:
        self.units.append(unit)

    def remove_unit(self, index: int) -> None:
        if 0 <= index < len(self.units):
            self.units.pop(index)

    def duplicate_unit(self, index: int) -> None:
        if 0 <= index < len(self.units):
            unit = copy.deepcopy(self.units[index])
            unit.carcass.name = f"{unit.carcass.name} (copy)"
            self.units.append(unit)

    def convert_to_material_type(self, original_material):
        material_type = original_material
        for material in self.sheet_materials_dict["Materials"]:
            if material["Material"] == original_material:
                if material["Veneer"]:
                    material_type = "Veneer"

                if material["Hardwood"]:
                    material_type = "Hardwood"

        return material_type

    def calculate_total_labour(self):
        total_labour_hours = 0
        for unit in self.units:
            unit_labour = 0

            # Carcass
            carcass_material_type = self.convert_to_material_type(unit.carcass.material)
            no_shelves = unit.carcass.shelves

            unit_labour += self.labour_costs_dict['Carcass'][carcass_material_type]
            # TODO Add shelf

            # Drawers
            for drawer in unit.drawers:
                drawer_material_type = self.convert_to_material_type(drawer.material)
                unit_labour += self.labour_costs_dict['Drawers'][drawer_material_type]

            # Doors
            door_unit_labour = 0
            doors_type = unit.doors.type
            doors_material = self.convert_to_material_type(unit.doors.material)
            doors_material = "Sprayed MDF" if doors_material == "MDF" else doors_material # Specific to doors
            for material_and_type in self.labour_costs_dict['Doors']:
                if material_and_type["Material"] == doors_material and material_and_type["Type"] == doors_type:
                    door_unit_labour += material_and_type['Per Door (hours)']
                    if unit.doors.moulding:
                        door_unit_labour += material_and_type['Moulding']
                    if unit.doors.cut_handle:
                        door_unit_labour += material_and_type['Moulding']
                    break
            unit_labour += (door_unit_labour * unit.doors.quantity)

            # Face Frames
            face_frame = unit.face_frame
            if face_frame.type != '': # TODO:Find better way
                material_type = self.convert_to_material_type(face_frame.type)
                unit_labour += self.labour_costs_dict['Face Frames'][material_type]['Per Frame (hours)']
                if face_frame.moulding:
                    unit_labour += self.labour_costs_dict['Face Frames'][material_type]['Moulding']

            total_labour_hours += unit_labour

        return total_labour_hours

    def get_all_parts_by_material(self) -> Dict[Tuple[str, float], List]:
        """Group all parts by material and thickness"""
        parts_by_material = defaultdict(list)

        for unit in self.units:
            # Get carcass parts
            carcass_parts = unit.carcass.get_parts()
            carcass_key = (unit.carcass.material, unit.carcass.material_thickness)

            # Multiply parts by quantity
            for _ in range(unit.quantity):
                parts_by_material[carcass_key].extend(carcass_parts)

            # Get drawer parts
            for drawer in unit.drawers:
                drawer_parts = drawer.get_parts()
                drawer_key = (drawer.material, drawer.thickness)

                # Multiply drawer parts by unit quantity
                for _ in range(unit.quantity):
                    parts_by_material[drawer_key].extend(drawer_parts)

            # Get door parts if doors exist
            if hasattr(unit, 'doors') and unit.doors is not None:
                door_parts = unit.doors.get_parts()
                door_key = (unit.doors.material, unit.doors.material_thickness)

                if len(door_parts) > 0:
                    # Multiply door parts by unit quantity
                    for _ in range(unit.quantity):
                        parts_by_material[door_key].extend(door_parts)

            # Get face frame parts if face frame exists
            if hasattr(unit, 'face_frame') and unit.face_frame is not None:
                face_frame_parts = unit.face_frame.get_parts()
                # Assuming face frame uses same material as carcass
                face_frame_key = (unit.carcass.material, unit.face_frame.thickness)

                if len(face_frame_parts) > 0:
                    # Multiply face frame parts by unit quantity
                    for _ in range(unit.quantity):
                        parts_by_material[face_frame_key].extend(face_frame_parts)

        return dict(parts_by_material)

    def calculate_quote(self) -> Dict:
        parts_by_material = self.get_all_parts_by_material()

        total_material_cost = 0
        sheets_breakdown = {}
        total_sheets = 0

        # Process each material/thickness combination separately
        for (material, thickness), parts in parts_by_material.items():
            if not parts:  # Skip if no parts for this material
                continue

            # Optimize sheet usage for this material/thickness
            optimizer = BinPackingGA(self.sheet_width, self.sheet_height)
            solution = optimizer.evolve(parts)
            num_sheets = solution.fitness
            sheets = optimizer.get_detailed_solution(parts, solution.genes)

            # Store results
            self.optimizers[(material, thickness)] = optimizer
            self.solutions[(material, thickness)] = solution
            self.sheets_by_material[(material, thickness)] = sheets

            # Calculate cost for this material
            sheet_price = self.get_sheet_price(material, thickness)
            material_cost = num_sheets * sheet_price * 1.1  # Including 10% wastage
            total_material_cost += material_cost
            total_sheets += num_sheets

            # Store breakdown
            sheets_breakdown[(material, thickness)] = {
                'sheets_required': num_sheets,
                'sheet_price': sheet_price,
                'material_cost': material_cost,
                'sheets_detail': sheets,
                'parts_count': len(parts)
            }

        # Calculate runner costs
        runner_cost = 0
        for cabinet in self.units:
            for drawer in cabinet.drawers:
                runner_cost += drawer.get_total_runners_price() * cabinet.quantity

        total_material_cost += runner_cost

        # Calculate labor cost
        labor_hours = self.calculate_total_labour()
        labor_cost = labor_hours * self.labor_rate

        # Calculate total cost
        subtotal = total_material_cost + labor_cost
        markup = subtotal * (self.markup_percentage / 100)
        total = subtotal + markup

        return {
            'units': len(self.units),
            'total_sheets_required': total_sheets,
            'sheets_breakdown': sheets_breakdown,
            'material_cost': total_material_cost,
            'runner_cost': runner_cost,
            'labor_hours': labor_hours,
            'labor_cost': labor_cost,
            'subtotal': subtotal,
            'markup': markup,
            'total': total,
            'materials_used': list(parts_by_material.keys())
        }

    def get_material_summary(self) -> Dict:
        """Get a summary of all materials and thicknesses used"""
        materials_used = set()

        for unit in self.units:
            # Carcass material
            materials_used.add((unit.carcass.material, unit.carcass.material_thickness))

            # Drawer materials
            for drawer in unit.drawers:
                materials_used.add((drawer.material, drawer.thickness))

            # Door materials
            if hasattr(unit, 'doors') and unit.doors is not None:
                materials_used.add((unit.doors.material, unit.doors.material_thickness))

            # Face frame materials
            if hasattr(unit, 'face_frame') and unit.face_frame is not None:
                materials_used.add((unit.carcass.material, unit.face_frame.thickness))

        return {
            'materials': list(materials_used),
            'missing_prices': [mat for mat in materials_used if mat not in self.sheet_prices]
        }

    def save_to_file(self, filename: str) -> None:
        """Save the current project to a JSON file"""
        data = {
            'units': [self._serialize_cabinet(c) for c in self.units],
            'sheet_prices': {f"{mat}_{thick}": price for (mat, thick), price in self.sheet_prices.items()},
            'sheet_width': self.sheet_width,
            'sheet_height': self.sheet_height,
            'labor_rate': self.labor_rate,
            'markup_percentage': self.markup_percentage
        }

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

    def _serialize_cabinet(self, cabinet: Cabinet) -> Dict:
        """Helper method to serialize a cabinet to dictionary"""
        return {
            'carcass': vars(cabinet.carcass),
            'drawers': [vars(drawer) for drawer in cabinet.drawers],
            'quantity': cabinet.quantity,
            'doors': vars(cabinet.doors) if cabinet.doors else None,
            'face_frame': vars(cabinet.face_frame) if cabinet.face_frame else None
        }

    def load_from_file(self, filename: str) -> None:
        """Load project from a JSON file"""
        with open(filename, 'r') as f:
            data = json.load(f)

        # Load sheet prices
        self.sheet_prices = {}
        for key, price in data.get('sheet_prices', {}).items():
            material, thickness = key.rsplit('_', 1)
            self.sheet_prices[(material, float(thickness))] = price

        # Load units (you'll need to implement cabinet reconstruction)
        self.units = []
        for unit_data in data['units']:
            # This will need to be implemented based on your Cabinet constructor
            cabinet = self._deserialize_cabinet(unit_data)
            self.units.append(cabinet)

        self.sheet_width = data.get('sheet_width', 2440)
        self.sheet_height = data.get('sheet_height', 1220)
        self.labor_rate = data.get('labor_rate', 0)
        self.markup_percentage = data.get('markup_percentage', 0)

    def _deserialize_cabinet(self, data: Dict) -> Cabinet:
        """Helper method to deserialize a cabinet from dictionary"""
        # Reconstruct carcass
        carcass = Carcass(**data['carcass'])

        # Reconstruct drawers
        drawers = []
        for drawer_data in data['drawers']:
            drawer = Drawer(**drawer_data)
            drawers.append(drawer)

        # Reconstruct doors and face frame
        doors = Doors(**data['doors']) if data['doors'] else None
        face_frame = FaceFrame(**data['face_frame']) if data['face_frame'] else None

        return Cabinet(
            carcass=carcass,
            drawers=drawers,
            quantity=data['quantity'],
            doors=doors,
            face_frame=face_frame
        )