# VSPC Rebalancing Project - Technical Documentation

> **Note**: This is a technical reference document. For project overview and quick start, see [README.md](README.md).

This document contains detailed technical information about the VSPC rebalancing algorithms, version history, implementation details, and progress tracking.

## Current Status

**Last Updated:** January 2025  
**Current System:** Version-agnostic (based on v14 algorithm)  
**Historical Versions:** v1-v14 preserved in `Archived Resources/`

### Summary

The project uses a ripple/cascade rebalancing algorithm focused on **voter volume distribution**. The algorithm processes VSPCs in order of size (largest first), fully distributing each VSPC's excess voters through ripple/cascade before moving to the next largest. **All scripts use master files** (`master_precincts.csv` and `master_vspcs.csv`) as the immutable source of truth, making the system version-agnostic. **Current voter registration data** (January 2026) is used as the primary source for voter counts.

### Current System (Version-Agnostic, Based on v14)

- **Total Precincts**: 403
- **Total VSPCs**: 32 (26 existing + 6 new)
- **Total Voters**: ~419,000+ (current active voters from January 2026 registration)
- **Target voters per VSPC**: ~13,000 (±25% tolerance)
- **Algorithm**: Largest-first ripple/cascade - processes VSPCs in order of size, fully distributes each before moving to next
- **Script**: `generate_assignments.py` (root directory)
- **Historical v14 script**: `Archived Resources/v14/generate_v14_ripple_rebalanced.py`
- **Status**: Current production version

### Key Statistics

**V11 (Current - Ripple/Cascade Algorithm, Voter Volume Focused)**
- Uses master files (`master_precincts.csv`, `master_vspcs.csv`) as immutable source of truth
- Current voter registration (January 2026) as primary voter count source
- 2022 voter data as fallback (incorporated into master file)

**V11 Results:**
- Uses same ripple/cascade algorithm as V10
- All 32 VSPCs included
- Current voter registration data (January 2026) as primary source

**V10 Results:**
- Trails Recreation Center: 91,711 → 19,124 voters (79% reduction, 52% over target)
- 34.4% of VSPCs within ±25% of target voter volume
- 12 VSPCs still overloaded (45-54% over target) - ripple constraint limits further moves
- Standard deviation: 6,742 voters

**V8 Results (32 VSPCs):**
- Total Voters: 402,357
- Target voters per VSPC: ~12,574
- Standard Deviation: 3,898 (35.4% better than V6)
- Coefficient of Variation: 31.0% (20.5% better than V6)
- VSPCs within ±25% of target: 28/32 (87.5%)
- Precincts reassigned: 68 (16.9%)
- Max voters per VSPC: 15,693 (The Avenue Church)
- Min voters per VSPC: 1,250 (Aurora Public Schools Educational Service Center 4)
- Range: 14,443 (41% better than V6)
- Trails Recreation Center reduced from 91,711 to 15,217 voters (83.4% reduction)

**V6 Results (26 VSPCs):**
- Total Voters: 402,357
- Target voters per VSPC: ~15,475
- Standard Deviation: 6,031
- Coefficient of Variation: 39.0%
- VSPCs within ±25% of target: 17/26 (65.4%)
- Precincts moved: 70 (17.4%)
- Max precincts per VSPC: 31 (was 70)
- Max voters per VSPC: 28,927 (was 79,056)

## Problem Statement

The current VSPC (Voter Service & Polling Center) rebalancing only considers **precinct count** (~12 per VSPC) but **ignores voter volume**. This creates severe workload imbalances:

- Some VSPCs handle **60+ precincts** while others have only **1-2 precincts**
- Precincts vary significantly in voter count (from ~0 to 2,000+ voters)
- Current rebalancing targets equal precinct counts, not equal voter workloads

## Solution Approach

Rebalance precincts to prioritize **voter volume** while maintaining:
- Geographic constraints (only reassign to second-closest VSPC)
- No east/west cross-county reassignments
- Rural VSPCs may exceed targets (geographic necessity)

## Data Structure

### Master Files (Immutable Source of Truth)

