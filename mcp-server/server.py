"""
Tapir ArchiCAD MCP Server

Connects Claude to a running ArchiCAD instance via the Tapir Add-On JSON API.
Exposes 90+ tools for creating, querying, modifying, and analyzing ArchiCAD projects.

Prerequisites:
  - ArchiCAD running with Tapir Add-On installed
  - Default endpoint: http://127.0.0.1:19723

Usage:
  mcp install server.py
  # or
  python server.py
"""

import json
import urllib.request
import urllib.error
from typing import Any
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "Tapir ArchiCAD",
    instructions="""You are connected to a live ArchiCAD instance via the Tapir Add-On.
You can create buildings, analyze projects, modify elements, and manage every aspect of an ArchiCAD project.

COORDINATE SYSTEM: ArchiCAD uses meters. X/Y are horizontal, Z is vertical (height).
ELEMENTS: Every element has a GUID. Use GetAllElements or GetElementsByType to discover them.
STORIES: Buildings have stories (floors). Index 0 = ground floor, negative = basement.
LAYERS: Elements belong to layers. Use GetAttributesByType with 'Layer' to list them.

WORKFLOW FOR CREATING A BUILDING:
1. GetProjectInfo to understand current state
2. GetStories / SetStories to define floor structure
3. Create structural elements: walls, columns, slabs, roofs
4. Add openings: windows, doors (via CreateObjects with library parts)
5. Create zones for rooms
6. Set properties and classifications

WORKFLOW FOR ANALYZING A HEAVY PROJECT:
1. GetAllElements to count total elements
2. GetElementsByType for each type to find which dominates
3. Get3DBoundingBoxes to find oversized elements
4. GetGDLParametersOfElements on Objects to check parametric complexity
5. GetLibraries to check loaded library sizes
6. GetHotlinks to find external references
7. GetComponentsOfElements for composite walls/slabs layer count

TIPS:
- Elements of type 'Object' are library parts (furniture, fixtures) — often the biggest bloat source
- Morph elements with many vertices are very heavy
- Hotlinks can multiply file size if nested deeply
- Use HighlightElements to visually show the user which elements you found problematic
""",
)

HOST = "http://127.0.0.1"
PORT = 19723


def _run_command(command: str, parameters: dict | None = None) -> Any:
    if parameters is None:
        parameters = {}
    connection = urllib.request.Request(f"{HOST}:{PORT}")
    connection.add_header("Content-Type", "application/json")
    request_data = {"command": command, "parameters": parameters}
    try:
        response = urllib.request.urlopen(
            connection, json.dumps(request_data).encode("utf8"), timeout=120
        )
        result = json.loads(response.read())
    except urllib.error.URLError as e:
        return {"error": f"Cannot connect to ArchiCAD at {HOST}:{PORT}. Is ArchiCAD running with Tapir Add-On? Details: {e}"}
    except Exception as e:
        return {"error": str(e)}
    if "error" in result and result["error"]:
        return {"error": result["error"]}
    if result.get("succeeded") and "result" in result:
        return result["result"]
    return result


def _run_tapir(command: str, parameters: dict | None = None) -> Any:
    if parameters is None:
        parameters = {}
    result = _run_command(
        "API.ExecuteAddOnCommand",
        {
            "addOnCommandId": {
                "commandNamespace": "TapirCommand",
                "commandName": command,
            },
            "addOnCommandParameters": parameters,
        },
    )
    if isinstance(result, dict) and "error" in result:
        return result
    if isinstance(result, dict) and "addOnCommandResponse" in result:
        resp = result["addOnCommandResponse"]
        if isinstance(resp, dict) and "error" in resp:
            return {"error": resp["error"]}
        return resp
    return result


# ============================================================================
# APPLICATION COMMANDS
# ============================================================================


@mcp.tool()
def get_addon_version() -> dict:
    """Get the version of the Tapir Add-On installed in ArchiCAD."""
    return _run_tapir("GetAddOnVersion")


@mcp.tool()
def get_archicad_location() -> dict:
    """Get the filesystem location of the running ArchiCAD executable."""
    return _run_tapir("GetArchicadLocation")


@mcp.tool()
def get_current_window_type() -> dict:
    """Get the type of the currently active window in ArchiCAD (FloorPlan, 3DModel, Section, etc.)."""
    return _run_tapir("GetCurrentWindowType")


@mcp.tool()
def change_window(window_type: str, database_id: str | None = None) -> dict:
    """Change the active ArchiCAD window.

    Args:
        window_type: Type of window — FloorPlan, Section, Elevation, InteriorElevation, Detail, Worksheet, Layout, 3DModel, DocumentFrom3D
        database_id: Optional database GUID for the specific view
    """
    params: dict = {"windowType": window_type}
    if database_id:
        params["databaseId"] = {"guid": database_id}
    return _run_tapir("ChangeWindow", params)


# ============================================================================
# PROJECT COMMANDS
# ============================================================================


@mcp.tool()
def get_project_info() -> dict:
    """Get info about the current project: name, location, path, teamwork status. Call this first to understand what project is open."""
    return _run_tapir("GetProjectInfo")


@mcp.tool()
def get_project_info_fields() -> dict:
    """Get ALL project info fields (custom metadata like client name, project number, etc.)."""
    return _run_tapir("GetProjectInfoFields")


@mcp.tool()
def set_project_info_field(field_id: str, value: str) -> dict:
    """Set a project info field value.

    Args:
        field_id: The ID of the project info field
        value: The new value
    """
    return _run_tapir("SetProjectInfoField", {"projectInfoId": field_id, "projectInfoValue": value})


@mcp.tool()
def get_stories() -> dict:
    """Get the story/floor structure of the project. Returns first/last story index, current story, and details of each story (name, level height)."""
    return _run_tapir("GetStories")


@mcp.tool()
def set_stories(stories: list[dict]) -> dict:
    """Set the story structure. Each story needs: index (int), floorId (optional), name (str), elevation (float in meters), height (float in meters).

    Args:
        stories: Array of story definitions, e.g. [{"index": -1, "name": "Basement", "elevation": -3.0, "height": 3.0}, {"index": 0, "name": "Ground Floor", "elevation": 0.0, "height": 3.2}]
    """
    return _run_tapir("SetStories", {"stories": stories})


@mcp.tool()
def get_hotlinks() -> dict:
    """Get all hotlink (external reference) modules and their file paths. Hotlinks are a common cause of large file sizes due to nesting."""
    return _run_tapir("GetHotlinks")


@mcp.tool()
def open_project(project_file_path: str) -> dict:
    """Open an ArchiCAD project file (.pln, .pla).

    Args:
        project_file_path: Full filesystem path to the project file
    """
    return _run_tapir("OpenProject", {"projectFilePath": project_file_path})


