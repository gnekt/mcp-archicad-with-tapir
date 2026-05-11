#!/bin/bash
set -e

echo "============================================"
echo "  MCP ArchiCAD with Tapir — Mac Installer"
echo "============================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MCP_SERVER="$SCRIPT_DIR/mcp-server/server.py"
CLAUDE_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"

# 1. Check Python
echo "[1/4] Checking Python..."
if ! command -v python3 &>/dev/null; then
    echo "ERROR: Python 3 not found. Install it from https://www.python.org/downloads/"
    exit 1
fi
PYVER=$(python3 --version)
echo "  Found $PYVER"

# 2. Install MCP dependencies
echo ""
echo "[2/4] Installing MCP server dependencies..."
cd "$SCRIPT_DIR/mcp-server"
pip3 install -e . --quiet 2>&1 | tail -3
echo "  Done."

# 3. Configure Claude Desktop
echo ""
echo "[3/4] Configuring Claude Desktop..."
PYTHON_PATH=$(which python3)

mkdir -p "$(dirname "$CLAUDE_CONFIG")"

if [ -f "$CLAUDE_CONFIG" ]; then
    if grep -q "tapir-archicad" "$CLAUDE_CONFIG" 2>/dev/null; then
        echo "  Already configured in Claude Desktop."
    else
        echo "  Claude Desktop config exists — adding tapir-archicad server."
        python3 -c "
import json, sys
config_path = sys.argv[1]
python_path = sys.argv[2]
server_path = sys.argv[3]
with open(config_path) as f:
    config = json.load(f)
if 'mcpServers' not in config:
    config['mcpServers'] = {}
config['mcpServers']['tapir-archicad'] = {
    'command': python_path,
    'args': [server_path]
}
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)
print('  Added tapir-archicad to Claude Desktop config.')
" "$CLAUDE_CONFIG" "$PYTHON_PATH" "$MCP_SERVER"
    fi
else
    cat > "$CLAUDE_CONFIG" << JSONEOF
{
  "mcpServers": {
    "tapir-archicad": {
      "command": "$PYTHON_PATH",
      "args": ["$MCP_SERVER"]
    }
  }
}
JSONEOF
    echo "  Created Claude Desktop config with tapir-archicad server."
fi

# 4. ArchiCAD Add-On instructions
echo ""
echo "[4/4] ArchiCAD Add-On"
echo ""
echo "  Download the Tapir Add-On for your ArchiCAD version:"
echo ""
echo "    AC25: https://github.com/gnekt/mcp-archicad-with-tapir/releases/latest/download/TapirAddOn_AC25_Mac.zip"
echo "    AC26: https://github.com/gnekt/mcp-archicad-with-tapir/releases/latest/download/TapirAddOn_AC26_Mac.zip"
echo "    AC27: https://github.com/gnekt/mcp-archicad-with-tapir/releases/latest/download/TapirAddOn_AC27_Mac.zip"
echo "    AC28: https://github.com/gnekt/mcp-archicad-with-tapir/releases/latest/download/TapirAddOn_AC28_Mac.zip"
echo "    AC29: https://github.com/gnekt/mcp-archicad-with-tapir/releases/latest/download/TapirAddOn_AC29_Mac.zip"
echo ""
echo "  Install in ArchiCAD:"
echo "    1. Unzip the downloaded file"
echo "    2. In ArchiCAD: Options > Add-On Manager"
echo "    3. Click 'Edit List of Available Add-Ons' tab"
echo "    4. Click 'Add' and browse to the .bundle file"
echo "    5. Click OK"
echo ""
echo "============================================"
echo "  Installation complete!"
echo ""
echo "  Next steps:"
echo "    1. Install the ArchiCAD Add-On (see above)"
echo "    2. Open ArchiCAD with a project"
echo "    3. Open Claude Desktop"
echo "    4. Ask Claude: 'Analizza il mio progetto ArchiCAD'"
echo "============================================"