1. **`master_precincts.csv`** - Master precinct data file
   - Contains all 403 precincts with immutable data:
     - Precinct identifiers: `PRECINCT`, `PRECINCT_STR`, `COLO_PREC`
     - Coordinates: `Precinct_Longitude`, `Precinct_Latitude` (from precinct_centroids.csv)
     - District info: `US_CONG`, `CO_SEN`, `CO_HSE`, `ARAP`, `COMM`
     - HYPERLINK to precinct map PDFs
     - Voter counts: `Voter_Count_2022` (from 2022 Precinct Table), `Voter_Count_Current` (from current voter registration)
   - Version-agnostic - used by all scripts

2. **`master_vspcs.csv`** - Master VSPC data file
   - Contains all 32 VSPCs (26 existing + 6 new) with immutable data:
     - VSPC names
     - Addresses: `Address`, `City`, `State`, `ZIP`
     - Coordinates: `VSPC_Latitude`, `VSPC_Longitude` (high-precision coordinates from Google Maps, 14-15 decimal places)
   - Version-agnostic - used by all scripts
   - **Updated**: All coordinates verified and updated with high-precision Google Maps coordinates (matching Arapahoe Community College precision)

### Source Data Files (Used to Build Master Files)

**Note:** These source files have been archived in `Archived Resources/` directory as they are no longer directly used by scripts. All data has been incorporated into the master files.

1. **Current Voter Registration**: `CE-VR011B_EXTERNAL_20260113_021047_03.txt`
   - Primary source for current active voter counts (January 2026)
   - Pipe-delimited file with individual voter records
   - Extracts last 3 digits of PRECINCT column to match precinct numbers
   - Counts only "Active" status voters
   - **Usage**: Scripts load this file directly to get current voter counts, then merge with master_precincts.csv

2. **2022 Voter Data**: `Archived Resources/2022 Precinct Table (4) (1).csv`
   - Historical baseline voter counts (as of 2022)
   - Used as fallback for precincts not in current registration
   - **How master file was created**: Data from this file was incorporated into `master_precincts.csv` as `Voter_Count_2022` column
   - **Process**: The "Voter Count" column from this file was matched to precincts by precinct number and added to master_precincts.csv

3. **Precinct Centroids**: `Archived Resources/precinct_centroids.csv` (archived - data incorporated into master file)
   - Source of truth for precinct coordinates
   - X = Longitude, Y = Latitude
   - **How master file was created**: Coordinate data (X, Y columns) was incorporated into `master_precincts.csv` as `Precinct_Longitude` and `Precinct_Latitude` columns
   - **Process**: Coordinates were matched by precinct number and merged into master_precincts.csv

### Output Files (to be generated)

Following v5 structure:
- `VSPC_v5 - Full_Assignments_Rebalanced.csv` (updated with voter-volume-based assignments)
- `VSPC_v5 - VSPC_Precinct_Map_Rebalanced.csv` (simplified view)
- `VSPC_v5 - VSPC_Summary.csv` (summary statistics)

## Constraints & Rules

### Geographic Constraints
1. **Second-closest VSPC only**: Precincts can only be reassigned to their second-closest VSPC (not third, fourth, etc.)
2. **No east/west cross-county**: Cannot reassign across certain county boundaries (needs validation)
3. **Distance calculation**: Use Haversine formula for lat/lon distance

### Rural VSPC Exception
- Rural VSPCs (those with ≤3 precincts in geographic assignment) may exceed target voter counts
- These are protected from having precincts moved away

### Rebalancing Targets
- **Primary goal**: Balance voter volume across VSPCs
- **Target**: Total voters / Number of VSPCs = average per VSPC
  - V6: Total voters / 26 VSPCs = ~15,475 per VSPC
  - V8: Total voters / 32 VSPCs = ~12,574 per VSPC
- **Tolerance**: ±25% of target (configurable)
- **Secondary goal**: Minimize precinct count variance (but voter volume takes priority)

## Technical Implementation

### Python Script: `Archived Resources/v10/generate_v10_ripple_rebalanced.py` (V10 - Historical)

**Purpose:** Generate V8 spreadsheet with all 32 VSPCs and improved rebalancing

**Key Features:**
1. **Adds 6 new VSPCs** from 2026 election list with geocoded coordinates
2. **Recalculates nearest VSPC** for each precinct with all 32 VSPCs (geographic baseline)
3. **Improved rebalancing algorithm** with more aggressive parameters
4. **Enhanced output** with comprehensive transparency columns:
   - Nearest VSPC and distance (geographic baseline)
   - Assigned VSPC and distance (rebalanced assignment)
   - Distance difference (impact of rebalancing)
   - Reassigned flag (True/False)

