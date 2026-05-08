#!/bin/bash
#
# Build script for swat_skill standalone executable.
# Creates a portable distribution that can run without Python installed.
#
# Usage:
#   ./build.sh [--onefile] [--clean]
#
# Options:
#   --onefile    Build as single executable file (larger but portable)
#   --clean      Clean build artifacts before building
#   --web        Include web dependencies (fastapi, uvicorn)
#
# Requirements:
#   pip install pyinstaller
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${0}")" && pwd)"
cd "$SCRIPT_DIR"

# Parse arguments
ONEFILE=false
CLEAN=false
INCLUDE_WEB=false

for arg in "$@"; do
    case $arg in
        --onefile) ONEFILE=true ;;
        --clean) CLEAN=true ;;
        --web) INCLUDE_WEB=true ;;
        *) echo "Unknown argument: $arg"; exit 1 ;;
    esac
done

echo "=== swat_skill Build Script ==="
echo "Options: ONEFILE=$ONEFILE, CLEAN=$CLEAN, INCLUDE_WEB=$INCLUDE_WEB"

# Check Python and PyInstaller
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 not found"
    exit 1
fi

# Activate virtual environment if exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Install PyInstaller if not installed
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "Installing PyInstaller..."
    pip install pyinstaller
fi

# Install web dependencies if requested
if [ "$INCLUDE_WEB" = true ]; then
    echo "Installing web dependencies..."
    pip install fastapi uvicorn websockets jinja2
fi

# Clean previous builds
if [ "$CLEAN" = true ]; then
    echo "Cleaning previous builds..."
    rm -rf build/ dist/
fi

# Build the executable
echo "Building executable..."

if [ "$ONEFILE" = true ]; then
    # Single file build (slower to start, easier to distribute)
    pyinstaller --onefile \
        --name swat_skill \
        --console \
        --clean \
        --noconfirm \
        --hidden-import rich \
        --hidden-import rich.console \
        --hidden-import rich.table \
        --hidden-import prompt_toolkit \
        --hidden-import prompt_toolkit.history \
        --hidden-import yaml \
        --hidden-import psycopg \
        --hidden-import psycopg.pq \
        --hidden-import psycopg_binary \
        --hidden-import swat_skill \
        --hidden-import swat_skill.config \
        --hidden-import swat_skill.database.connection \
        --hidden-import swat_skill.dispatcher.router \
        --hidden-import swat_skill.skills.base \
        --hidden-import swat_skill.skills.dbtop \
        --hidden-import swat_skill.utils.formatter \
        --collect-data rich \
        --collect-data prompt_toolkit \
        --collect-data psycopg \
        --collect-data psycopg_binary \
        --runtime-hook hooks/runtime_hook.py \
        swat_skill/cli.py

    echo ""
    echo "Build complete! Single executable at:"
    echo "  dist/swat_skill (Linux)"
    echo "  dist/swat_skill.exe (Windows)"
else
    # Directory build (faster to start, easier to debug)
    pyinstaller swat_skill.spec --noconfirm

    echo ""
    echo "Build complete! Distribution at:"
    echo "  dist/swat_skill/"
fi

# Create README for distribution
echo "Creating distribution README..."
cat > dist/swat_skill/README.txt << 'EOF'
swat_skill - PostgreSQL Database CLI Agent
============================================

This is a standalone executable that does not require Python to be installed.

Usage:
------
1. Run the executable:
   ./swat_skill setup       # Initial setup (configure database connection)
   ./swat_skill             # Start interactive session
   ./swat_skill web         # Start web interface

2. Connect to database:
   After running 'setup', you can start the interactive session.
   Or use command line options:
   ./swat_skill --host localhost --port 5432 --database mydb --user postgres

Configuration:
--------------
Configuration is stored in ~/.swat_skill/config.yaml

LLM Diagnostics:
-----------------
Set ANTHROPIC_API_KEY environment variable for LLM-powered diagnostics.

Requirements on target machine:
--------------------------------
- PostgreSQL client libraries (libpq)
- For Linux: apt install libpq5
- For Windows: PostgreSQL client DLLs should be in PATH or same directory

Troubleshooting:
----------------
If psycopg fails to load:
- Ensure PostgreSQL client libraries are installed
- Check LD_LIBRARY_PATH (Linux) or PATH (Windows)

Version: v1.8.0
EOF

# Create a launcher script for easier distribution
cat > dist/swat_skill/run.sh << 'EOF'
#!/bin/bash
# Launcher script for swat_skill

SCRIPT_DIR="$(cd "$(dirname "${0}")" && pwd)"

# Set library path for psycopg
export LD_LIBRARY_PATH="${SCRIPT_DIR}:${LD_LIBRARY_PATH}"

# Run the executable
exec "${SCRIPT_DIR}/swat_skill" "$@"
EOF
chmod +x dist/swat_skill/run.sh

echo ""
echo "=== Build Summary ==="
echo "Distribution created at: dist/swat_skill/"
echo ""
echo "To deploy to another machine:"
echo "1. Copy the entire dist/swat_skill/ directory"
echo "2. Ensure PostgreSQL client libraries are installed (libpq5 on Linux)"
echo "3. Run: ./swat_skill setup"
echo "4. Run: ./swat_skill"
echo ""
echo "For single-file distribution, use: ./build.sh --onefile"