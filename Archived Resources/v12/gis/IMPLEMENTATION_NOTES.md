# V12 Implementation Notes

## Current Status

V12 uses **HSL-based palette selection** with **concentric ring-based constraints** to avoid the cyclical problem of checking too far out.

## Ring-Based Constraint System

The algorithm uses concentric rings around each VSPC with different strictness levels:

### Ring Distances (Current Settings)
- **Immediate ring**: < 8 miles
  - **Constraint**: STRICT - Different color families required
  - **Purpose**: Ensure immediate neighbors are visually distinct
  
- **Middle ring**: 8-15 miles
  - **Constraint**: MODERATE - Same family OK if colors are very different (>200 color distance)
  - **Purpose**: Allow some flexibility while maintaining visual distinction
  
- **Far ring**: > 15 miles
  - **Constraint**: RELAXED - Same family allowed
  - **Purpose**: Avoid cyclical constraint problems

### Why Ring-Based?

The original approach used a single distance threshold (15 miles) for all constraints, which created a cyclical problem:
- If we check too close: miss conflicts
- If we check too far: create impossible constraints that prevent any valid assignment

The ring-based approach solves this by:
1. Being strict where it matters most (immediate neighbors)
2. Gradually relaxing constraints with distance
3. Avoiding the cyclical problem by not enforcing strict rules at far distances

## Implementation Details

### Key Functions

- `get_vspcs_by_rings()`: Organizes nearby VSPCs into immediate/middle/far rings
- `check_color_constraint_by_ring()`: Checks if two colors violate constraints based on their distance
- Ring distances are configurable (currently 8mi immediate, 15mi middle)

### HSL Palette

- 32 colors evenly distributed around HSL color wheel
- 11.25° hue increments (360° / 32)
- 100% saturation, 50% lightness for maximum vibrancy
- Color families based on 30° hue ranges

## Configuration

Ring distances can be adjusted in the code:
- `immediate_ring` parameter (default: 8.0 miles)
- `middle_ring` parameter (default: 15.0 miles)

These are used in:
- `get_vspcs_by_rings()`
- `check_color_constraint_by_ring()`
- All calls to these functions throughout the algorithm

## Results

Current performance with 8mi/15mi rings:
- Ring constraint violations: ~42 (varies by run)
- Unique colors: ~25/32 (some reuse due to constraints)
- All VSPCs have colors assigned

## Next Steps / Future Improvements

- Tune ring distances based on VSPC geographic distribution
- Adjust middle ring similarity threshold (currently 200 color distance)
- Consider adding more rings for finer-grained control
- Test different HSL saturation/lightness combinations

## References

- HSL Color Chart: https://www.quackit.com/css/color/charts/hsl_color_chart.cfm
- V11 Backup: `../v11/gis/`
