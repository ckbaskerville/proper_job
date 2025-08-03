"""
Proper Job - Main Entry Point

This application provides a comprehensive solution for designing kitchen
cabinets and generating quotes with optimized material usage.
"""

import sys
import logging
import time
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent
# sys.path.insert(0, str(PROJECT_ROOT))

from src.config.constants import (
    APP_NAME,
    APP_VERSION,
    LOG_FILE,
    LOG_FORMAT,
    LOG_LEVEL
)

from src.ui.app import KitchenQuoteApp


def setup_logging() -> None:
    """Configure application logging."""
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format=LOG_FORMAT,
        handlers=[
            # File handler
            logging.FileHandler(log_dir / LOG_FILE, encoding='utf-8'),
            # Console handler
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Set levels for specific loggers
    logging.getLogger('PIL').setLevel(logging.WARNING)  # Reduce PIL verbosity
    logging.getLogger('matplotlib').setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")


def setup_error_handling() -> None:
    """Configure global error handling."""

    def handle_exception(exc_type, exc_value, exc_traceback):
        """Global exception handler."""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        logger = logging.getLogger(__name__)
        logger.critical(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback)
        )

        # Show error dialog , TODO: Understand and correct this
        if tk._default_root:
            messagebox.showerror(
                "Critical Error",
                f"An unexpected error occurred:\n\n{exc_type.__name__}: {exc_value}\n\n"
                "Please check the log file for details."
            )

    sys.excepthook = handle_exception


def check_dependencies() -> bool:
    """Check that all required dependencies are available.
     TODO: This will be built into an executable so may not need this as missing dependencies would cause build failure?

    Returns:
        True if all dependencies are satisfied
    """
    required_modules = [
        'matplotlib',
        'tkinter',
        'json',
        'dataclasses'
    ]

    missing = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)

    if missing:
        logger = logging.getLogger(__name__)
        logger.error(f"Missing required dependencies: {', '.join(missing)}")

        if tk._default_root:
            messagebox.showerror(
                "Missing Dependencies",
                f"The following required packages are missing:\n\n"
                f"{', '.join(missing)}\n\n"
                f"Please install them using pip."
            )
        return False

    return True


def check_resources() -> bool:
    """Check that required resource files exist.

    Returns:
        True if all resources are available
    """
    from src.config.constants import (
        RUNNERS_FILE,
        MATERIALS_FILE,
        HINGES_FILE,
        LABOR_COSTS_FILE,
        DBC_DRAWERS_OAK_FILE,
        DBC_DRAWERS_WALNUT_FILE
    )

    required_files = [
        RUNNERS_FILE,
        MATERIALS_FILE,
        HINGES_FILE,
        LABOR_COSTS_FILE,
        DBC_DRAWERS_OAK_FILE,
        DBC_DRAWERS_WALNUT_FILE
    ]

    missing = []
    for file_path in required_files:
        if not file_path.exists():
            missing.append(str(file_path))

    if missing:
        logger = logging.getLogger(__name__)
        logger.error(f"Missing required resource files: {missing}")

        if tk._default_root:
            messagebox.showerror(
                "Missing Resources",
                f"The following required resource files are missing:\n\n"
                f"{chr(10).join(missing)}\n\n"
                f"Please ensure all resource files are in the 'resources' directory."
            )
        return False

    return True


def create_application() -> tk.Tk:
    """Create and configure the main application window.

    Returns:
        Configured Tkinter root window
    """
    # Create root window
    root = tk.Tk()

    # Hide window during setup
    root.withdraw()

    # Configure window
    root.title(f"{APP_NAME} v{APP_VERSION}")

    # Set window icon (if available)
    icon_path = PROJECT_ROOT / "resources" / "icon.ico"
    if icon_path.exists():
        try:
            root.iconbitmap(str(icon_path))
        except Exception as e:
            logging.warning(f"Could not set window icon: {e}")

    # Configure style
    # style = ttk.Style(root)
    # ThemeManager.apply_theme(style, 'dark')

    # Set minimum window size
    root.minsize(800, 600)

    # Center window on screen - TODO: Maximise window instead?
    root.update_idletasks()
    width = root.winfo_reqwidth()
    height = root.winfo_reqheight()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"+{x}+{y}")

    return root


def main() -> int:
    """Main application entry point.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Setup logging first
        setup_logging()
        logger = logging.getLogger(__name__)

        # Setup error handling
        setup_error_handling()

        # Create initial Tk instance for error dialogs
        initial_root = tk.Tk()
        initial_root.withdraw()

        # Check dependencies
        if not check_dependencies():
            return 1

        # Check resources
        # if not check_resources():
        #     return 2

        # Destroy initial root
        initial_root.destroy()

        # Create application
        logger.info("Creating application window")
        root = create_application()

        # Initialize application
        logger.info("Initializing application")
        app = KitchenQuoteApp(root)

        # Show window
        root.deiconify()

        # Handle window close
        def on_closing():
            """Handle window close event."""
            result = messagebox.askyesnocancel(
                "Confirm Exit",
                "Do you want to save your work before exiting?"
            )

            if result is None:  # Cancel
                return
            elif result:  # Yes - save
                # Trigger save in app
                try:
                    app._save_project()
                except Exception as e:
                    logger.error(f"Error saving on exit: {e}")
                    if not messagebox.askyesno(
                            "Save Error",
                            "Failed to save project. Exit anyway?"
                    ):
                        return

            logger.info("Application closing")
            root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_closing)

        # Start application
        logger.info("Starting main event loop")
        root.mainloop()

        logger.info("Application terminated normally")
        return 0

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.exception(f"Fatal error in main {e}")
        time.sleep(100)

        # Try to show error dialog
        try:
            messagebox.showerror(
                "Fatal Error",
                f"A fatal error occurred:\n\n{type(e).__name__}: {e}\n\n"
                "The application will now exit."
            )
            time.sleep(100)
        except:
            pass

        return 99


if __name__ == "__main__":
    # Run application and exit with return code
    sys.exit(main())


# Alternative: Simple entry point for development
def run_dev():
    """Run application in development mode with additional debugging."""
    import os

    # Enable debug logging
    os.environ['PYTHONASYNCIODEBUG'] = '1'
    logging.getLogger().setLevel(logging.DEBUG)

    # Run with debug flag
    sys.exit(main())


# For running with: python -m main
if __name__ == "__main__":
    sys.exit(main())