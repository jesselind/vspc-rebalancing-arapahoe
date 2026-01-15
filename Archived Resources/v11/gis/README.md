# V11 GIS Color Assignment (Backup)

**Status**: This is a backup/fallback version. The current active version is in `../v12/gis/`.

This directory contains a backup of the V11 color assignment system, preserved for reference and fallback purposes.

## V11 Results

- 18 remaining same-family conflicts (down from 55+)
- All 32 VSPCs have unique colors
- Family separation: 15 miles minimum

## Files

- `assign_vspc_colors.py` - Color assignment script (V11 version)
- `export_gis_data.py` - GIS data export script
- `vspc_locations.geojson` - VSPC location data
- `vspc_locations_colored.geojson` - VSPC locations with assigned colors (V11 output)
- `vspc_color_mapping.json` - Color mapping (V11 output)
- `v11_precinct_assignments.geojson` - Precinct assignments with v11 data

For details on the V11 approach and V12 improvements, see `../v12/gis/README.md`.
