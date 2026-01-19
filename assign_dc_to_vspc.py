#!/usr/bin/env python3
"""
Assign District Captains (DC) to VSPCs based on precinct distribution.

Each DC is assigned to the VSPC that has the greatest number of their precincts.
"""

import pandas as pd
from pathlib import Path
from collections import defaultdict

# File paths
WORKSPACE_ROOT = Path(__file__).parent
DC_GROUPING_FILE = WORKSPACE_ROOT / "DC-PL-grouping.csv"
PRECINCT_DISTRIBUTION_FILE = WORKSPACE_ROOT / "output" / "VSPC - Precinct Distribution.csv"
VSPC_LOCATIONS_FILE = WORKSPACE_ROOT / "output" / "VSPC Locations.csv"

def main():
    print("="*60)
    print("ASSIGNING DISTRICT CAPTAINS TO VSPCs")
    print("="*60)
    
    # Step 1: Load DC-PL-grouping.csv to get precinct-to-DC mapping
    print("\n1. Loading DC-PL-grouping.csv...")
    dc_grouping = pd.read_csv(DC_GROUPING_FILE)
    
    # Create mapping: precinct (New Pct#) -> DC
    # New Pct# is column index 5 (0-indexed), DC is column index 6
    precinct_to_dc = {}
    for _, row in dc_grouping.iterrows():
        precinct = str(row['New Pct#']).strip()
        dc = row['DC']
        if pd.notna(dc) and pd.notna(precinct) and precinct != '':
            # Store as string for consistency, but keep DC as number
            precinct_to_dc[precinct] = int(dc) if pd.notna(dc) else None
    
    print(f"   Found {len(precinct_to_dc)} precinct-to-DC mappings")
    print(f"   DCs found: {sorted(set(precinct_to_dc.values()))}")
    
    # Step 2: Load VSPC - Precinct Distribution.csv to get precinct-to-VSPC mapping
    print("\n2. Loading VSPC - Precinct Distribution.csv...")
    precinct_dist = pd.read_csv(PRECINCT_DISTRIBUTION_FILE)
    
    # Create mapping: precinct -> VSPC name
    # Precinct is column 0, Assigned VSPC is column 4
    precinct_to_vspc = {}
    for _, row in precinct_dist.iterrows():
        precinct = str(row['Precinct']).strip()
        vspc = str(row['Assigned VSPC']).strip()
        if pd.notna(precinct) and pd.notna(vspc) and precinct != '' and vspc != '':
            precinct_to_vspc[precinct] = vspc
    
    print(f"   Found {len(precinct_to_vspc)} precinct-to-VSPC mappings")
    
    # Step 3: For each DC, count how many precincts are in each VSPC
    print("\n3. Counting precincts per DC per VSPC...")
    # Structure: dc -> {vspc -> count}
    dc_vspc_counts = defaultdict(lambda: defaultdict(int))
    
    # Debug: Check a few sample precincts
    sample_precincts = list(precinct_to_dc.keys())[:5]
    print(f"   Sample precincts from DC file: {sample_precincts}")
    sample_vspc_precincts = list(precinct_to_vspc.keys())[:5]
    print(f"   Sample precincts from VSPC file: {sample_vspc_precincts}")
    
    matched_count = 0
    unmatched_count = 0
    
    for precinct, dc in precinct_to_dc.items():
        if dc is not None:
            # Normalize precinct number - remove any leading zeros, convert to int then back to str
            precinct_normalized = str(int(precinct)) if precinct.isdigit() else precinct.strip()
            if precinct_normalized in precinct_to_vspc:
                vspc = precinct_to_vspc[precinct_normalized]
                dc_vspc_counts[dc][vspc] += 1
                matched_count += 1
            else:
                unmatched_count += 1
                if unmatched_count <= 5:  # Show first 5 unmatched
                    print(f"   ⚠️  Precinct {precinct} (DC {dc}) not found in VSPC distribution")
    
    print(f"   Matched: {matched_count}, Unmatched: {unmatched_count}")
    
    # Step 4: For each DC, find the VSPC with the most precincts
    print("\n4. Determining DC assignments...")
    dc_to_vspc = {}
    for dc in sorted(dc_vspc_counts.keys()):
        vspc_counts = dc_vspc_counts[dc]
        if vspc_counts:
            # Find VSPC with maximum count
            best_vspc = max(vspc_counts.items(), key=lambda x: x[1])
            dc_to_vspc[dc] = best_vspc[0]
            print(f"   DC {dc} -> {best_vspc[0]} ({best_vspc[1]} precincts)")
        else:
            print(f"   DC {dc} -> No precincts found")
    
    # Step 5: Load VSPC Locations.csv and update Primary Captain District column
    print("\n5. Updating VSPC Locations.csv...")
    vspc_locations = pd.read_csv(VSPC_LOCATIONS_FILE)
    
    # Create reverse mapping: VSPC name -> DC
    vspc_to_dc = {vspc: dc for dc, vspc in dc_to_vspc.items()}
    
    # Update Primary Captain District column
    vspc_locations['Primary Captain District'] = vspc_locations['VSPC'].map(vspc_to_dc)
    
    # Count assignments
    assigned_count = vspc_locations['Primary Captain District'].notna().sum()
    print(f"   Assigned {assigned_count} out of {len(vspc_locations)} VSPCs")
    
    # Show unassigned VSPCs
    unassigned = vspc_locations[vspc_locations['Primary Captain District'].isna()]
    if len(unassigned) > 0:
        print(f"\n   Unassigned VSPCs ({len(unassigned)}):")
        for _, row in unassigned.iterrows():
            print(f"     - {row['VSPC']}")
    
    # Step 6: Save updated file
    print("\n6. Saving updated VSPC Locations.csv...")
    vspc_locations.to_csv(VSPC_LOCATIONS_FILE, index=False)
    print(f"   ✓ Saved to {VSPC_LOCATIONS_FILE}")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total VSPCs: {len(vspc_locations)}")
    print(f"VSPCs with DC assigned: {assigned_count}")
    print(f"VSPCs without DC assigned: {len(unassigned)}")
    print(f"Total DCs: {len(dc_to_vspc)}")
    print("\nDC Assignments:")
    for dc in sorted(dc_to_vspc.keys()):
        vspc = dc_to_vspc[dc]
        count = dc_vspc_counts[dc][vspc]
        print(f"  DC {dc}: {vspc} ({count} precincts)")

if __name__ == "__main__":
    main()
