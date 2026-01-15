# GIS Data Export

This directory contains GeoJSON files exported for use in QGIS for visualizing VSPC and precinct distributions.

## Version History

The color assignment system has been versioned:

- **V11** (backup in `../v11/gis/`): RGB-based color distance with explicit color families
  - Used strict color distance thresholds (250.0/300.0)
  - Family separation: 15 miles minimum
  - Result: 18 remaining conflicts

- **V12** (backup in `../v12/gis/`): HSL-based palette selection
  - Uses hue-evenly-distributed colors from [Quackit HSL Color Chart](https://www.quackit.com/css/color/charts/hsl_color_chart.cfm)
  - 32 colors evenly spaced around color wheel (~11.25° increments)
  - Maximizes perceptual separation before applying geographic constraints
  - **Issue**: Manual overrides triggered full recalculation

- **V13** (active in `../v13/gis/`): Hardcoded color assignments with automatic precinct coloring
  - All 32 VSPC colors are hardcoded from V12 final output
  - Manual overrides can be added without triggering recalculation
  - Perfect for incremental manual adjustments
  - **Solution**: Stable colors, no whack-a-mole problem
  - **New**: Precinct colors automatically match their assigned VSPC colors

The current active color assignment scripts are in `v13/gis/`. The `v12/gis/` and `v11/gis/` directories contain backups for reference.

## Files

### `vspc_locations.geojson`
- **Description**: All VSPC (Voter Service Polling Center) locations
- **Features**: 32 VSPC points
- **Properties**:
  - `name`: VSPC name
  - `address`, `city`, `state`, `zip`: Full address
  - `latitude`, `longitude`: Coordinates

### `precinct_locations.geojson`
- **Description**: All precinct locations
- **Features**: 403 precinct points
- **Properties**:
  - `precinct`: Precinct number
  - `precinct_str`: Precinct as string
  - `voter_count_2022`: Voter count from 2022
  - `voter_count_current`: Current voter count
  - `us_cong`, `co_sen`, `co_hse`, `arap`, `comm`: District information
  - `latitude`, `longitude`: Coordinates
  - `hyperlink`: Link to precinct map PDF

### V13 Colored Files (in `v13/gis/`)
- **`vspc_locations_colored.geojson`**: VSPC locations with assigned colors
  - All VSPC location properties
  - `color`, `color_hex`: Assigned color for each VSPC
  
- **`precinct_locations_colored.geojson`**: Precinct locations with colors matching assigned VSPC
  - All precinct location properties
  - `assigned_vspc`: VSPC assigned to this precinct
  - `color`, `color_hex`: Color matching the assigned VSPC
  - `voters`, `nearest_vspc`, `distance_to_assigned_mi`, `reassigned`: Assignment data

### `v11_precinct_assignments.geojson`
- **Location**: `v11/gis/v11_precinct_assignments.geojson` (moved to v11 directory)
- **Description**: Precinct locations with v11 assignment data
- **Features**: 403 precinct points with assignment information
- **Properties**:
  - All precinct location properties
  - `assigned_vspc`: VSPC assigned in v11
  - `nearest_vspc`: Geographically nearest VSPC
  - `distance_to_nearest_mi`: Distance to nearest VSPC
  - `distance_to_assigned_mi`: Distance to assigned VSPC
  - `distance_difference_mi`: Difference between assigned and nearest
  - `reassigned`: Whether precinct was reassigned from nearest
  - `voters`: Voter count for this precinct
  - `voters_assigned`, `precincts_assigned`: Totals for assigned VSPC
  - `vspc_address`, `vspc_city`, `vspc_state`, `vspc_zip`: Assigned VSPC address
  - `vspc_latitude`, `vspc_longitude`: Assigned VSPC coordinates

## Usage in QGIS

1. **Open QGIS**
2. **Add Vector Layer**: Layer > Add Layer > Add Vector Layer
3. **Select GeoJSON files**: Browse to this directory and select the `.geojson` files
4. **Style the layers**:
   - **VSPC locations** (from `v13/gis/vspc_locations_colored.geojson`): Use point markers with data-defined color using the `color` property
   - **Precinct locations** (from `v13/gis/precinct_locations_colored.geojson`): Use point markers with data-defined color using the `color` property (automatically matches assigned VSPC)
   - **Precinct locations** (basic): Use point markers, color by `voter_count_current` (graduated colors)
   - **v11 assignments** (in `v11/gis/`): Use point markers, color by `assigned_vspc` (categorized colors), or use `reassigned` to highlight reassigned precincts

## Regenerating Files

### V13 Colored Files (Current)

To regenerate VSPC and precinct colored files:

```bash
cd v13/gis
python3 assign_vspc_colors.py
```

This will:
- Update VSPC colors in `vspc_locations_colored.geojson`
- Update `vspc_color_mapping.json`
- Automatically update precinct colors in `precinct_locations_colored.geojson`

To manually update only precinct colors:

```bash
cd v13/gis
python3 assign_precinct_colors.py
```

### Basic Export Files

To regenerate the basic GIS export files, run:

```bash
python3 gis/export_gis_data.py
```

This will update all GeoJSON files with the latest data from the master files and v11 assignments.
