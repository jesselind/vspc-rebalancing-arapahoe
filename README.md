# Arapahoe County VSPC Rebalancing Project

A Python-based system for rebalancing voting precinct assignments to Voter Service & Polling Centers (VSPCs) in Arapahoe County, Colorado. This project optimizes voter distribution across 32 VSPCs to ensure balanced workloads while maintaining geographic proximity.

## Overview

### What is this project?

This project addresses a critical problem in election administration: **uneven voter distribution across polling centers**. Some VSPCs were handling 60+ precincts while others had only 1-2 precincts, creating severe workload imbalances. Additionally, precincts vary significantly in voter count (from ~0 to 2,000+ voters), so equal precinct counts don't mean equal workloads.

### What does it do?

The system:
1. **Loads precinct and VSPC data** from master files (403 precincts, 32 VSPCs)
2. **Calculates geographic assignments** (finds nearest VSPC for each precinct)
3. **Rebalances assignments** using algorithms that prioritize voter volume over precinct count
4. **Generates output files** with detailed assignment information, distances, and statistics
5. **Creates GIS visualizations** for mapping and analysis

### Key Features

- **Voter volume optimization**: Balances actual voter counts, not just precinct counts
- **Geographic constraints**: Ensures precincts don't move too far from their nearest VSPC
- **Multiple algorithm versions**: Iterative improvements from v1 through v14
- **Master data files**: Immutable source of truth for precincts and VSPCs
- **GIS integration**: QGIS-compatible GeoJSON files for visualization
- **Transparency**: Detailed output showing nearest vs. assigned VSPC, distances, and reassignment flags

## Quick Start

### Prerequisites

- Python 3.7+
- Required packages: `pandas`, `numpy`

### Running the Latest Version

```bash
# Generate v14 assignments (current development version)
cd v14
python generate_v14_ripple_rebalanced.py
```

This will create:
- `VSPC - Precinct Distribution.csv` - One row per precinct (403 rows)
- `VSPC Locations.csv` - One row per VSPC (32 rows)
- `Summary Statistics.csv` - Overall statistics

### Data Files

The system uses master files as the source of truth:

- **`master_precincts.csv`** - All 403 precincts with coordinates, voter counts, and district info
- **`master_vspcs.csv`** - All 32 VSPCs with addresses and coordinates
- **`CE-VR011B_EXTERNAL_20260113_021047_03.txt`** - Current voter registration data (January 2026)

> **Note:** All voter data used in this project is publicly available from the Arapahoe County Elections Department. The voter registration file and other voter lists can be downloaded from the [Arapahoe County Voter Lists page](https://www.arapahoeco.gov/your_county/arapahoevotes/records_data/voter_lists.php). All information contained in these lists is considered public under state law.

## Project Structure

```
CEI/
├── README.md                          # This file
├── VSPC_REBALANCING_CONTEXT.md       # Detailed technical documentation
├── master_precincts.csv              # Master precinct data (source of truth)
├── master_vspcs.csv                   # Master VSPC data (source of truth)
├── v14/                               # Current development version
│   ├── generate_v14_ripple_rebalanced.py
│   └── [output CSV files]
├── v13/                               # Previous stable version
├── v11/                               # Previous version with GIS tools
├── gis/                               # GIS data and QGIS setup guide
└── [other version directories]
```

## Current Status

**Latest Version: v14** (development)

- **Total Precincts**: 403
- **Total VSPCs**: 32
- **Algorithm**: Ripple/cascade rebalancing (voter volume focused)
- **Target**: ~13,000 voters per VSPC (±25% tolerance)

See `VSPC_REBALANCING_CONTEXT.md` for detailed statistics and version history.

## How It Works

### The Rebalancing Algorithm

The current algorithm (v14, based on v11 ripple/cascade):

1. **Geographic Baseline**: Calculates nearest VSPC for each precinct
2. **Identify Overloads**: Finds VSPCs with voter counts above target + 25%
3. **Cascade Redistribution**: 
   - Processes largest VSPCs first
   - Moves precincts to underloaded VSPCs (below target - 25%)
   - Precincts can move to 2nd-10th closest VSPC (away from nearest)
   - No distance limits - algorithm balances organically
4. **Iterate**: Recalculates and continues until balanced

### Key Constraints

- Precincts can only move **away from their nearest VSPC** (to 2nd, 3rd, etc. closest)
- Moves only from **overloaded** to **underloaded** VSPCs
- Geographic proximity maintained (no arbitrary distance limits)

## Output Files

### VSPC - Precinct Distribution.csv

One row per precinct (403 rows) with:
- Precinct number and voter count
- **Nearest VSPC** (geographic baseline) and distance
- **Assigned VSPC** (rebalanced assignment) and distance
- Distance difference (impact of rebalancing)
- Reassigned flag (True/False)
- VSPC address and contact info
- Link to precinct map PDF

### VSPC Locations.csv

One row per VSPC (32 rows) with:
- VSPC name
- Total voters assigned
- Total precincts assigned
- Address information

### Summary Statistics.csv

Overall statistics:
- Total VSPCs
- Total precincts
- Total precincts reassigned

## GIS Visualization

The project includes GIS tools for mapping:

- **QGIS Setup Guide**: `gis/QGIS_SETUP_GUIDE.md`
- **GeoJSON files**: Precinct and VSPC locations with colors
- **Color coding**: Each VSPC has a unique color; precincts match their assigned VSPC

> **Additional GIS Data:** Arapahoe County provides open GIS data downloads including election precincts, county boundaries, and other geographic layers. Data can be downloaded from the [Arapahoe County GIS Data Download page](https://gis.arapahoegov.com/datadownload/). All data is updated nightly and reflects the latest version in use at the county.

## Version History

The project has evolved through multiple versions:

- **v1-v5**: Initial implementations and refinements
- **v6**: Voter-volume-based rebalancing (64% std dev improvement)
- **v8**: Added 6 new VSPCs, geographic constraint enforcement
- **v10-v11**: Ripple/cascade algorithm, master file system
- **v13**: Stable version with GIS color assignments
- **v14**: Current development version (algorithm improvements)

See `VSPC_REBALANCING_CONTEXT.md` for detailed version history and results.

## Contributing

When making changes:

1. Work in the appropriate version directory (currently `v14/`)
2. Keep master files (`master_precincts.csv`, `master_vspcs.csv`) unchanged
3. Document algorithm changes in `VSPC_REBALANCING_CONTEXT.md`
4. Test with current voter registration data

## Documentation

- **`README.md`** (this file) - Project overview and quick start
- **`VSPC_REBALANCING_CONTEXT.md`** - Detailed technical documentation, algorithm details, version history
- **`gis/QGIS_SETUP_GUIDE.md`** - GIS visualization setup instructions
- Version-specific READMEs in each version directory

## License

[Add license information if applicable]

## Contact

[Add contact information if applicable]
