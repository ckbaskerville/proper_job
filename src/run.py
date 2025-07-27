"""Simple runner script for the application."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import and run main
from main import main

if __name__ == "__main__":
    sys.exit(main())