**Process:**
1. Load existing geographic assignments (26 VSPCs)
2. Add 6 new VSPCs with coordinates
3. Recalculate nearest VSPC for each precinct (geographic baseline with 32 VSPCs)
4. Run improved rebalancing algorithm
5. Calculate distances to both nearest and assigned VSPCs
6. Generate output files with all transparency columns

**Output Files (Historical - in `Archived Resources/v8/`):**
- `VSPC - Precinct Distribution.csv` - One row per precinct with:
  - Nearest VSPC and distance (geographic baseline)
  - Assigned VSPC and distance (rebalanced)
  - Distance difference and reassigned flag
  - All distances formatted to 2 decimal places in CSV output (full precision maintained in calculations)
- `VSPC Summary.csv` - One row per VSPC with totals

### Python Script: `generate_v6_spreadsheet.py`

**Dependencies:**
- pandas
- numpy
- csv (standard library)

**Key Functions:**
1. `haversine()` - Calculate distance between two lat/lon points (in km, converted to miles)
2. `find_vspc_distances()` - Find all VSPC distances for a precinct, return sorted list
3. `load_voter_registration_data()` - Load current active voters from registration file
4. `load_and_prepare_data()` - Load master files and prepare precinct/VSPC data
5. `add_new_vspcs_to_assignments()` - Calculate initial VSPC assignments from master files
6. `rebalance_by_ripple_cascade()` - Ripple/cascade rebalancing algorithm focused on voter volume

**Algorithm (V10):**
1. Load master precincts file (immutable data: coordinates, voter counts, district info)
2. Load master VSPCs file (all 32 VSPCs with coordinates and addresses)
3. Load current voter registration data (primary source for active voters)
4. Calculate initial geographic assignment (nearest VSPC for each precinct)
5. Calculate target voter count per VSPC (total voters / 32 VSPCs)
6. Run ripple/cascade rebalancing:
   - Process VSPCs largest-first (by voter count)
   - Fully distribute each VSPC's excess voters before moving to next
   - Recalculate "next largest" after each distribution
   - Precincts can move to 2nd-10th closest VSPC (no distance limit)
   - Moves from overloaded (> target + 25%) to underloaded (< target - 25%) VSPCs
   - For extreme overloads, allows moves to VSPCs up to 150% of target
7. Generate V10 output files with transparency columns

**Rebalancing Parameters (V6):**
- TARGET_TOLERANCE = 0.25 (25%)
- MAX_ITERATIONS = 300
- RURAL_VSPC_THRESHOLD = 3
- MAX_CLOSEST_VSPCS = 8
- MIN_DISTANCE_KM = 50

**Rebalancing Parameters (V10 - Current):**
- TARGET_TOLERANCE = 0.25 (25%)
- MAX_ITERATIONS = 1000 (higher limit for ripple effect)
- MAX_CLOSEST_VSPCS_TO_CHECK = 10 (allows moves to 2nd-10th closest VSPC, no distance limit)
- **Algorithm**: Ripple/cascade approach - processes largest VSPCs first, fully distributes each before moving to next
- **Data Sources**: Uses master files (`master_precincts.csv`, `master_vspcs.csv`) as immutable source of truth
- **Voter Counts**: Primary source is current voter registration file, with 2022 data as fallback (both in master_precincts.csv)

### Address Validation Script: `fix_sanity_check.py`

**Purpose:** Creates sanity check CSV with correct VSPC addresses from official source

**Key Features:**
- Uses official Arapahoe County website addresses
- Calculates distances using VSPC coordinates (geocoded from addresses)
- Includes City, State, ZIP columns
- Verifies all addresses are correct and unique per VSPC
- **VSPC Coordinates**: All 26 VSPC coordinates geocoded using OpenStreetMap/Nominatim for accuracy
- **Distance Calculation**: Uses Haversine formula with corrected VSPC coordinates
- **Column Headers**: Renamed to be Google Sheets friendly (spaces allowed, descriptive names)

## Progress Tracking

### Completed
- [x] Problem analysis and solution approach defined
- [x] Data structure documented
- [x] Context file created
- [x] Python script created and adapted for v5 structure (`rebalance_vspc_v5.py`)
- [x] Voter data validation and merging
- [x] Distance calculation implementation (Haversine)
- [x] Rebalancing algorithm implementation
- [x] Output file generation (matching v5 structure)