@mcp.tool()
def save_project() -> dict:
    """Save the currently open project."""
    return _run_tapir("SaveProject")


@mcp.tool()
def get_geo_location() -> dict:
    """Get the geographic location of the project (latitude, longitude, altitude, north direction, survey point, CRS)."""
    return _run_tapir("GetGeoLocation")


@mcp.tool()
def set_geo_location(
    longitude: float | None = None,
    latitude: float | None = None,
    altitude: float | None = None,
    north: float | None = None,
) -> dict:
    """Set the geographic location of the project.

    Args:
        longitude: Longitude in degrees
        latitude: Latitude in degrees
        altitude: Altitude in meters
        north: North direction in radians
    """
    loc = {}
    if longitude is not None:
        loc["longitude"] = longitude
    if latitude is not None:
        loc["latitude"] = latitude
    if altitude is not None:
        loc["altitude"] = altitude
    if north is not None:
        loc["north"] = north
    return _run_tapir("SetGeoLocation", {"projectLocation": loc})


@mcp.tool()
def ifc_file_operation(method: str, ifc_file_path: str, file_type: str = "ifc") -> dict:
    """Import/export IFC files.

    Args:
        method: 'save' to export, 'open' to import, 'merge' to merge
        ifc_file_path: Path to the IFC file
        file_type: ifc, ifcxml, ifczip, or ifcxmlzip
    """
    return _run_tapir("IFCFileOperation", {"method": method, "ifcFilePath": ifc_file_path, "fileType": file_type})


# ============================================================================
# ELEMENT QUERY COMMANDS
# ============================================================================


@mcp.tool()
def get_all_elements(filters: list[str] | None = None) -> dict:
    """Get identifiers (GUIDs) of ALL elements in the project. Use filters to narrow results.

    Args:
        filters: Optional filter list. Values: IsEditable, IsVisibleByLayer, IsVisibleByRenovation, IsVisibleByStructureDisplay, IsVisibleIn3D, OnActualFloor, OnActualLayout, InMyWorkspace, IsIndependent, InCroppedView, HasAccessRight, IsOverriddenByRenovation
    """
    params = {}
    if filters:
        params["filters"] = filters
    return _run_tapir("GetAllElements", params)


@mcp.tool()
def get_elements_by_type(element_type: str, filters: list[str] | None = None) -> dict:
    """Get all elements of a specific type. This is the primary way to find elements.

    Args:
        element_type: Wall, Column, Beam, Slab, Roof, Shell, Stair, Railing, Window, Door, Object, Lamp, Skylight, Opening, CurtainWall, Morph, Mesh, Zone, Dimension, Text, Label, Hatch, Line, PolyLine, Arc, Circle, Spline, Drawing, Detail, Elevation, Section, Hotlink, Group, etc.
        filters: Optional filter list (same as get_all_elements)
    """
    params: dict = {"elementType": element_type}
    if filters:
        params["filters"] = filters
    return _run_tapir("GetElementsByType", params)


@mcp.tool()
def get_selected_elements() -> dict:
    """Get the currently selected elements in ArchiCAD. Useful to work with what the user has manually selected."""
    return _run_tapir("GetSelectedElements")


@mcp.tool()
def change_selection(
    add_elements: list[dict] | None = None,
    remove_elements: list[dict] | None = None,
) -> dict:
    """Add or remove elements from the current selection in ArchiCAD.

    Args:
        add_elements: Elements to add to selection, e.g. [{"elementId": {"guid": "..."}}]
        remove_elements: Elements to remove from selection
    """
    params = {}
    if add_elements:
        params["addElementsToSelection"] = add_elements
    if remove_elements:
        params["removeElementsFromSelection"] = remove_elements
    return _run_tapir("ChangeSelectionOfElements", params)


@mcp.tool()
def filter_elements(elements: list[dict], filters: list[str]) -> dict:
    """Filter a list of elements by criteria.

    Args:
        elements: Array of element references [{"elementId": {"guid": "..."}}]
        filters: Filter criteria: IsEditable, IsVisibleByLayer, IsVisibleIn3D, OnActualFloor, etc.
    """
    return _run_tapir("FilterElements", {"elements": elements, "filters": filters})


# ============================================================================
# ELEMENT DETAILS & GEOMETRY
# ============================================================================


@mcp.tool()
def get_details_of_elements(elements: list[dict]) -> dict:
    """Get full details of elements: type, ID, floor, layer, draw order, and type-specific geometry (coordinates, dimensions, etc.).

    Args:
        elements: Array of element references [{"elementId": {"guid": "..."}}]
    """
    return _run_tapir("GetDetailsOfElements", {"elements": elements})


@mcp.tool()
def set_details_of_elements(elements_with_details: list[dict]) -> dict:
    """Modify element details (floor, layer, draw order, type-specific geometry).

    Args:
        elements_with_details: Array of {elementId: {guid: "..."}, details: {floorIndex: N, layerIndex: N, typeSpecificDetails: {...}}}
    """
    return _run_tapir("SetDetailsOfElements", {"elementsWithDetails": elements_with_details})


@mcp.tool()
def get_3d_bounding_boxes(elements: list[dict]) -> dict:
    """Get 3D bounding boxes (xMin, xMax, yMin, yMax, zMin, zMax) for elements. Essential for finding oversized or misplaced elements.

    Args:
        elements: Array of element references [{"elementId": {"guid": "..."}}]
    """
    return _run_tapir("Get3DBoundingBoxes", {"elements": elements})


@mcp.tool()
def get_subelements(elements: list[dict]) -> dict:
    """Get subelements of hierarchical elements (CurtainWall segments/frames/panels, Stair risers/treads, Railing parts, Beam/Column segments).

    Args:
        elements: Array of parent element references
    """
    return _run_tapir("GetSubelementsOfHierarchicalElements", {"elements": elements})


@mcp.tool()
def get_connected_elements(elements: list[dict], connected_element_type: str) -> dict:
    """Get elements connected to the given elements (e.g., windows connected to walls).

    Args:
        elements: Array of element references
        connected_element_type: The type of connected elements to find (Wall, Window, Door, etc.)
    """
    return _run_tapir("GetConnectedElements", {"elements": elements, "connectedElementType": connected_element_type})


@mcp.tool()
def get_zone_boundaries(zone_element_id: str) -> dict:
    """Get boundaries of a zone/room — connected walls, neighbouring zones, boundary geometry.

    Args:
        zone_element_id: GUID of the zone element
    """
    return _run_tapir("GetZoneBoundaries", {"zoneElementId": {"guid": zone_element_id}})


