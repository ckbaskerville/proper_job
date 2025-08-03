"""Path configuration and management."""

from pathlib import Path
from typing import Optional, List
import os
import platform


class PathConfig:
    """Centralized path configuration."""

    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize path configuration.

        Args:
            base_dir: Base directory for the application
        """
        self.base_dir = base_dir or Path(__file__).parent.parent
        self._setup_paths()

    def _setup_paths(self) -> None:
        """Setup all application paths."""
        # Main directories
        self.resources_dir = self.base_dir / "resources"
        self.data_dir = self.base_dir / "data"
        self.logs_dir = self.base_dir / "logs"
        self.temp_dir = self.base_dir / "temp"
        self.reports_dir = self.base_dir / "reports"
        self.backups_dir = self.base_dir / "backups"

        # User directories
        self.user_data_dir = self._get_user_data_dir()
        self.user_config_dir = self.user_data_dir / "config"
        self.user_projects_dir = self.user_data_dir / "projects"
        self.user_templates_dir = self.user_data_dir / "templates"

        # Resource files
        self.runners_file = self.resources_dir / "runners.json"
        self.materials_file = self.resources_dir / "sheet_material.json"
        self.labor_costs_file = self.resources_dir / "labour_costs.json"
        self.dbc_drawers_walnut_file = self.resources_dir / "DBC_drawers_walnut.json"
        self.dbc_drawers_oak_file = self.resources_dir / "DBC_drawers_oak.json"
        self.hinges_file = self.resources_dir / "hinges.json"
        self.icon_file = self.resources_dir / "icon.ico"
        self.logo_file = self.resources_dir / "logo.png"

        # Configuration files
        self.settings_file = self.user_config_dir / "settings.json"
        self.recent_projects_file = self.user_config_dir / "recent_projects.json"
        self.custom_materials_file = self.user_config_dir / "custom_materials.json"
        self.shortcuts_file = self.user_config_dir / "shortcuts.json"

        # Create directories if they don't exist
        self._ensure_directories()

    def _get_user_data_dir(self) -> Path:
        """Get platform-specific user data directory."""
        app_name = "ProperJob"

        system = platform.system()
        if system == "Windows":
            base = os.environ.get('APPDATA', '~')
            return Path(base).expanduser() / app_name
        elif system == "Darwin":  # macOS
            return Path("~/Library/Application Support").expanduser() / app_name
        else:  # Linux and others
            base = os.environ.get('XDG_DATA_HOME', '~/.local/share')
            return Path(base).expanduser() / app_name

    def _ensure_directories(self) -> None:
        """Ensure all directories exist."""
        directories = [
            self.data_dir,
            self.logs_dir,
            self.temp_dir,
            self.reports_dir,
            self.backups_dir,
            self.user_data_dir,
            self.user_config_dir,
            self.user_projects_dir,
            self.user_templates_dir
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def get_temp_file(self, prefix: str = "tmp", suffix: str = "") -> Path:
        """Get a temporary file path.

        Args:
            prefix: File prefix
            suffix: File suffix

        Returns:
            Path to temporary file
        """
        import tempfile
        fd, path = tempfile.mkstemp(
            prefix=prefix,
            suffix=suffix,
            dir=str(self.temp_dir)
        )
        os.close(fd)
        return Path(path)

    def get_backup_file(self, original_file: Path) -> Path:
        """Get backup file path for an original file.

        Args:
            original_file: Original file path

        Returns:
            Backup file path
        """
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{original_file.stem}_{timestamp}{original_file.suffix}"
        return self.backups_dir / backup_name

    def clean_temp_files(self, max_age_days: int = 7) -> int:
        """Clean old temporary files.

        Args:
            max_age_days: Maximum age of files to keep

        Returns:
            Number of files deleted
        """
        import time

        count = 0
        max_age_seconds = max_age_days * 24 * 60 * 60
        current_time = time.time()

        for file in self.temp_dir.iterdir():
            if file.is_file():
                file_age = current_time - file.stat().st_mtime
                if file_age > max_age_seconds:
                    try:
                        file.unlink()
                        count += 1
                    except Exception:
                        pass

        return count

    def get_report_filename(self, report_type: str, extension: str = ".pdf") -> Path:
        """Get a filename for a report.

        Args:
            report_type: Type of report
            extension: File extension

        Returns:
            Report file path
        """
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{report_type}_{timestamp}{extension}"
        return self.reports_dir / filename

    def find_resource_file(self, filename: str) -> Optional[Path]:
        """Find a resource file by name.

        Args:
            filename: Name of file to find

        Returns:
            Path to file or None if not found
        """
        # Search in multiple locations
        search_paths = [
            self.resources_dir,
            self.user_data_dir,
            self.base_dir
        ]

        for directory in search_paths:
            path = directory / filename
            if path.exists():
                return path

        return None

    def list_project_templates(self) -> List[Path]:
        """List available project templates.

        Returns:
            List of template file paths
        """
        templates = []

        # Built-in templates
        builtin_templates = self.resources_dir / "templates"
        if builtin_templates.exists():
            templates.extend(builtin_templates.glob("*.pjb"))

        # User templates
        if self.user_templates_dir.exists():
            templates.extend(self.user_templates_dir.glob("*.pjb"))

        return sorted(templates)