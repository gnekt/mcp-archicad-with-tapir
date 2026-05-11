# MCP ArchiCAD with Tapir

Fork of [tapir-archicad-automation](https://github.com/ENZYME-APD/tapir-archicad-automation) with an MCP Server that connects Claude to ArchiCAD.

## Project Structure

- **mcp-server/** — The MCP server (Python). Main addition of this fork.
  - `server.py` — 109 MCP tools wrapping the Tapir JSON API
  - `pyproject.toml` — Package definition, depends on `mcp[cli]>=1.0.0`
- **archicad-addon/** — Tapir C++ Add-On source (upstream + our new commands)
  - `Sources/ElementCreationCommands.cpp/.hpp` — Element creation (includes our Walls, Beams, Roofs, Windows, Doors)
  - `Sources/ElementCommands.cpp` — Element query/modify (GetDetails, Move, Delete, Highlight, etc.)
  - `Sources/AddOnMain.cpp` — Command registration
  - `Sources/CommandBase.cpp/.hpp` — Base class and helper functions
- **builtin-scripts/** — Python automation scripts. `aclib/__init__.py` is the HTTP client library.
- **docs/archicad-addon/** — Interactive web docs. `command_definitions.js` has the full API schema.

## What We Added vs Upstream

### C++ Add-On (archicad-addon/Sources/)
5 new element creation commands (version 1.5.0):
- **CreateWalls** — begCoordinate, endCoordinate, height, thickness, offset, arcAngle (curved walls)
- **CreateBeams** — begCoordinate, endCoordinate, level, slantAngle, arcAngle
- **CreateRoofs** — polygon outline, level, slope angle, thickness, holes
- **CreateWindows** — placed in existing wall via wallId + objLocation, with width/height/sill
- **CreateDoors** — same pattern as windows

### MCP Server (mcp-server/server.py)
109 tools total. Key composite/analysis tools:
- `get_project_visual_overview` — comprehensive overview with stats, bounding box, preview images, room plans
- `analyze_project_size` — element count breakdown with bloat warnings
- `find_oversized_elements` — finds elements with abnormal bounding boxes

## Architecture

```
Claude <-> MCP Protocol <-> mcp-server/server.py <-> HTTP JSON <-> ArchiCAD (Tapir Add-On on port 19723)
```

## Key Conventions

- Tapir commands: `_run_tapir()` wraps `API.ExecuteAddOnCommand` with namespace `TapirCommand`
- Official Graphisoft commands: `_run_command()` directly
- Default endpoint: `http://127.0.0.1:19723`
- Elements identified by GUID: `{"elementId": {"guid": "..."}}`
- Coordinates in meters. X/Y horizontal, Z vertical.
- Element creation follows the `CreateElementsCommandBase` pattern: constructor(name, API_TypeID, arrayField) + GetInputParametersSchema() + SetTypeSpecificParameters()
- New commands registered in AddOnMain.cpp with version "1.5.0"

## Development

```bash
cd mcp-server
pip install -e .
python server.py  # starts MCP server on stdio
```

To test a single command against a running ArchiCAD:
```python
import sys; sys.path.insert(0, 'builtin-scripts')
import aclib
aclib.RunTapirCommand('GetAllElements', {})
```

## Upstream Sync

This fork tracks ENZYME-APD/tapir-archicad-automation. Changes are in `mcp-server/` (new) and `archicad-addon/Sources/` (extended). To sync:
```bash
git remote add upstream https://github.com/ENZYME-APD/tapir-archicad-automation.git
git fetch upstream
git merge upstream/main
```