@mcp.tool()
def get_collisions(
    elements_group1: list[dict],
    elements_group2: list[dict],
    volume_tolerance: float = 0.001,
    perform_surface_check: bool = False,
    surface_tolerance: float = 0.001,
) -> dict:
    """Detect spatial collisions/clashes between two groups of elements.

    Args:
        elements_group1: First group of elements
        elements_group2: Second group of elements
        volume_tolerance: Minimum intersection volume to count as collision (m³)
        perform_surface_check: Also check surface intersections
        surface_tolerance: Minimum intersection surface to count (m²)
    """
    return _run_tapir(
        "GetCollisions",
        {
            "elementsGroup1": elements_group1,
            "elementsGroup2": elements_group2,
            "settings": {
                "volumeTolerance": volume_tolerance,
                "performSurfaceCheck": perform_surface_check,
                "surfaceTolerance": surface_tolerance,
            },
        },
    )


# ============================================================================
# ELEMENT VISUAL FEEDBACK
# ============================================================================


@mcp.tool()
def highlight_elements(
    elements: list[dict],
    colors: list[list[int]],
    wireframe_3d: bool = False,
    non_highlighted_color: list[int] | None = None,
) -> dict:
    """Highlight elements in ArchiCAD with colors. Pass empty elements array to clear highlights.
    This is very useful to SHOW the user which elements are problematic.

    Args:
        elements: Elements to highlight [{"elementId": {"guid": "..."}}]
        colors: RGBA colors for each element [[255,0,0,255], [0,255,0,255], ...]. One per element.
        wireframe_3d: Show non-highlighted elements as wireframe in 3D
        non_highlighted_color: Optional RGBA color for non-highlighted elements [128,128,128,64]
    """
    params: dict = {"elements": elements, "highlightedColors": colors}
    if wireframe_3d:
        params["wireframe3D"] = True
    if non_highlighted_color:
        params["nonHighlightedColor"] = non_highlighted_color
    return _run_tapir("HighlightElements", params)


# ============================================================================
# ELEMENT MODIFICATION
# ============================================================================


@mcp.tool()
def move_elements(elements_with_vectors: list[dict]) -> dict:
    """Move elements by a 3D vector. Can also copy elements.

    Args:
        elements_with_vectors: Array of {elementId: {guid: "..."}, moveVector: {x: 0, y: 0, z: 3.0}, copy: false}
    """
    return _run_tapir("MoveElements", {"elementsWithMoveVectors": elements_with_vectors})


@mcp.tool()
def delete_elements(elements: list[dict]) -> dict:
    """Delete elements from the project. WARNING: This is destructive!

    Args:
        elements: Elements to delete [{"elementId": {"guid": "..."}}]
    """
    return _run_tapir("DeleteElements", {"elements": elements})


# ============================================================================
# GDL PARAMETERS (Library Part Objects)
# ============================================================================


@mcp.tool()
def get_gdl_parameters(elements: list[dict]) -> dict:
    """Get all GDL parameters of elements (name, type, value, display name, possible values).
    GDL parameters define the shape, dimensions, and behavior of library part objects.
    Heavy or complex GDL objects are often the cause of large file sizes.

    Args:
        elements: Array of element references (typically Object, Window, Door, Lamp, Skylight types)
    """
    return _run_tapir("GetGDLParametersOfElements", {"elements": elements})


@mcp.tool()
def set_gdl_parameters(elements_with_params: list[dict]) -> dict:
    """Set GDL parameters on elements. Parameters can be set by name or index.

    Args:
        elements_with_params: Array of {elementId: {guid: "..."}, gdlParameters: [{name: "paramName", value: newValue}]}
    """
    return _run_tapir("SetGDLParametersOfElements", {"elementsWithGDLParameters": elements_with_params})


# ============================================================================
# CLASSIFICATIONS
# ============================================================================


@mcp.tool()
def get_classifications_of_elements(elements: list[dict], classification_system_ids: list[dict]) -> dict:
    """Get element classifications (IFC, custom classification systems).

    Args:
        elements: Array of element references
        classification_system_ids: Array of classification system IDs [{"classificationSystemId": {"guid": "..."}}]
    """
    return _run_tapir(
        "GetClassificationsOfElements",
        {"elements": elements, "classificationSystemIds": classification_system_ids},
    )


@mcp.tool()
def set_classifications_of_elements(element_classifications: list[dict]) -> dict:
    """Set classifications on elements.

    Args:
        element_classifications: Array of {elementId: {guid: "..."}, classificationId: {classificationSystemId: {guid: "..."}, classificationItemId: {guid: "..."}}}
    """
    return _run_tapir("SetClassificationsOfElements", {"elementClassifications": element_classifications})


# ============================================================================
# ELEMENT CREATION
# ============================================================================


@mcp.tool()
def create_columns(columns_data: list[dict]) -> dict:
    """Create column elements.

    Args:
        columns_data: Array of column definitions. Each needs: coordinates: {x, y, z} in meters.
            Example: [{"coordinates": {"x": 0.0, "y": 0.0, "z": 0.0}}, {"coordinates": {"x": 5.0, "y": 0.0, "z": 0.0}}]
    """
    return _run_tapir("CreateColumns", {"columnsData": columns_data})


@mcp.tool()
def create_slabs(slabs_data: list[dict]) -> dict:
    """Create slab (floor/ceiling) elements from 2D polygon outlines.

    Args:
        slabs_data: Array of slab definitions. Each needs:
            level (float): Z coordinate of the slab reference line in meters
            polygonCoordinates: Array of {x, y} 2D coordinates defining the outline (min 3 points)
            holes (optional): Array of hole polygons
            polygonArcs (optional): Arc segments
            Example: [{"level": 0.0, "polygonCoordinates": [{"x":0,"y":0}, {"x":10,"y":0}, {"x":10,"y":8}, {"x":0,"y":8}]}]
    """
    return _run_tapir("CreateSlabs", {"slabsData": slabs_data})


@mcp.tool()
def create_zones(zones_data: list[dict]) -> dict:
    """Create zone (room) elements.

    Args:
        zones_data: Array of zone definitions. Each needs:
            name (str): Room name
            numberStr (str): Room number
            geometry: Zone geometry — either {polygonCoordinates: [{x,y}...]} or {referenceCoordinate: {x,y}} for auto-detect
            floorIndex (optional): Story index
            stampPosition (optional): {x, y} position for zone stamp
    """
    return _run_tapir("CreateZones", {"zonesData": zones_data})


@mcp.tool()
def create_objects(objects_data: list[dict]) -> dict:
    """Create library part objects (furniture, fixtures, windows, doors, etc.).

    Args:
        objects_data: Array of object definitions. Each needs:
            libraryPartName (str): Name of the library part (e.g., "Chair 01", "Table Round")
            coordinates: {x, y, z} placement position
            dimensions (optional): {x, y, z} size override
            Example: [{"libraryPartName": "Chair 01", "coordinates": {"x": 3.0, "y": 2.0, "z": 0.0}}]
    """
    return _run_tapir("CreateObjects", {"objectsData": objects_data})


