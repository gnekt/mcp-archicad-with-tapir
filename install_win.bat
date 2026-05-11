@echo off
setlocal enabledelayedexpansion

echo ============================================
echo   MCP ArchiCAD with Tapir — Win Installer
echo ============================================
echo.

set "SCRIPT_DIR=%~dp0"
set "MCP_SERVER=%SCRIPT_DIR%mcp-server\server.py"
set "CLAUDE_CONFIG=%APPDATA%\Claude\claude_desktop_config.json"

:: 1. Check Python
echo [1/4] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do echo   Found %%i

:: 2. Install MCP dependencies
echo.
echo [2/4] Installing MCP server dependencies...
cd /d "%SCRIPT_DIR%mcp-server"
pip install -e . --quiet 2>nul
echo   Done.

:: 3. Configure Claude Desktop
echo.
echo [3/4] Configuring Claude Desktop...

for /f "tokens=*" %%i in ('where python') do set "PYTHON_PATH=%%i"

if not exist "%APPDATA%\Claude" mkdir "%APPDATA%\Claude"

if exist "%CLAUDE_CONFIG%" (
    findstr /c:"tapir-archicad" "%CLAUDE_CONFIG%" >nul 2>&1
    if !errorlevel! equ 0 (
        echo   Already configured in Claude Desktop.
    ) else (
        echo   Claude Desktop config exists — adding tapir-archicad server.
        python -c "import json,sys;p=sys.argv;c=json.load(open(p[1]));c.setdefault('mcpServers',{});c['mcpServers']['tapir-archicad']={'command':p[2],'args':[p[3]]};json.dump(c,open(p[1],'w'),indent=2);print('  Added tapir-archicad to config.')" "%CLAUDE_CONFIG%" "%PYTHON_PATH%" "%MCP_SERVER%"
    )
) else (
    :: Escape backslashes for JSON
    set "JSON_PYTHON=!PYTHON_PATH:\=\\!"
    set "JSON_SERVER=!MCP_SERVER:\=\\!"
    (
        echo {
        echo   "mcpServers": {
        echo     "tapir-archicad": {
        echo       "command": "!JSON_PYTHON!",
        echo       "args": ["!JSON_SERVER!"]
        echo     }
        echo   }
        echo }
    ) > "%CLAUDE_CONFIG%"
    echo   Created Claude Desktop config with tapir-archicad server.
)

:: 4. ArchiCAD Add-On instructions
echo.
echo [4/4] ArchiCAD Add-On
echo.
echo   Download the Tapir Add-On for your ArchiCAD version:
echo.
echo     AC25: https://github.com/gnekt/mcp-archicad-with-tapir/releases/latest/download/TapirAddOn_AC25_Win.apx
echo     AC26: https://github.com/gnekt/mcp-archicad-with-tapir/releases/latest/download/TapirAddOn_AC26_Win.apx
echo     AC27: https://github.com/gnekt/mcp-archicad-with-tapir/releases/latest/download/TapirAddOn_AC27_Win.apx
echo     AC28: https://github.com/gnekt/mcp-archicad-with-tapir/releases/latest/download/TapirAddOn_AC28_Win.apx
echo     AC29: https://github.com/gnekt/mcp-archicad-with-tapir/releases/latest/download/TapirAddOn_AC29_Win.apx
echo.
echo   Install in ArchiCAD:
echo     1. Save the .apx file somewhere on your computer
echo     2. In ArchiCAD: Options ^> Add-On Manager
echo     3. Click 'Edit List of Available Add-Ons' tab
echo     4. Click 'Add' and browse to the .apx file
echo     5. Click OK
echo.
echo ============================================
echo   Installation complete!
echo.
echo   Next steps:
echo     1. Install the ArchiCAD Add-On (see above)
echo     2. Open ArchiCAD with a project
echo     3. Open Claude Desktop
echo     4. Ask Claude: 'Analizza il mio progetto ArchiCAD'
echo ============================================
echo.
pause
