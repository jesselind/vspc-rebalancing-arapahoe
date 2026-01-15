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

## How the Rebalancing Process Works

**Step 1: Calculate the target.** The system adds up all active voters across all precincts and divides by the number of VSPCs to determine the ideal number of voters each VSPC should handle.

**Step 2: Count current voters at each VSPC.** For each VSPC, the system adds up all the voters from every precinct currently assigned to that VSPC.

**Step 3: Identify overloaded and underloaded VSPCs.** Overloaded VSPCs have more voters than the target (plus a 25% tolerance), while underloaded VSPCs have fewer voters than the target (minus a 25% tolerance).

**Step 4: Start with the most overloaded VSPC.** The system finds the VSPC with the most voters and calculates how many excess voters it has.

**Step 5: Redistribute excess voters.** The system looks at all precincts assigned to the overloaded VSPC, starting with the largest precincts first. For each precinct, it finds the closest underloaded VSPC that can accept more voters. Precincts can only move away from their nearest VSPC, never closer. After each move, the system recalculates voter counts for all VSPCs.

**Step 6: Move to the next most overloaded VSPC.** Once the first VSPC is balanced, the system finds the next most overloaded VSPC and repeats the process.

**Step 7: Continue until balanced.** The system keeps repeating this process until all VSPCs are within the acceptable range, or until no more moves are possible.

**Step 8: Final result.** Each VSPC ends up with a voter count close to the target, with precincts assigned to reasonably close VSPCs. The system prioritizes balancing voter volume over keeping precincts at their nearest VSPC.

## Quick Start

### Prerequisites

- Python 3.7+
- Required packages: `pandas`, `numpy`

### Running the Current Version

```bash
# Generate current assignments
python generate_assignments.py
```

This will create output files in the `output/` directory:
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
├── README.md                          # This file (project overview)
├── VSPC_REBALANCING_CONTEXT.md       # Detailed technical documentation
│
├── generate_assignments.py           # CURRENT: Main script to generate assignments
├── master_precincts.csv              # Master precinct data (source of truth)
├── master_vspcs.csv                  # Master VSPC data (source of truth)
│
├── output/                            # CURRENT: Output files (CSV results)
│   ├── VSPC - Precinct Distribution.csv
│   ├── VSPC Locations.csv
│   └── Summary Statistics.csv
│
├── gis/                               # CURRENT: GIS tools and data
│   ├── assign_vspc_colors.py         # Assign colors to VSPCs
│   ├── assign_precinct_colors.py     # Assign colors to precincts
│   ├── vspc_locations_colored.geojson
│   ├── precinct_locations_colored.geojson
│   ├── QGIS_SETUP_GUIDE.md
│   └── README.md
│
├── scripts/                           # Utility scripts
│   ├── geocode_vspcs.py
│   └── geocode_high_precision.py
│
└── Archived Resources/                # Historical versions (v1-v14) and outdated files
    ├── v1/ ... v14/                   # HISTORICAL: Previous versions (for reference)
    └── [other archived files]
```

**Note:** This repository is now version-controlled. Historical versions (v1-v14) are preserved in `Archived Resources/` for reference. Current work uses version-agnostic files in the root directory. Use git history to track changes over time.

## Current Status

**Current Algorithm**: Ripple/cascade rebalancing (voter volume focused)

- **Total Precincts**: 403
- **Total VSPCs**: 32
- **Target**: ~13,000 voters per VSPC (±25% tolerance)
- **Algorithm**: Based on v14 (see version history in `VSPC_REBALANCING_CONTEXT.md`)

See `VSPC_REBALANCING_CONTEXT.md` for detailed statistics and version history.

## How It Works

### The Rebalancing Algorithm

The current algorithm (based on v14, which evolved from v11 ripple/cascade):

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

The project has evolved through multiple versions (v1-v14), all preserved in `Archived Resources/v1/` through `Archived Resources/v14/` for reference:

- **v1-v5**: Initial implementations and refinements
- **v6**: Voter-volume-based rebalancing (64% std dev improvement)
- **v8**: Added 6 new VSPCs, geographic constraint enforcement
- **v10-v11**: Ripple/cascade algorithm, master file system
- **v13**: Stable version with GIS color assignments
- **v14**: Final versioned iteration (algorithm improvements)

**Current state**: The codebase is now version-agnostic. The main script (`generate_assignments.py`) is based on v14's algorithm. Use git history to track changes going forward.

See `VSPC_REBALANCING_CONTEXT.md` for detailed version history and results.

## Contributing

When making changes:

1. **Edit the main script**: `generate_assignments.py` (version-agnostic)
2. **Keep master files unchanged**: `master_precincts.csv`, `master_vspcs.csv` are the source of truth
3. **Document changes**: Update `VSPC_REBALANCING_CONTEXT.md` with algorithm changes
4. **Test with current data**: Use the latest voter registration file
5. **Use git**: Commit changes with descriptive messages - version history is tracked in git

**Historical versions** (v1-v14) are preserved in `Archived Resources/` for reference. The current codebase is version-agnostic and uses git for version control.

## Documentation

- **`README.md`** (this file) - Project overview and quick start
- **`VSPC_REBALANCING_CONTEXT.md`** - Detailed technical documentation, algorithm details, version history
- **`gis/QGIS_SETUP_GUIDE.md`** - GIS visualization setup instructions
- Version-specific READMEs in `Archived Resources/vX/` directories

## License

[Add license information if applicable]

## Contact

[Add contact information if applicable]
