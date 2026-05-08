#!/usr/bin/env python3
"""
Standalone entry point for swat_skill.

This file is used by PyInstaller to create the standalone executable.
It uses absolute imports to avoid relative import issues when bundled.
"""

import sys
import os

# Ensure swat_skill package is importable when bundled
if getattr(sys, 'frozen', False):
    # PyInstaller bundle - add MEIPASS to path
    bundle_dir = sys._MEIPASS
    if bundle_dir not in sys.path:
        sys.path.insert(0, bundle_dir)

# Now import using absolute paths
from swat_skill.cli import main

if __name__ == "__main__":
    main()