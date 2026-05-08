"""
PyInstaller runtime hook for swat_skill.

Sets up the runtime environment for standalone executable.
"""

import sys
import os

# Set up the base directory for the frozen application
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    BASE_DIR = sys._MEIPASS
else:
    # Running as script
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Ensure data files are found
os.environ.setdefault('SWAT_SKILL_BASE_DIR', BASE_DIR)

# Add the base directory to the path
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Ensure psycopg can find its binary libraries
# This is critical for PostgreSQL connection
try:
    import psycopg
    # The binary should be in the same directory
    psycopg_binary_path = os.path.join(BASE_DIR, 'psycopg_binary')
    if os.path.exists(psycopg_binary_path):
        os.environ.setdefault('PSYCOPG_BINARY_PATH', psycopg_binary_path)
except ImportError:
    pass

# Set up history and config directories
config_dir = os.path.expanduser('~/.swat_skill')
if not os.path.exists(config_dir):
    os.makedirs(config_dir, exist_ok=True)

history_file = os.path.join(config_dir, 'history')
if not os.path.exists(history_file):
    open(history_file, 'a').close()