@mcp.tool()
def create_polylines(polylines_data: list[dict]) -> dict:
    """Create 2D polyline elements.

    Args:
        polylines_data: Array of polyline definitions. Each needs:
            coordinates: Array of {x, y} points (min 2)
            floorInd (optional): Story index
            arcs (optional): Arc segments
    """
    return _run_tapir("CreatePolylines", {"polylinesData": polylines_data})


@mcp.tool()
def create_meshes(meshes_data: list[dict]) -> dict:
    """Create mesh (terrain/surface) elements from 3D polygon coordinates.

    Args:
        meshes_data: Array of mesh definitions. Each needs:
            polygonCoordinates: Array of {x, y, z} 3D coordinates (min 3)
            level (optional): Z reference level
            floorIndex (optional): Story index
            skirtType (optional): Vertical, Horizontal, None
            skirtLevel (optional): Skirt height
            holes (optional): Hole polygons
            sublines (optional): Internal leveling lines
    """
    return _run_tapir("CreateMeshes", {"meshesData": meshes_data})


@mcp.tool()
def create_labels(labels_data: list[dict]) -> dict:
    """Create label/annotation elements.

    Args:
        labels_data: Array of label definitions. Each can have:
            text (str): Label text content
            parentElementId (optional): {guid: "..."} for associative labels
            begCoordinate (optional): {x, y} start of leader line
            floorInd (optional): Story index
    """
    return _run_tapir("CreateLabels", {"labelsData": labels_data})


@mcp.tool()
def create_walls(walls_data: list[dict]) -> dict:
    """Create wall elements. This is the primary building block for any structure.

    Args:
        walls_data: Array of wall definitions. Each needs:
            begCoordinate: {x, y} start point in meters (REQUIRED)
            endCoordinate: {x, y} end point in meters (REQUIRED)
            height (optional): Wall height in meters
            thickness (optional): Wall thickness in meters
            zCoordinate (optional): Base elevation in meters (default 0)
            offset (optional): Reference line offset from center
            arcAngle (optional): Arc angle in radians for curved walls (0 = straight)
            floorIndex (optional): Story index override
            Example: [{"begCoordinate": {"x":0,"y":0}, "endCoordinate": {"x":10,"y":0}, "height": 3.0, "thickness": 0.3}]
    """
    return _run_tapir("CreateWalls", {"wallsData": walls_data})


@mcp.tool()
def create_beams(beams_data: list[dict]) -> dict:
    """Create beam (horizontal structural) elements.

    Args:
        beams_data: Array of beam definitions. Each needs:
            begCoordinate: {x, y} start point in meters (REQUIRED)
            endCoordinate: {x, y} end point in meters (REQUIRED)
            level (optional): Elevation of beam axis in meters
            offset (optional): Vertical offset
            slantAngle (optional): Slant angle in radians
            arcAngle (optional): Curve angle in radians (0 = straight)
            floorIndex (optional): Story index override
    """
    return _run_tapir("CreateBeams", {"beamsData": beams_data})


@mcp.tool()
def create_roofs(roofs_data: list[dict]) -> dict:
    """Create single-plane roof elements from polygon outlines.

    Args:
        roofs_data: Array of roof definitions. Each needs:
            level (float): Z elevation of the roof plane in meters (REQUIRED)
            polygonCoordinates: Array of {x, y} 2D outline coordinates, min 3 (REQUIRED)
            angle (optional): Slope angle in radians (0 = flat roof)
            thickness (optional): Roof thickness in meters
            polygonArcs (optional): Arc segments
            holes (optional): Hole polygons
            floorIndex (optional): Story index override
            Example: [{"level": 6.0, "polygonCoordinates": [{"x":0,"y":0}, {"x":10,"y":0}, {"x":10,"y":8}, {"x":0,"y":8}]}]
    """
    return _run_tapir("CreateRoofs", {"roofsData": roofs_data})


@mcp.tool()
def create_windows(windows_data: list[dict]) -> dict:
    """Create window elements inside existing walls. Windows cut an opening in the wall.

    Args:
        windows_data: Array of window definitions. Each needs:
            wallId: {guid: "..."} of the wall to place the window in (REQUIRED)
            objLocation (float): Position along wall reference line, 0.0=start to 1.0=end (REQUIRED)
            libraryPartName (optional): Name of window library part
            lower (optional): Sill height — distance from floor to bottom of window in meters
            width (optional): Window opening width in meters
            height (optional): Window opening height in meters
            Example: [{"wallId": {"guid": "ABC-123..."}, "objLocation": 0.5, "width": 1.2, "height": 1.5, "lower": 0.9}]
    """
    return _run_tapir("CreateWindows", {"windowsData": windows_data})


@mcp.tool()
def create_doors(doors_data: list[dict]) -> dict:
    """Create door elements inside existing walls. Doors cut an opening in the wall.

    Args:
        doors_data: Array of door definitions. Each needs:
            wallId: {guid: "..."} of the wall to place the door in (REQUIRED)
            objLocation (float): Position along wall reference line, 0.0=start to 1.0=end (REQUIRED)
            libraryPartName (optional): Name of door library part
            lower (optional): Distance from floor to bottom of door in meters (usually 0)
            width (optional): Door opening width in meters
            height (optional): Door opening height in meters
            Example: [{"wallId": {"guid": "ABC-123..."}, "objLocation": 0.3, "width": 0.9, "height": 2.1}]
    """
    return _run_tapir("CreateDoors", {"doorsData": doors_data})


# ============================================================================
# ELEMENT GROUPING
# ============================================================================


@mcp.tool()
def create_groups(element_groups: list[dict]) -> dict:
    """Group elements together.

    Args:
        element_groups: Array of group definitions. Each is {elements: [{elementId: {guid: "..."}}], name: "group name"}
    """
    return _run_tapir("CreateGroups", {"elementGroups": element_groups})


# ============================================================================
# PREVIEW IMAGES
# ============================================================================


@mcp.tool()
def get_element_preview_image(
    element_id: str,
    image_type: str = "3D",
    format: str = "png",
    width: int = 256,
    height: int = 256,
) -> dict:
    """Get a preview image of an element (base64 encoded). Very useful to SEE what an element looks like.

    Args:
        element_id: GUID of the element
        image_type: 2D, Section, or 3D
        format: png or jpg
        width: Image width in pixels
        height: Image height in pixels
    """
    return _run_tapir(
        "GetElementPreviewImage",
        {"elementId": {"guid": element_id}, "imageType": image_type, "format": format, "width": width, "height": height},
    )


