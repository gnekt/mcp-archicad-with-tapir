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

## Tutorial

What follows is a walkthrough of everything you can do with Claude and ArchiCAD. Every example is a real prompt you can type into Claude Desktop.

### First connection: see the project

The first thing to do when you connect Claude to an ArchiCAD project is to get an overview. Claude will count every element, measure the model, check libraries, and grab preview images.

**You say:**
> Dammi una panoramica completa del progetto

Claude calls `get_project_visual_overview` and returns:
- Project name, path, and teamwork status
- Story structure (basement, ground floor, first floor, ...)
- Total elements and breakdown by type (1200 Walls, 850 Objects, 340 Slabs, ...)
- Breakdown by floor (floor 0 has 40% of elements, floor 1 has 25%, ...)
- Full 3D bounding box of the model (the building is 45m wide, 32m deep, 18m tall)
- List of loaded libraries and hotlinks
- 3D preview images of sample elements (a wall, a slab, an object, a column)
- A room plan image if zones exist

This gives Claude enough context to advise you on anything.

### Analyze why a project is too heavy

Large ArchiCAD projects (10-20 GB) are a common problem. Claude can diagnose the cause.

**You say:**
> Il progetto pesa 18 GB, aiutami a capire perche'

Claude calls `analyze_project_size` and then digs deeper:

1. Counts elements by type. If you have 5000 Objects, that is probably the cause.
2. Calls `get_libraries` to check how many and how large the loaded libraries are.
3. Calls `get_hotlinks` to check for nested external references (hotlinks inside hotlinks multiply file size).
4. Calls `find_oversized_elements` to find elements with bounding boxes larger than 100 meters (imported at wrong scale, misplaced far from origin, or corrupted geometry).
5. Calls `get_gdl_parameters` on a sample of Object elements to check parametric complexity.

Claude then gives you a report like:
- "You have 5200 Object elements. 800 of them are from the library 'DetailComponents 29' which is known to be heavy."
- "There are 3 elements placed 2 km from the origin. They are probably imported wrong."
- "The hotlink 'Site_Model.pln' is nested 4 levels deep and appears 12 times in the project."

**You say:**
> Evidenzia in rosso gli elementi fuori scala

Claude calls `find_oversized_elements`, then calls `highlight_elements` with red color on the problematic elements. You see them light up in ArchiCAD's 3D view.

### Explore the project structure

**You say:**
> Quanti muri ci sono per piano?

Claude calls `get_elements_by_type` for Walls, then `get_details_of_elements` to get floor assignments, and returns a table:

| Floor | Walls |
| --- | --- |
| -1 (Basement) | 120 |
| 0 (Ground floor) | 340 |
| 1 (First floor) | 280 |
| 2 (Second floor) | 195 |

**You say:**
> Mostrami i layer usati nel progetto

Claude calls `get_attributes_by_type` with "Layer" and lists all layers with their names and visibility status.

**You say:**
> Quali zone/stanze ci sono al piano terra?

Claude calls `get_elements_by_type` for Zones, filters for floor 0, calls `get_details_of_elements` to get room names and numbers, and returns:

| Zone | Name | Number |
| --- | --- | --- |
| 1 | Living Room | 001 |
| 2 | Kitchen | 002 |
| 3 | Bathroom | 003 |
| 4 | Entrance | 004 |

**You say:**
> Fammi vedere la pianta della cucina

Claude calls `get_room_image` for the Kitchen zone and shows you a 2D plan image.

### Check element details and geometry

**You say:**
> Seleziona tutti i muri del piano terra e dimmi le loro dimensioni

Claude calls `get_elements_by_type` for Walls with filter `OnActualFloor`, then `get_details_of_elements`, and lists coordinates, heights, and thicknesses.

**You say:**
> Quanto e' alto l'edificio?

Claude calls `get_3d_bounding_boxes` on all elements and calculates: "The model extends from Z = -3.20m to Z = 12.60m. Total height: 15.80m."

**You say:**
> Ci sono collisioni tra i muri e le colonne?

Claude calls `get_elements_by_type` for Walls and Columns, then calls `get_collisions` between the two groups. Returns a list of clashing pairs with their GUIDs.

**You say:**
> Mostrami una preview 3D della colonna C-12

Claude calls `get_element_preview_image` with imageType "3D" and shows you a rendered thumbnail of that specific column.

### Create a simple structure

Claude can create architectural elements step by step.

**You say:**
> Crea una stanza rettangolare 5x4 metri al piano terra, alta 3 metri, con un solaio

Claude does:
1. Calls `get_stories` to find floor 0 elevation
2. Calls `create_walls` with 4 wall segments:
   - Wall 1: (0,0) to (5,0) - south wall
   - Wall 2: (5,0) to (5,4) - east wall
   - Wall 3: (5,4) to (0,4) - north wall
   - Wall 4: (0,4) to (0,0) - west wall
   - All with height 3.0 and thickness 0.3
3. Calls `create_slabs` with a rectangle polygon at level 0.0
4. Returns the GUIDs of all created elements

**You say:**
> Aggiungi una porta larga 90cm sul muro sud, al centro

