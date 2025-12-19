#!/bin/bash

# 1. IMPORTANT: Move terminal context to the folder containing this script
# (By default, .command files start in the user's Home directory)
cd "$(dirname "$0")"

# 2. Update the code
echo "--- Pulling latest changes ---"
git pull

# 3. Run the build
echo "--- Starting Build ---"
# Replace '/path/to/python' with your specific path
# (e.g., ./venv/bin/python3 if using a virtual environment inside the folder)
./env/bin/python build.py

# 4. Keep the window open so they can see if it worked
echo "--- Done ---"
read -p "Press Enter to close..."