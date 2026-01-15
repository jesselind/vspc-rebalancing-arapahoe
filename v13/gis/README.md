# V13 GIS Color Assignment

This directory contains the V13 version of the VSPC color assignment system, using hardcoded color assignments with manual override support.

## Migration from V12

**Date**: January 2025

**Purpose**: Provide stable color assignments with manual override capability without triggering full recalculation.

### V12 Approach (Backup in `../v12/gis/`)
- HSL-based palette with automatic color assignment
- Adjacent VSPC constraint checking
- Automatic recalculation when manual overrides are provided
- **Issue**: Manual overrides triggered full recalculation (whack-a-mole problem)

### V13 Approach (Current)
V13 uses **hardcoded color assignments** from V12's final output. All 32 VSPC colors are pre-assigned in the `MANUAL_COLOR_OVERRIDES` dictionary.

**Key Features**:
- All colors are hardcoded - no automatic recalculation
- Manual overrides can be added/changed without affecting other VSPCs
- Script skips recalculation and refinement when all colors are hardcoded
- Perfect for incremental manual adjustments

**Workflow**:
1. All 32 VSPCs have colors hardcoded in `assign_vspc_colors.py`
2. To change a color, edit `MANUAL_COLOR_OVERRIDES` dictionary
3. Run `assign_vspc_colors.py` - it automatically:
   - Updates VSPC colors in `vspc_locations_colored.geojson`
   - Updates `vspc_color_mapping.json`
   - Automatically runs `assign_precinct_colors.py` to update precinct colors
4. Both VSPC and precinct GeoJSON files are generated with updated colors

## Files

### Scripts
- `assign_vspc_colors.py` - Main color assignment script (V13 version with hardcoded colors)
- `assign_precinct_colors.py` - Assigns precinct colors based on their assigned VSPC colors

### Input Files
- `vspc_locations.geojson` - VSPC location data (input for color assignment)
- `../VSPC - Precinct Distribution.csv` - Precinct-to-VSPC assignments
- `../../master_precincts.csv` - Precinct location data

### Output Files
- `vspc_locations_colored.geojson` - VSPC locations with assigned colors
- `vspc_color_mapping.json` - JSON mapping of VSPC names to colors
- `precinct_locations_colored.geojson` - Precinct locations with colors matching their assigned VSPC

## Usage

To generate the colored GeoJSON file:

```bash
cd v13/gis
python3 assign_vspc_colors.py
```

This will:
- Load all hardcoded color assignments
- Skip recalculation (all colors already assigned)
- Generate `vspc_locations_colored.geojson` and `vspc_color_mapping.json`
- Automatically run `assign_precinct_colors.py` to update precinct colors
- Generate `precinct_locations_colored.geojson` with colors matching assigned VSPCs

### Making Manual Color Changes

To change a VSPC's color:

1. Open `assign_vspc_colors.py`
2. Find the `MANUAL_COLOR_OVERRIDES` dictionary (around line 193)
3. Update the color for the desired VSPC:
   ```python
   "VSPC Name": "#HEXCOLOR",  # Your comment
   ```
4. Run `assign_vspc_colors.py` - both VSPC and precinct colors will update automatically

**Example**:
```python
MANUAL_COLOR_OVERRIDES = {
    ...
    "Trails Recreation Center": "#87CEEB",  # Light blue
    ...
}
```

### Precinct Color Assignment

Precinct colors are automatically assigned based on their assigned VSPC. When you change a VSPC color and run `assign_vspc_colors.py`, all precincts assigned to that VSPC will automatically get the new color.

**Manual precinct color update** (if needed):
```bash
cd v13/gis
python3 assign_precinct_colors.py
```

This script:
- Reads VSPC colors from `vspc_color_mapping.json`
- Reads precinct assignments from `../VSPC - Precinct Distribution.csv`
- Assigns each precinct the same color as its assigned VSPC
- Generates `precinct_locations_colored.geojson`

## Color Assignment Philosophy

V13 prioritizes:
- **Stability**: Colors don't change unless explicitly modified
- **Control**: Manual overrides don't trigger cascading changes
- **Simplicity**: Direct color assignment without complex algorithms
- **Consistency**: Precinct colors automatically match their assigned VSPC colors

## QGIS Usage

### VSPC Colors
1. Load `vspc_locations_colored.geojson` in QGIS
2. In Symbology, use 'Categorized' by 'name'
3. For each category, set the color to match the 'color' property
4. Or use 'Single Symbol' with data-defined color override using the 'color' field

### Precinct Colors
1. Load `precinct_locations_colored.geojson` in QGIS
2. In Symbology, use 'Categorized' by 'assigned_vspc'
3. For each category, set the color to match the 'color' property
4. Or use 'Single Symbol' with data-defined color override using the 'color' field

**Note**: Each precinct's color automatically matches its assigned VSPC's color. When you update a VSPC color in the script, all associated precincts update automatically.

## References

- V12 Backup: `../v12/gis/` (automatic color assignment)
- V11 Backup: `../v11/gis/` (RGB-based approach)
- Main GIS README: `../../gis/README.md`