Claude:
1. Knows the south wall goes from (0,0) to (5,0)
2. Calls `create_doors` with wallId of the south wall, objLocation 0.5 (center), width 0.9, height 2.1

**You say:**
> Metti due finestre sul muro nord, simmetriche

Claude:
1. Calls `create_windows` twice on the north wall, at objLocation 0.3 and 0.7, with width 1.2, height 1.5, lower (sill) 0.9

**You say:**
> Metti il tetto piatto a 3 metri

Claude calls `create_roofs` with the same polygon as the slab, at level 3.0, angle 0 (flat).

**You say:**
> Adesso inclina il tetto di 15 gradi

Claude calls `create_roofs` with angle 0.26 radians (15 degrees).

### Create structural elements

**You say:**
> Aggiungi 4 colonne agli angoli della stanza

Claude calls `create_columns` with coordinates at (0,0), (5,0), (5,4), (0,4) at z=0.

**You say:**
> Collega le colonne con travi

Claude calls `create_beams` between each pair of adjacent columns at the ceiling level.

### Work with properties and classifications

**You say:**
> Quali proprieta' hanno i muri del piano terra?

Claude calls `get_all_properties` to discover available properties, then `get_property_values_of_elements` on the walls, and lists all custom BIM properties with their values.

**You say:**
> Imposta la proprieta' "Fire Rating" a "REI 120" su tutti i muri portanti

Claude:
1. Finds the property ID for "Fire Rating"
2. Filters walls by structural property
3. Calls `set_property_values_of_elements` to set the value on all matching walls

**You say:**
> Quali classificazioni IFC hanno le colonne?

Claude calls `get_classifications_of_elements` on the columns and lists their IFC classes (IfcColumn, IfcMember, etc.).

### Manage layers and materials

**You say:**
> Crea un nuovo layer "AI_Generated" per gli elementi che creo con Claude

Claude calls `create_layers` with name "AI_Generated".

**You say:**
> Elencami tutti i materiali da costruzione usati nel progetto

Claude calls `get_attributes_by_type` with "BuildingMaterial" and lists all materials.

**You say:**
> Quali sono le proprieta' fisiche del calcestruzzo?

Claude calls `get_building_material_physical_properties` for the concrete material and returns thermal conductivity, density, heat capacity, etc.

### Work with favorites

**You say:**
> Quali preferiti ci sono per i muri?

Claude calls `get_favorites_by_type` with "Wall" and lists all saved wall configurations.

**You say:**
> Mostrami l'anteprima del preferito "Muro Esterno 38cm"

Claude calls `get_favorite_preview_image` and shows the thumbnail.

### Navigate and manage views

**You say:**
> Passa alla vista 3D

Claude calls `change_window` with "3DModel".

**You say:**
> Zoom su tutto il modello

Claude calls `fit_in_window`.

**You say:**
> Aggiorna tutti i disegni

Claude calls `update_drawings`.

### Highlight and select elements

**You say:**
> Evidenzia tutti gli Object del piano 2 in blu

Claude:
1. Calls `get_elements_by_type` for Object
2. Calls `filter_elements` with OnActualFloor (after switching to floor 2)
3. Calls `highlight_elements` with blue RGBA [0, 100, 255, 200] for each element

**You say:**
> Seleziona tutti i muri piu' corti di 1 metro

Claude:
1. Gets all walls
2. Gets their details (begCoordinate, endCoordinate)
3. Calculates length for each
4. Calls `change_selection` to select only the short ones

**You say:**
> Togli l'evidenziazione

Claude calls `highlight_elements` with an empty elements array to clear all highlights.

### Issue tracking and collaboration

**You say:**
> Crea una issue "Elementi fuori scala" e allega gli elementi problematici

Claude:
1. Calls `create_issue` with name "Elementi fuori scala"
2. Calls `find_oversized_elements` to get the problematic elements
3. Calls `attach_elements_to_issue` to link them
4. Calls `add_comment_to_issue` with a description of the problem

**You say:**
> Esporta tutte le issue in BCF

Claude calls `export_issues_to_bcf` and saves a .bcf file that you can share with other BIM tools.

### Import and export

**You say:**
> Esporta il progetto in IFC

Claude calls `ifc_file_operation` with method "save" and a file path.

**You say:**
> Importa il modello strutturale da questo file IFC

Claude calls `ifc_file_operation` with method "merge" to add the IFC model to the current project.

### Teamwork (BIMcloud)

If you work on a shared BIMcloud project:

**You say:**
> Ricevi le modifiche dal server

Claude calls `teamwork_receive`.

**You say:**
> Riserva tutti i muri del piano terra per la modifica

Claude calls `get_elements_by_type` for Walls on floor 0, then `reserve_elements`.

**You say:**
> Invia le mie modifiche

Claude calls `teamwork_send`.

### Design options

**You say:**
> Quali opzioni di progetto ci sono?

Claude calls `get_design_options`, `get_design_option_sets`, and `get_design_option_combinations` to show all design alternatives configured in the project.

### Real-time monitoring

**You say:**
> Avvisami quando qualcuno modifica un elemento

Claude calls `set_element_notification_client` to register for change notifications from ArchiCAD.

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