### In Progress
- [ ] Manual review of sanity check CSV in Google Sheets
- [ ] Final validation of assignments

### Completed (V10)
- [x] Created master files (`master_precincts.csv`, `master_vspcs.csv`) as immutable source of truth
- [x] Updated all scripts to use master files (version-agnostic)
- [x] Integrated current voter registration data (January 2026) as primary voter count source
- [x] Integrated 2022 voter data as fallback in master file
- [x] Ripple/cascade rebalancing algorithm implemented
- [x] Generated V10 files with enhanced transparency columns
- [x] All 32 VSPCs have precincts assigned

### Pending
- [ ] Any manual adjustments based on review
- [ ] Final approval of v10 assignments

## File Locations

**Workspace Root:**
```
/Users/jesselind/Library/Mobile Documents/com~apple~CloudDocs/ACR/CEI/
```

**Key Files:**
- **Master Files (Immutable Source of Truth):**
  - `master_precincts.csv` - All precinct data (coordinates, voter counts, district info)
    - **Created from**: 
      - `precinct_centroids.csv` (coordinates: X→Longitude, Y→Latitude)
      - `Archived Resources/2022 Precinct Table (4) (1).csv` (2022 voter counts: "Voter Count" column → `Voter_Count_2022`)
      - District data from original sources (US_CONG, CO_SEN, CO_HSE, ARAP, COMM)
    - **Process**: Merged by precinct number (PRECINCT column) to combine coordinates, 2022 voter counts, and district information
  - `master_vspcs.csv` - All 32 VSPC data (coordinates, addresses)
    - **Created from**: Official Arapahoe County VSPC list (https://www.arapahoeco.gov/your_county/arapahoevotes/voting_locations/voter_service_polling_centers.php)
    - **Process**: VSPC names and addresses from official source, coordinates manually verified and updated with high-precision Google Maps coordinates (14-15 decimal places)
    - **Updated**: All coordinates verified and corrected with Google Maps for maximum accuracy
- **Source Data Files:**
  - Current voter registration: `CE-VR011B_EXTERNAL_20260113_021047_03.txt` (January 2026) - **Active, used by scripts**
  - Historical voter data: `Archived Resources/2022 Precinct Table (4) (1).csv` (incorporated into master file)
  - Precinct centroids: `Archived Resources/precinct_centroids.csv` (incorporated into master file) - **Archived** ✅
- **Scripts:**
  - `generate_assignments.py` ✅ Current generator (uses master files, based on v14)
  - Historical scripts preserved in `Archived Resources/vX/` directories:
    - `Archived Resources/v10/generate_v10_ripple_rebalanced.py` ✅ V10 generator
    - `Archived Resources/v11/generate_v11_ripple_rebalanced.py` ✅ V11 generator
    - `Archived Resources/v8/analyze_trails_rebalancing.py` ✅ V8-specific analysis tool
  - `Archived Resources/generate_qgis_visualization.py` ✅ Archived (uses master files)
- **Output:**
  - **Current output directory: `output/` ✅ Created with 3 CSV files (current)**
    - `VSPC - Precinct Distribution.csv` - One row per precinct
    - `VSPC Locations.csv` - One row per VSPC
    - `Summary Statistics.csv` - Overall statistics
  - **Historical outputs**: Preserved in `Archived Resources/vX/` directories for reference
- Context: `VSPC_REBALANCING_CONTEXT.md` (this file)

## Notes & Considerations

1. **Voter Count Data**: ✅ Validated - Using `2022 Precinct Table (4) (1).csv` as source of truth

2. **East/West Boundaries**: ✅ Validated - Geographic sanity check completed. Cross-county constraints implemented to prevent opposite quadrant moves (SW↔NE, NW↔SE). Precinct 132 issue resolved - now correctly assigned to Glendale instead of MLK Library.

3. **Rural VSPC Identification**: Currently defined as VSPCs with ≤3 precincts in geographic assignment. Working as intended.

4. **Precinct Number Matching**: ✅ Resolved - Using 3-digit `PRECINCT` column throughout

5. **Iteration Limits**: ✅ Tuned - Algorithm runs up to 300 iterations with progress tracking

6. **VSPC Addresses**: ✅ Fixed - Created lookup table from official Arapahoe County website. All addresses verified and corrected in sanity check file.

7. **VSPC Coordinates**: ✅ Updated with High-Precision Google Maps Coordinates - All 32 VSPC coordinates updated with high-precision Google Maps coordinates (14-15 decimal places, matching Arapahoe Community College precision). All coordinates manually verified from Google Maps for maximum accuracy. Previously incorrect coordinates have been corrected (some were off by 1-8 km).

8. **Sanity Check File Format**: ✅ Optimized for Google Sheets - Column headers renamed to be user-friendly:
   - `Precinct_Number` → `Precinct`
   - `Precinct_Voters` → `Voters`
   - `VSPC_Name` → `Voter Service Polling Center (VSPC)`
   - `VSPC_Total_Voters` → `VSPC Total Voters`
   - `VSPC_Address` → `Address`
   - `VSPC_City` → `City`
   - `VSPC_State` → `State`
   - `VSPC_ZIP` → `Zip`
   - `Distance_Miles` → `Distance From Precinct (mi.)`
   - Column order: Precinct, Voters, Voter Service Polling Center (VSPC), VSPC Total Voters, Address, City, State, Zip, Distance From Precinct (mi.)

7. **Rebalancing Results**:
   - The Avenue Church: 70 → 31 precincts (still highest but manageable)
   - Max voters: 79,056 → 28,927
   - Standard deviation: 64% improvement
   - Average distance increase: 0.60 miles
   - Max distance: 16.27 miles (no assignments >20 miles)

## Next Steps

1. ✅ Create Python script adapted for v5 structure
2. ✅ Create v6 spreadsheet generator script
3. ✅ Run `generate_v6_spreadsheet.py` to create all v6 CSV files
4. ✅ Import CSV files into Google Sheets (one file = one tab)
5. ✅ Review the rebalanced distribution
6. ✅ Validate geographic constraints (no east/west cross-assignments found)
7. ✅ Create sanity check CSV with correct addresses
8. [ ] Manual review of sanity check CSV in Google Sheets
9. [ ] Final approval and any adjustments

## Future Planning: Area Organization and Polling Stations

### Area Definition and Organization

**Concept:** Organize precincts into Areas based on VSPCs for polling station management.

**Requirements:**

1. **Area Definition:**
   - Areas should be defined by the ~32 VSPCs listed for the 2026 election
   - Reference: https://www.arapahoeco.gov/your_county/arapahoevotes/voting_locations/voter_service_polling_centers.php
   - Rationale: Since polling places cannot be set up within each precinct, the plan is to establish approximately 12 polling stations within each of these county-approved VSPCs

2. **Precinct Assignment to Areas:**
   - Assign precincts to areas as evenly as possible
   - Consider aligning with existing GOP District Captain assignments to minimize confusion
   - This alignment may help maintain consistency with existing organizational structure

3. **Spreadsheet Structure:**
   - Create a spreadsheet listing:
     - Each area (VSPC)
     - Precincts assigned to each area
     - Area Lead (one per area)
     - Precinct Lead (one per precinct)
     - At least 10 spaces for hand counters per precinct
     - Note: Precinct Lead can be counted as one of the 10 hand counters

4. **Next Actions:**
   - Generate the area/precinct assignment list
   - Once list is ready, names will be added to Area Lead, Precinct Lead, and hand counter positions

**Status:** [ ] Pending - Area organization spreadsheet to be created

## V6 Spreadsheet Structure

The v6 spreadsheet consists of 8 CSV files (one per tab):

1. **Column_Legend.csv** - Column definitions (from v3 format)
2. **Data_Dictionary.csv** - Column definitions (from v5 format)
3. **Full_Assignments_Geo.csv** - Geographic assignments with all columns
   - Includes Secondary column (from v3)
4. **Full_Assignments_Rebalanced.csv** - Voter-volume-based rebalanced assignments
   - Includes Secondary column (from v3)
5. **Rulebook.csv** - Updated to reflect voter-volume-based rebalancing
6. **VSPC_Precinct_Map_Geo.csv** - Simplified geographic map
   - **CRITICAL**: Includes PRECINCT column (v5 was missing this!)
7. **VSPC_Precinct_Map_Rebalanced.csv** - Simplified rebalanced map
   - **CRITICAL**: Includes PRECINCT column (v5 was missing this!)
8. **VSPC_Summary.csv** - Summary with precinct counts AND voter counts

### Additional Files

- **VSPC_v6 - Sanity_Check.csv** - Manual review file with:
  - Precinct number, precinct voters, VSPC total voters
  - VSPC name, address, city, state, ZIP (all verified against official source)
  - Distance in miles from precinct to VSPC (calculated using geocoded VSPC coordinates)
  - **Column headers optimized for Google Sheets** (spaces allowed, descriptive names)
  - **All VSPC coordinates geocoded** for accurate distance calculations

### Key Improvements: Best of v3 + v5

**From v3 (what v5 was missing):**
- PRECINCT column in VSPC_Precinct_Map files - shows which precincts belong to each VSPC
- Secondary column in Full_Assignments - shows second-closest VSPC

**From v5:**
- Voter counts in all files
- Complete data structure

**New in v6:**
- Voter-volume-based rebalancing (64% std dev improvement)
- Voter counts in Summary file
- Aggressive rebalancing algorithm (allows moves to 2nd-8th closest VSPC)
- Geographic sanity check validation
- Address validation against official Arapahoe County website
- VSPC coordinate geocoding (all 26 VSPCs geocoded using OpenStreetMap/Nominatim)
- Google Sheets-optimized column headers in sanity check file

**To create v6:** Run `python v6/generate_v6_spreadsheet.py` ✅ **Already completed**

**New in v8:**
- **All 32 VSPCs included** (26 existing + 6 new from 2026 election list)
- **Geographic constraint enforcement** (cross-county guardrails):
  - Prevents opposite quadrant moves (SW↔NE, NW↔SE) to avoid cross-county reassignments
  - Uses quadrant analysis to detect and prevent unreasonable reassignments (e.g., precinct 132 issue fixed)
  - Example: Precinct 132 correctly assigned to Glendale (NW) instead of MLK Library (NE)
- **Simplified rebalancing algorithm** (reverted to proven v6 approach):
  - Moves precincts from overloaded to underloaded VSPCs only
  - Moves to 2nd-4th closest VSPC (proven to work)
  - Distance limit 30km (~18.6 miles) for reasonable geographic proximity
  - Removed complex percentage-based constraints that weren't working
- **Known Geographic Constraint**: Trails Recreation Center has 73 precincts assigned because it's geographically the nearest VSPC for many precincts. This is a geographic reality, not an algorithm failure.
- **Enhanced transparency columns**:
  - "Nearest VSPC" - Geographic baseline (closest VSPC)
  - "Distance to Nearest VSPC (mi.)" - Distance to closest VSPC
  - "Assigned VSPC" - Final rebalanced assignment (renamed from "Voter Service Polling Center")
  - "Distance to Assigned VSPC (mi.)" - Distance to assigned VSPC
  - "Distance Difference (mi.)" - Shows impact of rebalancing (assigned - nearest)
  - "Reassigned" - True/False flag for easy filtering
- **Improved column names**: "Voters Assigned" and "Precincts Assigned" (more intuitive)
- **Distance formatting**: All distances formatted to 2 decimal places in CSV output (e.g., 0.00, 1.00, 5.30) for consistent display, while maintaining full precision in all calculations
- **Geographic baseline recalculation**: First recalculates nearest VSPC with all 32 VSPCs, then rebalances
- All 6 new VSPCs geocoded and included in assignments

**To create v8:** Run `python v8/generate_v8_rebalanced.py` ✅ **Already completed**

**To create v10:** Run `python v10/generate_v10_ripple_rebalanced.py` ✅
**To create v11:** Run `python v11/generate_v11_ripple_rebalanced.py` ✅
**To create v13:** Use v13 CSV files (stable version)
**To create v14:** Run `python v14/generate_v14_ripple_rebalanced.py` (development)

## V10 - Ripple/Cascade Algorithm (Current) - Voter Volume Focused

**Status:** ✅ Completed

**Approach:** Revolutionary ripple/cascade rebalancing algorithm that prioritizes **voter volume distribution** over precinct count. Processes VSPCs in order of size (largest first), fully distributing each VSPC's excess voters before moving to the next largest.

**Key Principles:**
1. **Voter volume focused** - prioritizes balancing voter count, not precinct count
2. **Largest-first processing**: Find largest VSPC → fully distribute → recalculate next largest
3. Each precinct uses its **nearest VSPC as reference point** (geographic baseline)
4. Precincts can only move **AWAY from their nearest VSPC** (to 2nd, 3rd, 4th, etc. closest)
5. **No distance limits** - ripple sorts itself out organically
6. Moves from **overloaded** (voters > target + 25%) to **underloaded** (voters < target - 25%) VSPCs
7. For extreme overloads (>2x target), allows moves to VSPCs up to 150% of target
8. Processes precincts **largest-first** within each VSPC

**Algorithm Flow:**
1. Calculate target voters per VSPC (total voters / 32 VSPCs)
2. Find the **largest VSPC** (by voter count)
3. Fully distribute its excess voters:
   - Get precincts sorted by voter count (largest first)
   - For each precinct, move it to next closest VSPC (further from nearest) that can accept more voters
   - Continue until this VSPC is balanced OR no more moves possible
4. **Recalculate** - find the NEW largest VSPC (after distribution)
5. Repeat until all VSPCs are balanced (within ±25% of target)

**Key Difference from v8:**
- v8 focused on precinct count (≤20 precincts per VSPC)
- v10 focuses on voter volume (target: ~13,105 voters per VSPC based on current registration)
- v10 processes largest-first and fully distributes each before moving to next
- v10 recalculates "next largest" after each distribution (not from initial state)
- v10 uses master files as immutable source of truth (version-agnostic)
- v10 uses current voter registration as primary voter count source

**Results:**
- **Trails Recreation Center: 91,711 → 19,124 voters** (79% reduction, 52% over target)
- **34.4% of VSPCs within ±25% of target** voter volume
- **12 VSPCs still overloaded** (45-54% over target) - ripple constraint limits further moves
- **9 VSPCs underloaded** (mostly rural/small VSPCs)
- **Standard deviation: 6,742 voters**
- **Much better voter distribution than v8** (which had 2.87x ratio in 20-precinct VSPCs)

**Philosophy:** Better to inconvenience everyone equally rather than making some people make huge geographic jumps while keeping others close. Voter volume is more important than precinct count.

**Files Generated:**
- `v10/VSPC - Precinct Distribution.csv` - One row per precinct (403 rows)
- `v10/VSPC Summary.csv` - One row per VSPC (32 rows)
- `v11/VSPC - Precinct Distribution.csv` - One row per precinct (403 rows)
- `v11/VSPC Locations.csv` - One row per VSPC (32 rows)
- `v11/Summary Statistics.csv` - Summary statistics (total VSPCs, total precincts, total reassigned)

## Current Output Files

### V14 Spreadsheet Files (in `v14/` directory) - **CURRENT DEVELOPMENT**

Same structure as v11 (see below). Currently being modified to improve geographic proximity.

### V13 Spreadsheet Files (in `v13/` directory) - **STABLE**

Same structure as v11 (see below). This is the current stable version.

### V11 Spreadsheet Files (in `v11/` directory)
1. **VSPC - Precinct Distribution.csv** (403 rows) - One row per precinct with:
   - Precinct number and voter count
   - Nearest VSPC (geographic baseline) and distance to nearest
   - Assigned VSPC (rebalanced assignment) and distance to assigned
   - Distance difference (assigned - nearest)
   - Reassigned flag (True/False)
   - Voters Assigned, Precincts Assigned (aggregated totals)
   - Address, City, State, Zip
   - Precinct Map URL
   - All distances formatted to 2 decimal places
2. **VSPC Locations.csv** (32 rows) - One row per VSPC with:
   - Assigned VSPC name
   - Voters Assigned, Precincts Assigned
   - Address, City, State, Zip

3. **Summary Statistics.csv** (3 rows) - Summary statistics with:
   - Total Number of VSPCs
   - Total Number of Precincts
   - Total Number of Precincts Reassigned

### V10 Spreadsheet Files (in `v10/` directory)
Same structure as V11 (see above)

### V8 Spreadsheet Files (in `v8/` directory)
Same structure as V10/V11 (see above)

### V6 Spreadsheet Files (in `v6/` directory)
1. VSPC_v6 - Column_Legend.csv
2. VSPC_v6 - Data_Dictionary.csv
3. VSPC_v6 - Full_Assignments_Geo.csv
4. VSPC_v6 - Full_Assignments_Rebalanced.csv
5. VSPC_v6 - Rulebook.csv
6. VSPC_v6 - VSPC_Precinct_Map_Geo.csv
7. VSPC_v6 - VSPC_Precinct_Map_Rebalanced.csv
8. VSPC_v6 - VSPC_Summary.csv
9. VSPC_v6 - Sanity_Check.csv (for manual review)

