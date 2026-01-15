# Trails Recreation Center Rebalancing Analysis

**Current Status:**
- Precincts assigned: 73
- Voters assigned: 74,978
- Target voters: 12,574
- Over target by: 496.3%

**Reassignment Opportunities:**
- Precincts with potential targets: 73
- Precincts with underloaded targets: 12

**QGIS Files Generated:**
- precincts.geojson - All precinct points (red = Trails, green = reassigned, gray = other)
- vspcs.geojson - All VSPC locations (red = Trails, orange = overloaded, green = underloaded)
- reassignment_opportunities.geojson - Lines showing potential moves (green = to underloaded VSPC)
- distance_buffers.geojson - 10km, 20km, 30km buffers around Trails Recreation Center
- trails_reassignment_analysis.csv - Detailed analysis of each precinct

**QGIS Styling Suggestions:**
- Precincts: Use 'color' field for styling
- VSPCs: Use 'color' field, size by 'voters'
- Reassignment lines: Use 'color' field, width by 'voters'
- Buffers: Semi-transparent fill, no outline