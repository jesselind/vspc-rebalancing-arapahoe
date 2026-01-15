# Historical Version: v14

This directory contains **v14**, the final manually versioned iteration of the VSPC rebalancing system.

## Status: Historical Reference

**This version is preserved for historical reference only.** The current codebase uses version-agnostic files in the root directory.

- **Main script**: `generate_v14_ripple_rebalanced.py` → Now `../generate_assignments.py`
- **Output location**: This directory → Now `../output/`

## What Changed in v14

- Based on v11 ripple/cascade algorithm
- Fixed: Uses Voter_Count from geographic file as fallback for newer precincts not in 2022 data
- Ripple/cascade rebalancing with voter volume focus
- Target: ~13,000 voters per VSPC (±25% tolerance)

## Migration to Version-Agnostic Structure

With the introduction of source control, manual versioning is no longer needed. The current system:

1. Uses `generate_assignments.py` in the root directory
2. Outputs to `output/` directory
3. Tracks changes via git history
4. Preserves all historical versions (v1-v14) for reference

## Files in This Directory

- `generate_v14_ripple_rebalanced.py` - Original v14 script (historical)
- `Summary Statistics.csv` - v14 output (historical)
- `VSPC - Precinct Distribution.csv` - v14 output (historical)
- `VSPC Locations.csv` - v14 output (historical)

**Note**: These files are preserved for reference. For current work, use the files in the root directory.
