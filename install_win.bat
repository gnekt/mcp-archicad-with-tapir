@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

echo.
echo   ══════════════════════════════════════════
echo     MCP ArchiCAD — Installer per Windows
echo     Claude + ArchiCAD via Tapir
echo   ══════════════════════════════════════════
echo.

set "SCRIPT_DIR=%~dp0"
set "MCP_SERVER=%SCRIPT_DIR%mcp-server\server.py"
set "CLAUDE_CONFIG=%APPDATA%\Claude\claude_desktop_config.json"
set "UV_DIR=%SCRIPT_DIR%.tools"
set "UV_BIN=%UV_DIR%\uv.exe"
set "ADDON_DIR=%SCRIPT_DIR%.addon"

:: ── 1. Install uv (Python manager, no system Python needed) ──
echo [1/5] Installazione runtime Python (uv)...
if exist "%UV_BIN%" (
    echo   Gia' installato.
) else (
    mkdir "%UV_DIR%" 2>nul
    echo   Scaricamento uv...
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; $ProgressPreference = 'SilentlyContinue'; try { Invoke-WebRequest -Uri 'https://astral.sh/uv/install.ps1' -OutFile '%TEMP%\uv_install.ps1'; } catch { Write-Host 'ERRORE: impossibile scaricare uv. Controlla internet.'; exit 1 }"
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "$env:UV_INSTALL_DIR = '%UV_DIR%'; $env:INSTALLER_NO_MODIFY_PATH = '1'; & '%TEMP%\uv_install.ps1'"
    if not exist "%UV_BIN%" (
        echo   ERRORE: installazione uv fallita.
        pause
        exit /b 1
    )
    echo   Installato.
)

:: ── 2. Install Python via uv and MCP dependencies ──
echo.
echo [2/5] Installazione Python e dipendenze MCP...
"%UV_BIN%" python install 3.12 --quiet 2>nul
cd /d "%SCRIPT_DIR%mcp-server"
for /f "tokens=*" %%p in ('"%UV_BIN%" python find 2^>nul') do set "UV_PYTHON=%%p"
"%UV_BIN%" pip install --quiet -e . --python "%UV_PYTHON%" 2>nul
echo   Fatto.

:: ── 3. Configure Claude Desktop ──
echo.
echo [3/5] Configurazione Claude Desktop...

if not exist "%APPDATA%\Claude" mkdir "%APPDATA%\Claude"

:: Escape paths for JSON
set "JSON_UV=%UV_BIN:\=\\%"
set "JSON_SERVER=%MCP_SERVER:\=\\%"

if exist "%CLAUDE_CONFIG%" (
    findstr /c:"tapir-archicad" "%CLAUDE_CONFIG%" >nul 2>&1
    if !errorlevel! equ 0 (
        echo   Gia' configurato.
    ) else (
        echo   Configurazione esistente — aggiungo tapir-archicad...
        "%UV_BIN%" run --with mcp[cli] python -c "import json,sys;p=r'%CLAUDE_CONFIG%';c=json.load(open(p));c.setdefault('mcpServers',{});c['mcpServers']['tapir-archicad']={'command':r'%UV_BIN%','args':['run','--with','mcp[cli]','python',r'%MCP_SERVER%']};json.dump(c,open(p,'w'),indent=2);print('  Aggiunto.')" 2>nul
        if errorlevel 1 echo   ATTENZIONE: configurazione manuale necessaria.
    )
) else (
    (
        echo {
        echo   "mcpServers": {
        echo     "tapir-archicad": {
        echo       "command": "!JSON_UV!",
        echo       "args": ["run", "--with", "mcp[cli]", "python", "!JSON_SERVER!"]
        echo     }
        echo   }
        echo }
    ) > "%CLAUDE_CONFIG%"
    echo   Configurazione creata.
)

:: ── 4. Download ArchiCAD Add-On ──
echo.
echo [4/5] Download Add-On ArchiCAD...
echo.
echo   Quale versione di ArchiCAD usi?
echo.
echo     1) ArchiCAD 25
echo     2) ArchiCAD 26
echo     3) ArchiCAD 27
echo     4) ArchiCAD 28
echo     5) ArchiCAD 29
echo     0) Salta (lo scarico dopo)
echo.
set /p AC_CHOICE="  Scegli [1-5, 0 per saltare]: "

set "AC_VERSION="
if "%AC_CHOICE%"=="1" set "AC_VERSION=25"
if "%AC_CHOICE%"=="2" set "AC_VERSION=26"
if "%AC_CHOICE%"=="3" set "AC_VERSION=27"
if "%AC_CHOICE%"=="4" set "AC_VERSION=28"
if "%AC_CHOICE%"=="5" set "AC_VERSION=29"

if defined AC_VERSION (
    set "ADDON_URL=https://github.com/gnekt/mcp-archicad-with-tapir/releases/latest/download/TapirAddOn_AC!AC_VERSION!_Win.apx"
    set "ADDON_FILE=%ADDON_DIR%\TapirAddOn_AC!AC_VERSION!_Win.apx"
    if not exist "%ADDON_DIR%" mkdir "%ADDON_DIR%"
    echo   Scaricamento Add-On per ArchiCAD !AC_VERSION!...
    powershell -NoProfile -ExecutionPolicy Bypass -Command ^
        "$ProgressPreference = 'SilentlyContinue'; try { Invoke-WebRequest -Uri '!ADDON_URL!' -OutFile '!ADDON_FILE!'; Write-Host '  Scaricato.'; } catch { Write-Host '  Release non disponibile. Scarica da: https://github.com/gnekt/mcp-archicad-with-tapir/releases'; }"
    echo.
    echo   Per installare in ArchiCAD:
    echo     1. Apri ArchiCAD
    echo     2. Vai in Options ^> Add-On Manager
    echo     3. Tab 'Edit List of Available Add-Ons'
    echo     4. Clicca 'Add' e seleziona:
    echo        %ADDON_DIR%\TapirAddOn_AC!AC_VERSION!_Win.apx
    echo     5. Clicca OK
) else (
    echo   Saltato. Scaricalo da: https://github.com/gnekt/mcp-archicad-with-tapir/releases
)

:: ── 5. Done ──
echo.
echo   ══════════════════════════════════════════
echo          Installazione completata!
echo   ══════════════════════════════════════════
echo.
echo     1. Installa l'Add-On in ArchiCAD
echo     2. Apri un progetto in ArchiCAD
echo     3. Apri Claude Desktop
echo     4. Chiedi: "Analizza il mio progetto"
echo.
echo   ══════════════════════════════════════════
echo.
pause