@mcp.tool()
def get_room_image(
    zone_id: str,
    format: str = "png",
    width: int = 512,
    height: int = 512,
    scale: float = 0.005,
) -> dict:
    """Get a plan view image of a room/zone (base64 encoded).

    Args:
        zone_id: GUID of the zone element
        format: png or jpg
        width: Image width in pixels
        height: Image height in pixels
        scale: View scale (0.005 = 1:200, 0.01 = 1:100)
    """
    return _run_tapir(
        "GetRoomImage",
        {"zoneId": {"guid": zone_id}, "format": format, "width": width, "height": height, "scale": scale},
    )


# ============================================================================
# FAVORITES
# ============================================================================


@mcp.tool()
def get_favorites_by_type(element_type: str) -> dict:
    """Get available favorites for an element type. Favorites are predefined element configurations.

    Args:
        element_type: Element type (Wall, Column, Slab, Object, etc.)
    """
    return _run_tapir("GetFavoritesByType", {"elementType": element_type})


@mcp.tool()
def get_favorite_preview_image(favorite_name: str, format: str = "png", width: int = 128, height: int = 128) -> dict:
    """Get a preview image of a favorite (base64 encoded).

    Args:
        favorite_name: Name of the favorite
        format: png or jpg
        width: Image width in pixels
        height: Image height in pixels
    """
    return _run_tapir("GetFavoritePreviewImage", {"favoriteName": favorite_name, "format": format, "width": width, "height": height})


@mcp.tool()
def apply_favorites_to_element_defaults(favorites: list[dict]) -> dict:
    """Apply favorites to element defaults (so next created element uses this config).

    Args:
        favorites: Array of {favoriteName: "name", elementType: "Wall"}
    """
    return _run_tapir("ApplyFavoritesToElementDefaults", {"favorites": favorites})


@mcp.tool()
def create_favorites_from_elements(elements_with_names: list[dict]) -> dict:
    """Save elements as favorites for reuse.

    Args:
        elements_with_names: Array of {elementId: {guid: "..."}, favoriteName: "My Wall Type"}
    """
    return _run_tapir("CreateFavoritesFromElements", {"elementsWithFavoriteNames": elements_with_names})


# ============================================================================
# PROPERTY COMMANDS
# ============================================================================


@mcp.tool()
def get_all_properties() -> dict:
    """Get all property definitions available in the project. Returns property groups with their property definitions."""
    return _run_tapir("GetAllProperties")


@mcp.tool()
def get_property_values_of_elements(elements: list[dict], properties: list[dict]) -> dict:
    """Get property values for elements. Use get_all_properties first to find available property IDs.

    Args:
        elements: Array of element references [{"elementId": {"guid": "..."}}]
        properties: Array of property IDs [{"propertyId": {"guid": "..."}}]
    """
    return _run_tapir("GetPropertyValuesOfElements", {"elements": elements, "properties": properties})


@mcp.tool()
def set_property_values_of_elements(element_property_values: list[dict]) -> dict:
    """Set property values on elements.

    Args:
        element_property_values: Array of {elementId: {guid: "..."}, propertyId: {guid: "..."}, propertyValue: {value: "..."}}
    """
    return _run_tapir("SetPropertyValuesOfElements", {"elementPropertyValues": element_property_values})


@mcp.tool()
def create_property_groups(property_groups: list[dict]) -> dict:
    """Create new property groups with property definitions.

    Args:
        property_groups: Array of property group definitions with name and property definitions
    """
    return _run_tapir("CreatePropertyGroups", {"propertyGroups": property_groups})


@mcp.tool()
def delete_property_groups(property_group_ids: list[dict]) -> dict:
    """Delete property groups.

    Args:
        property_group_ids: Array of {propertyGroupId: {guid: "..."}}
    """
    return _run_tapir("DeletePropertyGroups", {"propertyGroupIds": property_group_ids})


@mcp.tool()
def create_property_definitions(property_definitions: list[dict]) -> dict:
    """Create new property definitions within existing groups.

    Args:
        property_definitions: Array of property definition specs
    """
    return _run_tapir("CreatePropertyDefinitions", {"propertyDefinitions": property_definitions})


@mcp.tool()
def delete_property_definitions(property_definition_ids: list[dict]) -> dict:
    """Delete property definitions.

    Args:
        property_definition_ids: Array of {propertyId: {guid: "..."}}
    """
    return _run_tapir("DeletePropertyDefinitions", {"propertyDefinitionIds": property_definition_ids})


# ============================================================================
# ATTRIBUTE COMMANDS
# ============================================================================


@mcp.tool()
def get_attributes_by_type(attribute_type: str) -> dict:
    """Get all attributes of a given type. Attributes define layers, materials, composites, surfaces, etc.

    Args:
        attribute_type: Layer, Line, Fill, Composite, Surface, LayerCombination, ZoneCategory, Profile, PenTable, MEPSystem, OperationProfile, BuildingMaterial
    """
    return _run_tapir("GetAttributesByType", {"attributeType": attribute_type})


@mcp.tool()
def create_layers(layers_data: list[dict]) -> dict:
    """Create new layers.

    Args:
        layers_data: Array of {name: "Layer Name", isHidden: false, isLocked: false}
    """
    return _run_tapir("CreateLayers", {"layersData": layers_data})


@mcp.tool()
def create_layer_combinations(layer_combinations: list[dict]) -> dict:
    """Create layer combinations (presets of layer visibility).

    Args:
        layer_combinations: Array of layer combination definitions
    """
    return _run_tapir("CreateLayerCombinations", {"layerCombinations": layer_combinations})


@mcp.tool()
def create_building_materials(building_materials: list[dict]) -> dict:
    """Create building materials with physical properties.

    Args:
        building_materials: Array of building material definitions
    """
    return _run_tapir("CreateBuildingMaterials", {"buildingMaterials": building_materials})


@mcp.tool()
def create_composites(composites: list[dict]) -> dict:
    """Create composite wall/slab/roof structures (multi-layer definitions).

    Args:
        composites: Array of composite definitions with skin layers
    """
    return _run_tapir("CreateComposites", {"composites": composites})


@mcp.tool()
def create_surfaces(surfaces: list[dict]) -> dict:
    """Create surface materials for rendering.

    Args:
        surfaces: Array of surface definitions with color, texture, reflection properties
    """
    return _run_tapir("CreateSurfaces", {"surfaces": surfaces})


@mcp.tool()
def get_building_material_physical_properties(attribute_ids: list[dict]) -> dict:
    """Get physical properties of building materials (thermal conductivity, density, etc.).

    Args:
        attribute_ids: Array of building material attribute IDs [{"attributeId": {"guid": "..."}}]
    """
    return _run_tapir("GetBuildingMaterialPhysicalProperties", {"attributeIds": attribute_ids})


