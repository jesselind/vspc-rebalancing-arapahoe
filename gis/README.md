# GIS Data and Tools

This directory contains the **current** GIS tools and data for visualizing VSPC and precinct distributions in QGIS.

## Current Tools

### Color Assignment Scripts

- **`assign_vspc_colors.py`** - Assigns colors to VSPCs based on geographic proximity
  - Uses hardcoded color assignments (from v13) with manual override support
  - Ensures adjacent VSPCs use different color families
  - Generates `vspc_locations_colored.geojson` and `vspc_color_mapping.json`
  - Automatically runs `assign_precinct_colors.py` after VSPC colors are assigned

- **`assign_precinct_colors.py`** - Assigns colors to precincts based on their assigned VSPC
  - Reads VSPC colors from `vspc_color_mapping.json`
  - Reads precinct assignments from `output/VSPC - Precinct Distribution.csv`
  - Generates `precinct_locations_colored.geojson` with colors matching assigned VSPCs

### Usage

To generate colored GeoJSON files:

```bash
cd gis
python3 assign_vspc_colors.py
```

This will:
1. Load VSPC locations from `vspc_locations.geojson`
2. Assign colors to VSPCs (using hardcoded assignments from v13)
3. Generate `vspc_locations_colored.geojson` and `vspc_color_mapping.json`
4. Automatically update precinct colors in `precinct_locations_colored.geojson`

To manually update only precinct colors:

```bash
cd gis
python3 assign_precinct_colors.py
```

## Output Files

### VSPC Files

- **`vspc_locations.geojson`** - Basic VSPC locations (input for color assignment)
- **`vspc_locations_colored.geojson`** - VSPC locations with assigned colors (current)
- **`vspc_color_mapping.json`** - JSON mapping of VSPC names to colors

### Precinct Files

- **`precinct_locations.geojson`** - Basic precinct locations
- **`precinct_locations_colored.geojson`** - Precinct locations with colors matching assigned VSPC (current)
- **Note**: Original `precinct_centroids.csv` (source data) is archived in `Archived Resources/` - data was incorporated into `master_precincts.csv`

### Reference Data

- **`County_Boundary_SHAPE_WGS/`** - County boundary shapefile data

## QGIS Usage

### Loading Colored Files

1. **VSPC Colors**:
   - Load `vspc_locations_colored.geojson` in QGIS
   - In Symbology, use 'Categorized' by 'name'
   - For each category, set the color to match the 'color' property
   - Or use 'Single Symbol' with data-defined color override using the 'color' field

2. **Precinct Colors**:
   - Load `precinct_locations_colored.geojson` in QGIS
   - In Symbology, use 'Categorized' by 'assigned_vspc'
   - For each category, set the color to match the 'color' property
   - Or use 'Single Symbol' with data-defined color override using the 'color' field

### Color Assignment Philosophy

The current color system (based on v13):
- **Stability**: All 32 VSPC colors are hardcoded for consistency
- **Manual Overrides**: Colors can be changed in `assign_vspc_colors.py` without triggering full recalculation
- **Automatic Precinct Colors**: Precinct colors automatically match their assigned VSPC colors
- **Geographic Constraints**: Adjacent VSPCs (within 10 miles) use different color families

## Historical Versions

Previous versions of the GIS color assignment system are preserved in:
- **`Archived Resources/v13/gis/`** - V13 color assignment system (source of current hardcoded colors)
- **`Archived Resources/v12/gis/`** - V12 HSL-based automatic color assignment
- **`Archived Resources/v11/gis/`** - V11 RGB-based color assignment

See the version-specific READMEs in those directories for details on their approaches.

## Additional Resources

- **`QGIS_SETUP_GUIDE.md`** - Detailed QGIS setup and visualization instructions
- **Arapahoe County GIS Data**: [GIS Data Download page](https://gis.arapahoegov.com/datadownload/) - Updated nightly with latest county data
