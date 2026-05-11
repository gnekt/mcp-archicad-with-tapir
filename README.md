# MCP ArchiCAD

[![Build](https://github.com/gnekt/mcp-archicad-with-tapir/actions/workflows/archicad_addon_build_check.yml/badge.svg)](https://github.com/gnekt/mcp-archicad-with-tapir/actions/workflows/archicad_addon_build_check.yml)

Connect Claude to ArchiCAD. Create buildings, analyze projects, find problems, modify elements, all through natural language.

> This project is a fork of [tapir-archicad-automation](https://github.com/ENZYME-APD/tapir-archicad-automation) by ENZYME APD. We extend Tapir with an MCP server and new element creation commands (Walls, Beams, Roofs, Windows, Doors) so that Claude can work directly inside ArchiCAD.

## What you can do

Open Claude Desktop and talk to your ArchiCAD project:

- "Analizza il progetto e dimmi perche' pesa 20 giga"
- "Quanti muri ci sono per piano?"
- "Crea 4 muri per fare una stanza 5x4 metri"
- "Metti una finestra al centro del muro nord"
- "Trova gli oggetti con dimensioni anomale"
- "Evidenzia in rosso tutti gli Object del piano 3"
- "Esporta il progetto in IFC"

Claude can see element previews, room plans, bounding boxes, and the full project structure. It has access to 109 tools covering the entire ArchiCAD API.

## How it works

```
Claude Desktop <-> MCP Protocol <-> MCP Server (Python) <-> HTTP JSON <-> ArchiCAD (Tapir Add-On)
                                                                |
                                                        localhost:19723
```

The MCP server translates Claude's tool calls into HTTP requests to the Tapir Add-On running inside ArchiCAD. ArchiCAD must be open with a project loaded.

## Quick start

### macOS

```bash
git clone https://github.com/gnekt/mcp-archicad-with-tapir.git
cd mcp-archicad-with-tapir
./install_mac.sh
```

### Windows

```
git clone https://github.com/gnekt/mcp-archicad-with-tapir.git
cd mcp-archicad-with-tapir
install_win.bat
```

The installer does everything automatically:

1. Downloads a Python runtime (uv) if needed. Nothing to install on your system.
2. Installs the MCP server dependencies.
3. Configures Claude Desktop to use the MCP server.
4. Asks which ArchiCAD version you have and downloads the Add-On.

After the installer finishes, add the Add-On in ArchiCAD:

1. Open ArchiCAD
2. Go to **Options > Add-On Manager**
3. Click the **Edit List of Available Add-Ons** tab
4. Click **Add** and select the downloaded file (`.apx` on Windows, `.bundle` on macOS)
5. Click **OK**

Then open Claude Desktop, open a project in ArchiCAD, and start talking.

## ArchiCAD Add-On download

If you prefer to download the Add-On manually:

| ArchiCAD version | Windows | macOS |
| --- | --- | --- |
| ArchiCAD 28 | [Download .apx](https://github.com/gnekt/mcp-archicad-with-tapir/releases/latest/download/TapirAddOn_AC28_Win.apx) | [Download .zip](https://github.com/gnekt/mcp-archicad-with-tapir/releases/latest/download/TapirAddOn_AC28_Mac.zip) |
| ArchiCAD 29 | [Download .apx](https://github.com/gnekt/mcp-archicad-with-tapir/releases/latest/download/TapirAddOn_AC29_Win.apx) | [Download .zip](https://github.com/gnekt/mcp-archicad-with-tapir/releases/latest/download/TapirAddOn_AC29_Mac.zip) |

## Available tools (109)

### Project
Get project info, story structure, hotlinks, geolocation. Open, save, close projects. Import/export IFC.

### Elements: query
Get all elements or filter by type (Wall, Column, Slab, Roof, Object, Zone, ...). Get the current selection. Filter by visibility, floor, editability.

### Elements: create
Create walls (straight or curved), columns, slabs, beams, roofs (flat or sloped), zones, objects (library parts), meshes, polylines, labels, groups. Place windows and doors inside existing walls.

### Elements: modify
Move elements by a 3D vector. Copy elements. Delete elements. Highlight elements with custom colors in the 3D view.

### Elements: geometry
Get full details (type, floor, layer, coordinates, dimensions). Get 3D bounding boxes. Get subelements of stairs, curtain walls, railings. Get connected elements. Detect collisions between element groups.

### GDL parameters
Read and write parametric object properties. This is key for analyzing why a project is heavy: complex GDL objects with many parameters are often the cause.

### Properties and classifications
Read and write custom BIM properties. Get and set IFC classifications. Create property groups and definitions.

### Attributes
Query and create layers, building materials, composites, surfaces. Get layer combinations. Get physical properties of materials.

### Libraries
List loaded libraries. Reload libraries. Add files to the embedded library.

### Images
Get 3D preview images of individual elements (base64 PNG). Get 2D plan images of rooms/zones.

### Navigator and views
Create details, worksheets, layouts, drawings. Set view options and 3D cut planes. Zoom to fit.

### Issues (BCF)
Create, delete, and manage issues. Add comments. Attach elements. Export and import BCF files.

### Analysis (high-level)
**analyze_project_size**: counts all elements by type and floor, flags heavy types (Object, Morph, Mesh), gives actionable recommendations.

**find_oversized_elements**: scans bounding boxes to find elements with abnormal dimensions (misplaced, corrupted, or imported at wrong scale).

**get_project_visual_overview**: comprehensive overview in one call. Returns project info, story structure, element statistics, full project bounding box (dimensions in meters), library info, hotlinks, preview images of representative elements, and room plan images.

## What we added to Tapir

This fork adds:

**MCP server** (`mcp-server/server.py`): 109 tools wrapping the complete Tapir JSON API, plus composite analysis tools.

**5 new C++ creation commands** (version 1.5.0):
- **CreateWalls**: straight or curved walls with height, thickness, offset
- **CreateBeams**: structural beams with level, slant angle, curve
- **CreateRoofs**: single-plane roofs from polygon outlines with slope angle
- **CreateWindows**: placed inside existing walls with sill height, width, height
- **CreateDoors**: placed inside existing walls with width, height

**Installers**: zero-prerequisite scripts for macOS and Windows.

## Requirements

- ArchiCAD 28 or 29
- Claude Desktop (macOS or Windows)
- Internet connection (for initial setup only)

## Documentation

- [Tapir JSON command reference](https://enzyme-apd.github.io/tapir-archicad-automation/archicad-addon)
- [Tapir GitHub wiki](https://github.com/ENZYME-APD/tapir-archicad-automation/wiki)
- [MCP server details](mcp-server/README.md)

## Credits

Built on top of [Tapir](https://github.com/ENZYME-APD/tapir-archicad-automation) by [ENZYME APD](https://github.com/ENZYME-APD). Tapir provides the ArchiCAD Add-On with 100+ JSON commands and the Grasshopper plugin.

## License

Same license as the upstream Tapir project. See [LICENSE](LICENSE).