@mcp.tool()
def get_layer_combinations() -> dict:
    """Get all layer combinations with their layer visibility settings."""
    return _run_tapir("GetLayerCombinations")


# ============================================================================
# LIBRARY COMMANDS
# ============================================================================


@mcp.tool()
def get_libraries() -> dict:
    """Get all loaded libraries. Libraries contain GDL objects (furniture, fixtures, etc.). Large or many libraries increase file size significantly."""
    return _run_tapir("GetLibraries")


@mcp.tool()
def reload_libraries() -> dict:
    """Reload all loaded libraries. Useful after adding new library parts."""
    return _run_tapir("ReloadLibraries")


@mcp.tool()
def add_files_to_embedded_library(file_paths: list[str]) -> dict:
    """Add files to the project's embedded library.

    Args:
        file_paths: Array of file paths to add
    """
    return _run_tapir("AddFilesToEmbeddedLibrary", {"filePaths": file_paths})


# ============================================================================
# TEAMWORK COMMANDS
# ============================================================================


@mcp.tool()
def teamwork_send() -> dict:
    """Send (publish) changes to the BIMcloud server in a teamwork project."""
    return _run_tapir("TeamworkSend")


@mcp.tool()
def teamwork_receive() -> dict:
    """Receive (pull) changes from the BIMcloud server in a teamwork project."""
    return _run_tapir("TeamworkReceive")


@mcp.tool()
def reserve_elements(elements: list[dict]) -> dict:
    """Reserve elements for editing in a teamwork project.

    Args:
        elements: Array of element references
    """
    return _run_tapir("ReserveElements", {"elements": elements})


@mcp.tool()
def release_elements(elements: list[dict]) -> dict:
    """Release reserved elements in a teamwork project.

    Args:
        elements: Array of element references
    """
    return _run_tapir("ReleaseElements", {"elements": elements})


# ============================================================================
# NAVIGATOR COMMANDS
# ============================================================================


@mcp.tool()
def publish_publisher_set(publisher_set_name: str) -> dict:
    """Publish a publisher set (batch export of views).

    Args:
        publisher_set_name: Name of the publisher set
    """
    return _run_tapir("PublishPublisherSet", {"publisherSetName": publisher_set_name})


@mcp.tool()
def update_drawings() -> dict:
    """Update all drawings in the project."""
    return _run_tapir("UpdateDrawings")


@mcp.tool()
def create_details(details_data: list[dict]) -> dict:
    """Create detail views.

    Args:
        details_data: Array of detail definitions
    """
    return _run_tapir("CreateDetails", {"detailsData": details_data})


@mcp.tool()
def create_worksheets(worksheets_data: list[dict]) -> dict:
    """Create worksheet views.

    Args:
        worksheets_data: Array of worksheet definitions
    """
    return _run_tapir("CreateWorksheets", {"worksheetsData": worksheets_data})


@mcp.tool()
def create_layouts(layouts_data: list[dict]) -> dict:
    """Create layouts for printing/documentation.

    Args:
        layouts_data: Array of layout definitions
    """
    return _run_tapir("CreateLayouts", {"layoutsData": layouts_data})


@mcp.tool()
def create_subsets(subsets_data: list[dict]) -> dict:
    """Create layout subsets (folders in the layout book).

    Args:
        subsets_data: Array of subset definitions
    """
    return _run_tapir("CreateSubsets", {"subsetsData": subsets_data})


@mcp.tool()
def create_drawings(drawings_data: list[dict]) -> dict:
    """Create drawings on layouts.

    Args:
        drawings_data: Array of drawing definitions
    """
    return _run_tapir("CreateDrawings", {"drawingsData": drawings_data})


@mcp.tool()
def get_model_view_options() -> dict:
    """Get current 3D model view options (rendering settings)."""
    return _run_tapir("GetModelViewOptions")


@mcp.tool()
def get_view_settings() -> dict:
    """Get current view settings (scale, grid, etc.)."""
    return _run_tapir("GetViewSettings")


@mcp.tool()
def set_view_settings(view_settings: dict) -> dict:
    """Set view settings.

    Args:
        view_settings: View settings dictionary
    """
    return _run_tapir("SetViewSettings", view_settings)


@mcp.tool()
def set_3d_cut_planes(cut_planes: dict) -> dict:
    """Set 3D cut planes for section visibility.

    Args:
        cut_planes: Cut plane settings
    """
    return _run_tapir("Set3DCutPlanes", cut_planes)


@mcp.tool()
def fit_in_window() -> dict:
    """Zoom to fit all elements in the current window."""
    return _run_tapir("FitInWindow")


# ============================================================================
# ISSUE MANAGEMENT (BCF)
# ============================================================================


@mcp.tool()
def create_issue(name: str, tag_text: str | None = None) -> dict:
    """Create a new issue/markup for project coordination.

    Args:
        name: Issue name/title
        tag_text: Optional tag text
    """
    params: dict = {"name": name}
    if tag_text:
        params["tagText"] = tag_text
    return _run_tapir("CreateIssue", params)


@mcp.tool()
def get_issues() -> dict:
    """Get all issues in the project."""
    return _run_tapir("GetIssues")


@mcp.tool()
def delete_issue(issue_id: str) -> dict:
    """Delete an issue.

    Args:
        issue_id: GUID of the issue
    """
    return _run_tapir("DeleteIssue", {"issueId": {"guid": issue_id}})


@mcp.tool()
def add_comment_to_issue(issue_id: str, comment: str, author: str = "Claude") -> dict:
    """Add a comment to an issue.

    Args:
        issue_id: GUID of the issue
        comment: Comment text
        author: Author name
    """
    return _run_tapir("AddCommentToIssue", {"issueId": {"guid": issue_id}, "comment": comment, "author": author})


@mcp.tool()
def get_comments_from_issue(issue_id: str) -> dict:
    """Get all comments from an issue.

    Args:
        issue_id: GUID of the issue
    """
    return _run_tapir("GetCommentsFromIssue", {"issueId": {"guid": issue_id}})


@mcp.tool()
def attach_elements_to_issue(issue_id: str, elements: list[dict]) -> dict:
    """Attach elements to an issue for tracking.

    Args:
        issue_id: GUID of the issue
        elements: Array of element references
    """
    return _run_tapir("AttachElementsToIssue", {"issueId": {"guid": issue_id}, "elements": elements})


@mcp.tool()
def get_elements_attached_to_issue(issue_id: str) -> dict:
    """Get elements attached to an issue.

    Args:
        issue_id: GUID of the issue
    """
    return _run_tapir("GetElementsAttachedToIssue", {"issueId": {"guid": issue_id}})


