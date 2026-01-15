# V6 Spreadsheet Generation

## Overview

This script generates a complete V6 spreadsheet with voter-volume-based rebalancing. The output consists of 8 CSV files, each representing a tab in the spreadsheet.

## Usage

```bash
python generate_v6_spreadsheet.py
```

This will:
1. Load voter data and geographic assignments
2. Perform aggressive voter-volume-based rebalancing
3. Generate all 8 CSV files in the `v6/` directory

**Note:** Script has already been run successfully. Files are in `v6/` directory.

## Sanity Check File

A separate sanity check file is available for manual review:

```bash
python fix_sanity_check.py
```

This creates `v6/VSPC_v6 - Sanity_Check.csv` with:
- Precinct number, precinct voters, VSPC total voters
- VSPC name, address, city, state, ZIP (all verified against official source)
- Distance in miles from precinct to VSPC

**Note:** This file has already been created and verified.

## Output Files

All files are saved to the `v6/` directory with the naming pattern `VSPC_v6 - [TabName].csv`:

### 1. Column_Legend.csv
- Column definitions and descriptions
- From v3 format (more detailed)

### 2. Data_Dictionary.csv
- Column definitions and descriptions
- From v5 format

### 3. Full_Assignments_Geo.csv
- Complete geographic assignments
- All columns from the original data
- Each precinct assigned to its closest VSPC
- Includes voter counts
- **Secondary column**: Second-closest VSPC name (from v3)

### 4. Full_Assignments_Rebalanced.csv
- Complete rebalanced assignments
- All columns from the original data
- Includes `VSPC_Rebalanced` column with new assignments
- Balanced by voter volume (not just precinct count)
- **Secondary column**: Second-closest VSPC name (from v3)

### 5. Rulebook.csv
- Updated documentation
- Explains voter-volume-based rebalancing approach
- Usage instructions for GEO vs REBALANCED sheets

### 6. VSPC_Precinct_Map_Geo.csv
- Simplified view of geographic assignments
- **IMPORTANT**: Includes PRECINCT column (v5 was missing this!)
- Columns: VSPC_Name, Address, City, State, ZIP, PRECINCT
- One row per precinct assignment
- Shows which precincts belong to each VSPC (unlike v5)

### 7. VSPC_Precinct_Map_Rebalanced.csv
- Simplified view of rebalanced assignments
- **IMPORTANT**: Includes PRECINCT column (v5 was missing this!)
- Columns: VSPC_Name, Address, City, State, ZIP, PRECINCT
- One row per precinct assignment
- Shows which precincts belong to each VSPC (unlike v5)

### 8. VSPC_Summary.csv
- Summary statistics for each VSPC
- Columns:
  - VSPC_Name
  - Geo_Count (precinct count in geographic assignment)
  - Geo_Voters (total voters in geographic assignment)
  - Rebalanced_Count (precinct count in rebalanced assignment)
  - Rebalanced_Voters (total voters in rebalanced assignment)
- Sorted by Rebalanced_Voters (descending)

## Importing into Google Sheets

1. Open Google Sheets
2. Create a new spreadsheet
3. For each CSV file:
   - File → Import
   - Upload the CSV file
   - Choose "Insert new sheet(s)"
   - The sheet name will be the filename (you can rename it)

Alternatively, you can:
1. Create a new Google Sheet
2. Import all CSV files as separate tabs
3. Rename tabs to match the file names (without the .csv extension)

## Key Improvements: Best of v3 + v5

### From v3 (what v5 was missing):
- **PRECINCT in VSPC_Precinct_Map files**: Now you can see which precincts are assigned to each VSPC (v5 was missing this!)
- **Secondary column**: Shows the second-closest VSPC for each precinct (useful for rebalancing reference)

### From v5:
- **Voter counts**: Included in all assignment files
- **Complete data structure**: All columns preserved

### New in v6:
- **Voter-volume-based rebalancing**: Balances by voter count, not just precinct count
- **Voter counts in Summary**: Summary file includes both precinct counts AND voter counts
- **Better balance**: More even distribution of voter workload across VSPCs
- **Results**: 64% standard deviation improvement, The Avenue Church reduced from 70 to 31 precincts

## Rebalancing Results

- **The Avenue Church**: 70 → 31 precincts (still highest but manageable)
- **Max voters**: 79,056 → 28,927
- **Standard deviation**: 64% improvement
- **Average distance increase**: 0.60 miles
- **Max distance**: 16.27 miles (no assignments >20 miles)
- **Geographic validation**: ✅ No east/west cross-assignments found
- **Precincts moved**: 70 out of 403 (17.4%)

## Sanity Check File

A separate sanity check file is available for manual review:

```bash
python fix_sanity_check.py
```

This creates `v6/VSPC_v6 - Sanity_Check.csv` with:
- Precinct number, precinct voters, VSPC total voters
- VSPC name, address, city, state, ZIP (all verified against official source)
- Distance in miles from precinct to VSPC (calculated using geocoded VSPC coordinates)

**Note:** This file has already been created and verified. All addresses are correct and all VSPC coordinates have been geocoded for accurate distance calculations.

**Column Headers:** Optimized for Google Sheets with user-friendly names (spaces allowed):
- `Precinct`, `Voters`, `Voter Service Polling Center (VSPC)`, `VSPC Total Voters`, `Address`, `City`, `State`, `Zip`, `Distance From Precinct (mi.)`

## Future Planning: Area Organization

### Area-Based Polling Station Management

**Concept:** Organize precincts into Areas based on VSPCs for polling station staffing and management.

**Requirements:**
1. **Areas** defined by ~32 VSPCs from 2026 election (see: https://www.arapahoeco.gov/your_county/arapahoevotes/voting_locations/voter_service_polling_centers.php)
2. **Precinct assignment** to areas as evenly as possible, potentially aligning with GOP District Captain assignments
3. **Spreadsheet** with: Area, Precincts, Area Lead, Precinct Lead, 10+ hand counter positions
4. **Status:** Pending - Area organization spreadsheet to be created

## Validation

✅ **Already Completed:**
1. ✅ All 403 precincts are assigned
2. ✅ No precincts are assigned to invalid VSPCs
3. ✅ Geographic constraints validated (no east/west cross-assignments)
4. ✅ Rural VSPCs are protected appropriately
5. ✅ Voter distribution is 64% more balanced than geographic assignment
6. ✅ All VSPC addresses verified against official Arapahoe County website
7. ✅ Sanity check CSV created with correct addresses, city, state, ZIP
8. ✅ All 26 VSPC coordinates geocoded using OpenStreetMap/Nominatim for accurate distances
9. ✅ Sanity check column headers optimized for Google Sheets (user-friendly names)
10. ✅ All distances recalculated using corrected VSPC coordinates


