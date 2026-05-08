@echo off
REM Build script for swat_skill standalone executable on Windows.
REM Creates a portable distribution that can run without Python installed.
REM
REM Usage: build.bat [--onefile] [--clean] [--web]
REM
REM Requirements: pip install pyinstaller

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

set ONEFILE=0
set CLEAN=0
set INCLUDE_WEB=0

REM Parse arguments
for %%a in (%*) do (
    if "%%a"=="--onefile" set ONEFILE=1
    if "%%a"=="--clean" set CLEAN=1
    if "%%a"=="--web" set INCLUDE_WEB=1
)

echo === swat_skill Build Script (Windows) ===
echo Options: ONEFILE=%ONEFILE%, CLEAN=%CLEAN%, INCLUDE_WEB=%INCLUDE_WEB%

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found
    exit /b 1
)

REM Check PyInstaller
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

REM Install web dependencies if requested
if "%INCLUDE_WEB%"=="1" (
    echo Installing web dependencies...
    pip install fastapi uvicorn websockets jinja2
)

REM Clean previous builds
if "%CLEAN%"=="1" (
    echo Cleaning previous builds...
    if exist build rd /s /q build
    if exist dist rd /s /q dist
)

echo Building executable...

if "%ONEFILE%"=="1" (
    REM Single file build
    pyinstaller --onefile --name swat_skill --console --clean --noconfirm ^
        --hidden-import rich --hidden-import rich.console --hidden-import rich.table ^
        --hidden-import prompt_toolkit --hidden-import prompt_toolkit.history ^
        --hidden-import yaml --hidden-import psycopg --hidden-import psycopg.pq ^
        --hidden-import psycopg_binary ^
        --hidden-import swat_skill --hidden-import swat_skill.config ^
        --hidden-import swat_skill.database.connection ^
        --hidden-import swat_skill.dispatcher.router ^
        --hidden-import swat_skill.skills.base ^
        --hidden-import swat_skill.skills.dbtop ^
        --hidden-import swat_skill.utils.formatter ^
        --collect-data rich --collect-data prompt_toolkit ^
        --collect-data psycopg --collect-data psycopg_binary ^
        --runtime-hook hooks\runtime_hook.py ^
        swat_skill\cli.py

    echo.
    echo Build complete! Single executable at: dist\swat_skill.exe
) else (
    REM Directory build
    pyinstaller swat_skill.spec --noconfirm

    echo.
    echo Build complete! Distribution at: dist\swat_skill\
)

REM Create README
echo Creating distribution README...
(
echo swat_skill - PostgreSQL Database CLI Agent
echo ============================================
echo.
echo This is a standalone executable that does not require Python.
echo.
echo Usage:
echo -------
echo swat_skill.exe setup       - Initial setup
echo swat_skill.exe             - Start interactive session
echo swat_skill.exe web         - Start web interface
echo.
echo Configuration:
echo ---------------
echo Stored in %%USERPROFILE%%\.swat_skill\config.yaml
echo.
echo Requirements:
echo -------------
echo - PostgreSQL client libraries (libpq.dll)
echo - Copy libpq.dll from PostgreSQL installation to same directory
echo.
echo Version: v1.8.0
) > dist\swat_skill\README.txt

echo.
echo === Build Summary ===
echo Distribution created at: dist\swat_skill\
echo.
echo To deploy:
echo 1. Copy dist\swat_skill\ directory to target machine
echo 2. Copy libpq.dll from PostgreSQL to the same directory
echo 3. Run: swat_skill.exe setup
echo 4. Run: swat_skill.exe

endlocal