@mcp.tool()
def export_issues_to_bcf(file_path: str) -> dict:
    """Export issues to BCF (BIM Collaboration Format) file.

    Args:
        file_path: Target BCF file path
    """
    return _run_tapir("ExportIssuesToBCF", {"filePath": file_path})


@mcp.tool()
def import_issues_from_bcf(file_path: str) -> dict:
    """Import issues from a BCF file.

    Args:
        file_path: Source BCF file path
    """
    return _run_tapir("ImportIssuesFromBCF", {"filePath": file_path})


# ============================================================================
# REVISION MANAGEMENT
# ============================================================================


@mcp.tool()
def get_revision_issues() -> dict:
    """Get revision issues (change tracking milestones)."""
    return _run_tapir("GetRevisionIssues")


@mcp.tool()
def get_revision_changes() -> dict:
    """Get revision changes."""
    return _run_tapir("GetRevisionChanges")


@mcp.tool()
def get_document_revisions() -> dict:
    """Get document revision history."""
    return _run_tapir("GetDocumentRevisions")


# ============================================================================
# DESIGN OPTIONS
# ============================================================================


@mcp.tool()
def get_design_options() -> dict:
    """Get all design options in the project. Design options allow exploring alternative configurations."""
    return _run_tapir("GetDesignOptions")


@mcp.tool()
def get_design_option_sets() -> dict:
    """Get all design option sets."""
    return _run_tapir("GetDesignOptionSets")


@mcp.tool()
def get_design_option_combinations() -> dict:
    """Get all design option combinations."""
    return _run_tapir("GetDesignOptionCombinations")


# ============================================================================
# COMPONENT COMMANDS (via official API)
# ============================================================================


@mcp.tool()
def get_components_of_elements(elements: list[dict]) -> dict:
    """Get components (layers/skins) of composite elements like walls and slabs.
    Returns the individual layers that make up a composite structure.

    Args:
        elements: Array of element references [{"elementId": {"guid": "..."}}]
    """
    return _run_command("API.GetComponentsOfElements", {"elements": elements})


@mcp.tool()
def get_property_values_of_components(
    element_components: list[dict], properties: list[dict]
) -> dict:
    """Get property values for element components (individual layers of composites).

    Args:
        element_components: Array of element component references
        properties: Array of property IDs
    """
    return _run_command(
        "API.GetPropertyValuesOfElementComponents",
        {"elementComponents": element_components, "properties": properties},
    )


# ============================================================================
# NOTIFICATION (for real-time monitoring)
# ============================================================================


@mcp.tool()
def set_element_notification_client(
    port: int,
    host: str | None = None,
    notify_on_new: bool = True,
    notify_on_modify: bool = True,
    notify_on_reservation: bool = True,
) -> dict:
    """Register for real-time element change notifications from ArchiCAD.

    Args:
        port: Port number for the notification listener
        host: Host address (default: localhost)
        notify_on_new: Notify when elements are created
        notify_on_modify: Notify when elements are modified/deleted
        notify_on_reservation: Notify on reservation changes (teamwork)
    """
    params: dict = {
        "port": port,
        "notifyOnNewElement": notify_on_new,
        "notifyOnModificationOfAnElement": notify_on_modify,
        "notifyOnReservationChanges": notify_on_reservation,
    }
    if host:
        params["host"] = host
    return _run_tapir("SetElementNotificationClient", params)


@mcp.tool()
def remove_element_notification_client(port: int, host: str | None = None) -> dict:
    """Remove a notification client registration.

    Args:
        port: Port number of the listener to remove
        host: Host address (default: localhost)
    """
    params: dict = {"port": port}
    if host:
        params["host"] = host
    return _run_tapir("RemoveElementNotificationClient", params)


# ============================================================================
# HIGH-LEVEL ANALYSIS TOOLS (composite tools for common workflows)
# ============================================================================


@mcp.tool()
def analyze_project_size() -> dict:
    """Analyze the project to understand what makes it large. Returns element counts by type, total count, and identified heavy element types.
    This is the FIRST tool to use when investigating why a project is 20GB."""
    all_elements = _run_tapir("GetAllElements", {})
    if isinstance(all_elements, dict) and "error" in all_elements:
        return all_elements

    elements = all_elements.get("elements", [])
    total = len(elements)

    if total == 0:
        return {"totalElements": 0, "message": "Project has no elements"}

    details_result = _run_tapir("GetDetailsOfElements", {"elements": elements})
    if isinstance(details_result, dict) and "error" in details_result:
        return {"totalElements": total, "error_getting_details": details_result["error"]}

    details = details_result.get("detailsOfElements", [])
    type_counts: dict[str, int] = {}
    floor_counts: dict[int, int] = {}
    for d in details:
        t = d.get("type", "Unknown")
        type_counts[t] = type_counts.get(t, 0) + 1
        f = d.get("floorIndex", -999)
        floor_counts[f] = floor_counts.get(f, 0) + 1

    sorted_types = sorted(type_counts.items(), key=lambda x: -x[1])
    sorted_floors = sorted(floor_counts.items(), key=lambda x: -x[1])

    heavy_types = ["Object", "Morph", "Mesh", "CurtainWall", "Stair", "Railing"]
    warnings = []
    for ht in heavy_types:
        if ht in type_counts and type_counts[ht] > 50:
            warnings.append(f"{type_counts[ht]} {ht} elements — these are typically heavy in file size")

    return {
        "totalElements": total,
        "elementsByType": dict(sorted_types),
        "elementsByFloor": {str(k): v for k, v in sorted_floors},
        "warnings": warnings,
        "recommendation": "Use get_3d_bounding_boxes on the heaviest types to find oversized elements. Use get_gdl_parameters on Objects to check parametric complexity. Use get_libraries and get_hotlinks to check external references.",
    }


