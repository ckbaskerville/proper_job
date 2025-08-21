"""Application constants and configuration values."""

import os
from pathlib import Path
import sys

def get_exe_directory():
    """Get the directory where the executable is located"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return os.path.dirname(sys.executable)
    else:
        # Running as script (for development)
        return os.path.dirname(os.path.abspath(__file__))

# ==================== Application Info ====================
APP_NAME = "Proper Job"
APP_VERSION = "2.0.0"
APP_AUTHOR = "Your Company Name"
APP_DESCRIPTION = "Professional Kitchen Cabinet Design & Quotation System"
WINDOW_TITLE = f"{APP_NAME}"

# ==================== Window Settings ====================
DEFAULT_WINDOW_SIZE = "1200x800"
MIN_WINDOW_WIDTH = 800
MIN_WINDOW_HEIGHT = 600
WINDOW_PADDING = 10

# ==================== File Paths ====================
# Base directories
BASE_DIR = Path(get_exe_directory())
RESOURCES_DIR = BASE_DIR / "resources"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
TEMP_DIR = BASE_DIR / "temp"

# Resource files
RUNNERS_FILE = RESOURCES_DIR / "runners.json"
MATERIALS_FILE = RESOURCES_DIR / "sheet_material.json"
LABOR_COSTS_FILE = RESOURCES_DIR / "labour_costs.json"
HINGES_FILE = RESOURCES_DIR / "hinges.json"
DBC_DRAWERS_OAK_FILE = RESOURCES_DIR / "DBC_drawers_oak.csv"
DBC_DRAWERS_WALNUT_FILE = RESOURCES_DIR / "DBC_drawers_walnut.csv"
ICON_FILE = RESOURCES_DIR / "icon.ico"
LOGO_FILE = RESOURCES_DIR / "logo.png"

# User data files
SETTINGS_FILE = DATA_DIR / "settings.json"
RECENT_PROJECTS_FILE = DATA_DIR / "recent_projects.json"
CUSTOM_MATERIALS_FILE = DATA_DIR / "custom_materials.json"

# ==================== Default Values ====================
# Sheet dimensions (mm)
DEFAULT_SHEET_WIDTH = 2440.0
DEFAULT_SHEET_HEIGHT = 1220.0
COMMON_SHEET_SIZES = [
    (2440, 1220, "Standard 8×4"),
    (3050, 1220, "10×4"),
    (2800, 2070, "MDF Large"),
    (3660, 1830, "12×6")
]

# Material defaults
DEFAULT_MATERIAL = "Laminate"
DEFAULT_MATERIAL_THICKNESS = 18.0
STANDARD_THICKNESSES = [6, 9, 12, 15, 16, 18, 19, 22, 25, 30]

# Labor defaults
DEFAULT_LABOR_RATE = 40.0  # £/hour
DEFAULT_MARKUP_PERCENTAGE = 20.0  # %
DEFAULT_VAT_RATE = 0.20  # 20%

# Waste and efficiency
WASTE_FACTOR = 1.1  # 10% waste allowance
MIN_EFFICIENCY_WARNING = 0.75  # Warn if efficiency < 75%
TARGET_EFFICIENCY = 0.85  # Target 85% material usage

# ==================== Component Constraints ====================
# Dimension limits (mm)
MIN_DIMENSION = 10.0
MAX_DIMENSION = 5000.0
MIN_THICKNESS = 3.0
MAX_THICKNESS = 50.0

# Component limits
MAX_SHELVES = 10
MAX_DRAWERS = 10
MAX_DOORS = 4
MAX_CABINETS_PER_PROJECT = 100

# Standard gaps and clearances (mm)
STANDARD_GAP = 2.0
DOOR_GAP = 3.0
DRAWER_GAP = 2.0

# ==================== Drawer Constants ====================
DRAWER_RUNNER_CLEARANCE = 10  # mm - clearance for runner mechanism
DRAWER_SIDE_CLEARANCE = 43  # mm - total clearance for both sides
DRAWER_GROOVE_ALLOWANCE = 15  # mm - extra for base panel grooves
DRAWER_MIN_HEIGHT = 60  # mm
DRAWER_MAX_HEIGHT = 300  # mm

# Standard drawer runner sizes
STANDARD_RUNNER_SIZES = [250, 300, 350, 400, 450, 500, 550, 600]
RUNNER_CAPACITIES = [20, 30, 40, 50, 70]  # kg

# ==================== Door Constants ====================
DOOR_INSET_HEIGHT_CLEARANCE = 22  # mm - clearance for inset doors
DEFAULT_DOOR_MARGIN = 4  # mm - gap around doors
DEFAULT_DOOR_INTER_MARGIN = 1  # mm - gap between adjacent doors
DOOR_MIN_WIDTH = 200  # mm
DOOR_MAX_WIDTH = 600  # mm
HINGE_BORE_DIAMETER = 35  # mm - standard euro hinge
HINGE_CUP_DEPTH = 13  # mm
MIN_HINGE_DISTANCE = 70  # mm - from edge

# Door overlay options
DOOR_OVERLAYS = {
    "Full": 18,     # mm
    "Half": 9,      # mm
    "Inset": 0      # mm
}

# ==================== Face Frame Constants ====================
DEFAULT_FACE_FRAME_THICKNESS = 25  # mm
DEFAULT_FACE_FRAME_BORDER = 36  # mm - width of frame pieces
DEFAULT_FACE_FRAME_BOTTOM_HEIGHT = 100  # mm - height of bottom rail
MIN_FACE_FRAME_WIDTH = 20  # mm
MAX_FACE_FRAME_WIDTH = 100  # mm

# ==================== Carcass Standards ====================
# Standard cabinet heights (mm)
STANDARD_HEIGHTS = {
    "Base": 720,
    "Tall": 2100,
    "Wall": 720,
    "Wall Tall": 900
}

# Standard cabinet widths (mm)
STANDARD_WIDTHS = [300, 400, 450, 500, 600, 800, 900, 1000, 1200]

# Standard cabinet depths (mm)
STANDARD_DEPTHS = {
    "Base": 560,
    "Wall": 300,
    "Tall": 560,
    "Reduced": 450
}

# ==================== Genetic Algorithm Settings ====================
GA_POPULATION_SIZE = 50
GA_MUTATION_RATE = 0.1
GA_GENERATIONS = 100
GA_TOURNAMENT_SIZE = 3
GA_ELITE_PERCENTAGE = 0.1
GA_CROSSOVER_RATE = 0.8
GA_MAX_STAGNATION = 20  # Stop if no improvement for N generations

# ==================== UI Settings ====================
# Table settings
TABLE_ROW_HEIGHT = 25
TABLE_HEADER_HEIGHT = 30
DEFAULT_COLUMN_WIDTH = 100

# Widget dimensions
LABEL_WIDTH = 15
ENTRY_WIDTH = 20
BUTTON_WIDTH = 12
COMBOBOX_WIDTH = 15

# Padding and margins
WIDGET_PADDING = 5
FRAME_PADDING = 10
SECTION_SPACING = 20

# Font sizes
FONT_SIZE_SMALL = 9
FONT_SIZE_NORMAL = 10
FONT_SIZE_LARGE = 12
FONT_SIZE_TITLE = 14
FONT_SIZE_HEADER = 16

# Animation settings
ANIMATION_DURATION = 200  # ms
TOOLTIP_DELAY = 500  # ms

# ==================== Validation Messages ====================
VALIDATION_MESSAGES = {
    'dimension_range': "Dimension must be between {min} and {max}mm",
    'positive_required': "{field} must be a positive number",
    'integer_required': "{field} must be a whole number",
    'selection_required': "Please select a {field}",
    'name_required': "Name cannot be empty",
    'invalid_email': "Please enter a valid email address",
    'invalid_phone': "Please enter a valid phone number"
}

# ==================== Export Formats ====================
EXPORT_FORMATS = [
    ("JSON files", "*.json"),
    ("CSV files", "*.csv"),
    ("PDF files", "*.pdf"),
    ("Text files", "*.txt"),
    ("All files", "*.*")
]

PROJECT_FILE_EXTENSION = ".pjb"  # Proper Job Project
PROJECT_FILE_FILTER = [
    ("Proper Job Projects", f"*{PROJECT_FILE_EXTENSION}"),
    ("JSON files", "*.json"),
    ("All files", "*.*")
]

# ==================== Report Settings ====================
COMPANY_INFO = {
    'name': 'Your Company Name',
    'address': 'Your Address',
    'phone': 'Your Phone',
    'email': 'your@email.com',
    'website': 'www.yourwebsite.com',
    'registration': 'Company Reg No: 12345678'
}

# ==================== Logging ====================
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_LEVEL = "INFO"
LOG_FILE = "kitchen_cabinet_system.log"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

# ==================== Performance Settings ====================
MAX_UNDO_STACK = 50
AUTOSAVE_INTERVAL = 300  # seconds (5 minutes)
CACHE_SIZE = 100  # Maximum cached calculations
THUMBNAIL_SIZE = (200, 150)  # pixels

# ==================== Network Settings ====================
UPDATE_CHECK_URL = "https://api.yourcompany.com/updates/kitchen-cabinet"
FEEDBACK_URL = "https://api.yourcompany.com/feedback"
LICENSE_SERVER = "https://api.yourcompany.com/license"
CONNECTION_TIMEOUT = 10  # seconds

# ==================== Feature Flags ====================
FEATURES = {
    'advanced_optimization': True,
    'cloud_sync': False,
    'multi_user': False,
    'reporting': True,
    'visualization_3d': False,
    'barcode_generation': True,
    'material_database': True,
    'cost_tracking': True
}