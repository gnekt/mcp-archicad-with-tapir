# Tapir ArchiCAD MCP Server

Connect Claude to a running ArchiCAD instance. Create buildings, analyze projects, modify elements — all through natural language.

## What it does

This MCP server exposes **90+ tools** that let Claude interact with ArchiCAD via the Tapir Add-On JSON API:

- **Create** — columns, slabs, roofs, zones, objects, meshes, labels
- **Query** — get all elements, filter by type/layer/floor, get 3D bounding boxes, get GDL parameters
- **Modify** — move elements, change properties, set classifications, update GDL parameters
- **Analyze** — project size analysis, find oversized elements, check libraries and hotlinks
- **Visualize** — highlight elements with colors, get preview images, room images
- **Document** — create issues, add comments, export BCF, manage revisions
- **Manage** — layers, materials, composites, surfaces, favorites, design options

## Prerequisites

1. **ArchiCAD** (version 25-29) running on the same machine
2. **Tapir Add-On** installed in ArchiCAD — [download from releases](https://github.com/ENZYME-APD/tapir-archicad-automation/releases)
3. **Python 3.10+**

## Installation

### For Claude Desktop

```bash
cd mcp-server
pip install -e .
```

Then add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "tapir-archicad": {
      "command": "python",
      "args": ["/full/path/to/mcp-archicad-with-tapir/mcp-server/server.py"]
    }
  }
}
```

### For Claude Code

```bash
cd mcp-server
pip install -e .
claude mcp add tapir-archicad -- python /full/path/to/mcp-archicad-with-tapir/mcp-server/server.py
```

## Usage Examples

Once connected, you can ask Claude things like:

- "Analizza il progetto e dimmi perche' e' cosi' grande" (Analyze the project and tell me why it's so big)
- "Quanti muri ci sono per piano?" (How many walls per floor?)
- "Trova gli oggetti con bounding box anomali" (Find objects with anomalous bounding boxes)
- "Crea un solaio rettangolare 10x8 metri al piano terra" (Create a 10x8m rectangular slab on the ground floor)
- "Evidenzia in rosso tutti gli Object sul piano 3" (Highlight all Objects on floor 3 in red)
- "Esporta il progetto in IFC" (Export the project to IFC)
- "Crea una issue per gli elementi problematici" (Create an issue for problematic elements)

## Architecture

```
Claude <-> MCP Protocol <-> This Server <-> HTTP JSON <-> ArchiCAD (Tapir Add-On)
                                              |
                                     localhost:19723
```

The server translates MCP tool calls into HTTP JSON requests to the Tapir Add-On running inside ArchiCAD. No direct file access to .pln files — everything goes through the live ArchiCAD instance.

## Available Tools (90+)

### Project
`get_project_info` `get_project_info_fields` `set_project_info_field` `get_stories` `set_stories` `get_hotlinks` `open_project` `save_project` `get_geo_location` `set_geo_location` `ifc_file_operation`

### Elements — Query
`get_all_elements` `get_elements_by_type` `get_selected_elements` `change_selection` `filter_elements`

### Elements — Details & Geometry
`get_details_of_elements` `set_details_of_elements` `get_3d_bounding_boxes` `get_subelements` `get_connected_elements` `get_zone_boundaries` `get_collisions`

### Elements — Create
`create_columns` `create_slabs` `create_zones` `create_objects` `create_polylines` `create_meshes` `create_labels` `create_groups`

### Elements — Modify
`move_elements` `delete_elements` `highlight_elements`

### GDL Parameters
`get_gdl_parameters` `set_gdl_parameters`

### Classifications
`get_classifications_of_elements` `set_classifications_of_elements`

### Properties
`get_all_properties` `get_property_values_of_elements` `set_property_values_of_elements` `create_property_groups` `delete_property_groups` `create_property_definitions` `delete_property_definitions`

### Attributes
`get_attributes_by_type` `create_layers` `create_layer_combinations` `create_building_materials` `create_composites` `create_surfaces` `get_building_material_physical_properties` `get_layer_combinations`

### Library
`get_libraries` `reload_libraries` `add_files_to_embedded_library`

### Favorites
`get_favorites_by_type` `get_favorite_preview_image` `apply_favorites_to_element_defaults` `create_favorites_from_elements`

### Images
`get_element_preview_image` `get_room_image`

### Navigator
`publish_publisher_set` `update_drawings` `create_details` `create_worksheets` `create_layouts` `create_subsets` `create_drawings` `get_model_view_options` `get_view_settings` `set_view_settings` `set_3d_cut_planes` `fit_in_window`

### Issues (BCF)
`create_issue` `get_issues` `delete_issue` `add_comment_to_issue` `get_comments_from_issue` `attach_elements_to_issue` `get_elements_attached_to_issue` `export_issues_to_bcf` `import_issues_from_bcf`

### Revisions
`get_revision_issues` `get_revision_changes` `get_document_revisions`

### Design Options
`get_design_options` `get_design_option_sets` `get_design_option_combinations`

### Teamwork
`teamwork_send` `teamwork_receive` `reserve_elements` `release_elements`

### Notifications
`set_element_notification_client` `remove_element_notification_client`

### Analysis (High-Level)
`analyze_project_size` `find_oversized_elements`

## Troubleshooting

**"Cannot connect to ArchiCAD"** — Make sure ArchiCAD is running and the Tapir Add-On is installed. The API listens on `localhost:19723` by default.

**Slow responses** — Large projects with 50K+ elements may take time for bulk queries. Use `get_elements_by_type` instead of `get_all_elements` to work with smaller batches.

**"Element not found"** — Element GUIDs change when elements are recreated. Re-query elements if you get stale GUIDs.