@mcp.tool()
def find_oversized_elements(element_type: str | None = None, size_threshold: float = 100.0) -> dict:
    """Find elements with unusually large bounding boxes (possibly misplaced or corrupted).

    Args:
        element_type: Optional — only check this element type. If None, checks all.
        size_threshold: Max dimension in meters to consider normal. Elements exceeding this are flagged. Default 100m.
    """
    if element_type:
        result = _run_tapir("GetElementsByType", {"elementType": element_type})
    else:
        result = _run_tapir("GetAllElements", {})

    if isinstance(result, dict) and "error" in result:
        return result

    elements = result.get("elements", [])
    if not elements:
        return {"oversized": [], "message": "No elements found"}

    batch_size = 500
    oversized = []

    for i in range(0, len(elements), batch_size):
        batch = elements[i : i + batch_size]
        boxes_result = _run_tapir("Get3DBoundingBoxes", {"elements": batch})
        if isinstance(boxes_result, dict) and "error" in boxes_result:
            continue
        boxes = boxes_result.get("boundingBoxes3D", [])
        for j, box in enumerate(boxes):
            if not isinstance(box, dict):
                continue
            dx = abs(box.get("xMax", 0) - box.get("xMin", 0))
            dy = abs(box.get("yMax", 0) - box.get("yMin", 0))
            dz = abs(box.get("zMax", 0) - box.get("zMin", 0))
            max_dim = max(dx, dy, dz)
            if max_dim > size_threshold:
                elem = batch[j]
                oversized.append(
                    {
                        "elementId": elem["elementId"],
                        "boundingBox": box,
                        "dimensions": {"dx": round(dx, 2), "dy": round(dy, 2), "dz": round(dz, 2)},
                        "maxDimension": round(max_dim, 2),
                    }
                )

    return {
        "totalChecked": len(elements),
        "oversizedCount": len(oversized),
        "sizeThreshold": size_threshold,
        "oversizedElements": oversized[:50],
    }


@mcp.tool()
def get_project_visual_overview(max_preview_elements: int = 6) -> dict:
    """Get a comprehensive visual overview of the entire project. Returns project info, story structure,
    element statistics, the 3D bounding box of the whole model, library info, hotlinks, AND preview images
    of representative elements so Claude can actually SEE the project.

    This is THE tool to call first when you want to understand a project.

    Args:
        max_preview_elements: How many element preview images to include (default 6). Each is a base64 PNG.
    """
    overview: dict = {}

    project_info = _run_tapir("GetProjectInfo")
    if isinstance(project_info, dict) and "error" not in project_info:
        overview["project"] = project_info

    stories = _run_tapir("GetStories")
    if isinstance(stories, dict) and "error" not in stories:
        overview["stories"] = stories

    all_elements = _run_tapir("GetAllElements", {})
    if isinstance(all_elements, dict) and "error" in all_elements:
        overview["error"] = all_elements["error"]
        return overview

    elements = all_elements.get("elements", [])
    overview["totalElements"] = len(elements)

    if not elements:
        overview["message"] = "Project is empty"
        return overview

    details_result = _run_tapir("GetDetailsOfElements", {"elements": elements})
    type_counts: dict[str, int] = {}
    floor_counts: dict[str, int] = {}
    elements_by_type: dict[str, list] = {}

    if isinstance(details_result, dict) and "detailsOfElements" in details_result:
        for i, d in enumerate(details_result["detailsOfElements"]):
            t = d.get("type", "Unknown")
            type_counts[t] = type_counts.get(t, 0) + 1
            f = str(d.get("floorIndex", "?"))
            floor_counts[f] = floor_counts.get(f, 0) + 1
            if t not in elements_by_type:
                elements_by_type[t] = []
            if len(elements_by_type[t]) < 3:
                elements_by_type[t].append(elements[i])

    overview["elementsByType"] = dict(sorted(type_counts.items(), key=lambda x: -x[1]))
    overview["elementsByFloor"] = dict(sorted(floor_counts.items(), key=lambda x: -x[1]))

    batch_size = 500
    global_box = {"xMin": float("inf"), "xMax": float("-inf"),
                  "yMin": float("inf"), "yMax": float("-inf"),
                  "zMin": float("inf"), "zMax": float("-inf")}
    for i in range(0, len(elements), batch_size):
        batch = elements[i : i + batch_size]
        boxes_result = _run_tapir("Get3DBoundingBoxes", {"elements": batch})
        if isinstance(boxes_result, dict) and "boundingBoxes3D" in boxes_result:
            for box in boxes_result["boundingBoxes3D"]:
                if not isinstance(box, dict):
                    continue
                for key in ("xMin", "yMin", "zMin"):
                    if key in box and box[key] < global_box[key]:
                        global_box[key] = box[key]
                for key in ("xMax", "yMax", "zMax"):
                    if key in box and box[key] > global_box[key]:
                        global_box[key] = box[key]

    if global_box["xMin"] != float("inf"):
        overview["projectBoundingBox"] = {k: round(v, 2) for k, v in global_box.items()}
        overview["projectDimensions"] = {
            "width_m": round(global_box["xMax"] - global_box["xMin"], 2),
            "depth_m": round(global_box["yMax"] - global_box["yMin"], 2),
            "height_m": round(global_box["zMax"] - global_box["zMin"], 2),
        }

    libs = _run_tapir("GetLibraries")
    if isinstance(libs, dict) and "error" not in libs:
        overview["libraries"] = libs

    hotlinks = _run_tapir("GetHotlinks")
    if isinstance(hotlinks, dict) and "error" not in hotlinks:
        overview["hotlinks"] = hotlinks

    previews = []
    priority_types = ["Wall", "Object", "Slab", "Roof", "Column", "Beam",
                      "Window", "Door", "Stair", "CurtainWall", "Morph", "Mesh"]
    sampled = []
    for pt in priority_types:
        if pt in elements_by_type and elements_by_type[pt]:
            sampled.append((pt, elements_by_type[pt][0]))
        if len(sampled) >= max_preview_elements:
            break

    if len(sampled) < max_preview_elements:
        for t, elems in elements_by_type.items():
            if not any(s[0] == t for s in sampled) and elems:
                sampled.append((t, elems[0]))
            if len(sampled) >= max_preview_elements:
                break

    for elem_type, elem in sampled:
        guid = elem.get("elementId", {}).get("guid", "")
        if not guid:
            continue
        img = _run_tapir(
            "GetElementPreviewImage",
            {"elementId": {"guid": guid}, "imageType": "3D", "format": "png", "width": 256, "height": 256},
        )
        if isinstance(img, dict) and "previewImage" in img:
            previews.append({
                "elementType": elem_type,
                "elementId": guid,
                "previewImage_base64_png": img["previewImage"],
            })

    if previews:
        overview["elementPreviews"] = previews

    zones_result = _run_tapir("GetElementsByType", {"elementType": "Zone"})
    if isinstance(zones_result, dict) and "elements" in zones_result:
        zone_elements = zones_result["elements"]
        if zone_elements:
            zone_guid = zone_elements[0].get("elementId", {}).get("guid", "")
            if zone_guid:
                room_img = _run_tapir(
                    "GetRoomImage",
                    {"zoneId": {"guid": zone_guid}, "format": "png", "width": 512, "height": 512, "scale": 0.005},
                )
                if isinstance(room_img, dict) and "roomImage" in room_img:
                    overview["sampleRoomPlan"] = {
                        "zoneId": zone_guid,
                        "roomImage_base64_png": room_img["roomImage"],
                    }

    return overview


if __name__ == "__main__":
    mcp.run()
