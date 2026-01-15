# V12 GIS Color Assignment

This directory contains the V12 version of the VSPC color assignment system, using an HSL-based palette selection approach.

## Migration from V11

**Date**: January 2025

**Purpose**: Improve color assignment by using HSL-based palette selection with hue-evenly-distributed colors.

### V11 Approach (Backup in `../v11/gis/`)
- RGB-based color distance calculations
- Explicit color family definitions
- Graph coloring with 2-hop neighbor checking
- Color distance thresholds: 250.0 (initial), 300.0 (refinement)
- Family separation: 15 miles minimum
- **Result**: 18 remaining same-family conflicts

### V12 Approach (Current)
V12 uses a hue-evenly-distributed color palette based on HSL color space combined with **concentric ring-based constraints** to avoid cyclical constraint problems.

**Color Selection Method**: Colors are selected using the HSL color chart from [Quackit HSL Color Chart](https://www.quackit.com/css/color/charts/hsl_color_chart.cfm), which provides:
- Systematic hue increments (5° steps)
- Visual color swatches
- Saturation and lightness variations
- HSL values for precise color selection

The palette is designed to have 32 colors evenly distributed around the color wheel (approximately 11.25° hue increments) to maximize visual distinction.

**Ring-Based Constraint System**: Instead of a single distance threshold (which creates cyclical problems), V12 uses concentric rings:
- **Immediate ring (< 8mi)**: STRICT - Different color families required
- **Middle ring (8-15mi)**: MODERATE - Same family OK if colors very different (>200 distance)
- **Far ring (> 15mi)**: RELAXED - Same family allowed

This prevents the cyclical problem where checking too far out makes assignment impossible, while still ensuring immediate neighbors are visually distinct.

See `IMPLEMENTATION_NOTES.md` for detailed documentation.

## Files

### Scripts
- `assign_vspc_colors.py` - Main color assignment script (V12 version with HSL-based palette)
- `export_gis_data.py` - GIS data export script

### Input Files
- `vspc_locations.geojson` - VSPC location data (input for color assignment)

### Output Files
- `vspc_locations_colored.geojson` - VSPC locations with assigned colors
- `vspc_color_mapping.json` - JSON mapping of VSPC names to colors

## Usage

To assign colors using the V12 HSL-based approach:

```bash
cd v12/gis
python3 assign_vspc_colors.py
```

This will generate:
- `vspc_locations_colored.geojson` - GeoJSON with color properties
- `vspc_color_mapping.json` - Color mapping for reference

## References

- HSL Color Chart: https://www.quackit.com/css/color/charts/hsl_color_chart.cfm
- V11 Backup: `../v11/gis/`
- Main GIS README: `../../gis/README.md`
