#!/bin/bash
set -e

echo ""
echo "  ╔══════════════════════════════════════════╗"
echo "  ║   MCP ArchiCAD — Installer per macOS     ║"
echo "  ║   Claude + ArchiCAD via Tapir             ║"
echo "  ╚══════════════════════════════════════════╝"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MCP_SERVER="$SCRIPT_DIR/mcp-server/server.py"
CLAUDE_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
UV_DIR="$SCRIPT_DIR/.tools"
UV_BIN="$UV_DIR/uv"
ADDON_DIR="$SCRIPT_DIR/.addon"

# ── 1. Install uv (Python manager, no system Python needed) ──
echo "[1/5] Installazione runtime Python (uv)..."
if [ -f "$UV_BIN" ]; then
    echo "  Gia' installato."
else
    mkdir -p "$UV_DIR"
    curl -sSfL https://astral.sh/uv/install.sh | env INSTALLER_NO_MODIFY_PATH=1 UV_INSTALL_DIR="$UV_DIR" sh 2>&1 | tail -1
    if [ ! -f "$UV_BIN" ]; then
        echo "  ERRORE: impossibile scaricare uv. Controlla la connessione internet."
        exit 1
    fi
    echo "  Installato."
fi

# ── 2. Install MCP dependencies via uv ──
echo ""
echo "[2/5] Installazione dipendenze MCP server..."
cd "$SCRIPT_DIR/mcp-server"
"$UV_BIN" pip install --quiet -e . --python "$("$UV_BIN" python find 2>/dev/null || "$UV_BIN" python install 3.12 --quiet && "$UV_BIN" python find)" 2>&1 | tail -3
echo "  Fatto."

# ── 3. Configure Claude Desktop ──
echo ""
echo "[3/5] Configurazione Claude Desktop..."
UV_RUN="$UV_BIN"
JSON_CMD="$UV_RUN"
JSON_ARGS="run --with mcp[cli] python $MCP_SERVER"

mkdir -p "$(dirname "$CLAUDE_CONFIG")"

if [ -f "$CLAUDE_CONFIG" ]; then
    if grep -q "tapir-archicad" "$CLAUDE_CONFIG" 2>/dev/null; then
        echo "  Gia' configurato."
    else
        "$UV_BIN" run --with mcp[cli] python -c "
import json, sys
p = '$CLAUDE_CONFIG'
c = json.load(open(p))
c.setdefault('mcpServers', {})
c['mcpServers']['tapir-archicad'] = {
    'command': '$UV_RUN',
    'args': 'run --with mcp[cli] python $MCP_SERVER'.split()
}
json.dump(c, open(p, 'w'), indent=2)
print('  Aggiunto a Claude Desktop.')
" 2>/dev/null || echo "  ATTENZIONE: non riesco a modificare il config. Configuralo manualmente."
    fi
else
    cat > "$CLAUDE_CONFIG" << JSONEOF
{
  "mcpServers": {
    "tapir-archicad": {
      "command": "$UV_RUN",
      "args": ["run", "--with", "mcp[cli]", "python", "$MCP_SERVER"]
    }
  }
}
JSONEOF
    echo "  Configurazione creata."
fi

# ── 4. Download ArchiCAD Add-On ──
echo ""
echo "[4/5] Download Add-On ArchiCAD..."
echo ""
echo "  Quale versione di ArchiCAD usi?"
echo ""
echo "    1) ArchiCAD 25"
echo "    2) ArchiCAD 26"
echo "    3) ArchiCAD 27"
echo "    4) ArchiCAD 28"
echo "    5) ArchiCAD 29"
echo "    0) Salta (lo scarico dopo)"
echo ""
read -p "  Scegli [1-5, 0 per saltare]: " AC_CHOICE

AC_VERSION=""
case "$AC_CHOICE" in
    1) AC_VERSION=25 ;;
    2) AC_VERSION=26 ;;
    3) AC_VERSION=27 ;;
    4) AC_VERSION=28 ;;
    5) AC_VERSION=29 ;;
    *) echo "  Saltato. Potrai scaricarlo dopo da GitHub Releases." ;;
esac

if [ -n "$AC_VERSION" ]; then
    ADDON_URL="https://github.com/gnekt/mcp-archicad-with-tapir/releases/latest/download/TapirAddOn_AC${AC_VERSION}_Mac.zip"
    ADDON_ZIP="$ADDON_DIR/TapirAddOn_AC${AC_VERSION}_Mac.zip"
    mkdir -p "$ADDON_DIR"
    echo "  Scaricamento Add-On per ArchiCAD $AC_VERSION..."
    if curl -sSfL -o "$ADDON_ZIP" "$ADDON_URL" 2>/dev/null; then
        cd "$ADDON_DIR"
        unzip -qo "$ADDON_ZIP" 2>/dev/null
        echo "  Scaricato in: $ADDON_DIR/"
        echo ""
        echo "  Per installare in ArchiCAD:"
        echo "    1. Apri ArchiCAD"
        echo "    2. Vai in Options > Add-On Manager"
        echo "    3. Tab 'Edit List of Available Add-Ons'"
        echo "    4. Clicca 'Add' e seleziona il file .bundle in:"
        echo "       $ADDON_DIR/"
        echo "    5. Clicca OK"
    else
        echo "  Non riesco a scaricare — probabilmente la release non esiste ancora."
        echo "  Scaricalo manualmente da: https://github.com/gnekt/mcp-archicad-with-tapir/releases"
    fi
fi

# ── 5. Done ──
echo ""
echo "  ╔══════════════════════════════════════════╗"
echo "  ║         Installazione completata!         ║"
echo "  ╠══════════════════════════════════════════╣"
echo "  ║                                           ║"
echo "  ║  1. Installa l'Add-On in ArchiCAD         ║"
echo "  ║  2. Apri un progetto in ArchiCAD          ║"
echo "  ║  3. Apri Claude Desktop                   ║"
echo "  ║  4. Chiedi: 'Analizza il mio progetto'    ║"
echo "  ║                                           ║"
echo "  ╚══════════════════════════════════════════╝"
echo ""
