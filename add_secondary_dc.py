#!/usr/bin/env python3
"""
Add Secondary Captain District column to VSPC Locations.csv

Assigns unassigned DCs to VSPCs with highest percentage of their precincts.
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
    print("ADDING SECONDARY CAPTAIN DISTRICT COLUMN")
    print("="*60)
    
    # Unassigned DCs
    unassigned_dcs = [2, 3, 6, 7, 9, 12, 22, 26, 28, 30]
    print(f"\nUnassigned DCs to assign: {unassigned_dcs}")
    
    # Step 1: Load DC-PL-grouping.csv to get total precinct count per DC
    print("\n1. Loading DC-PL-grouping.csv to get DC precinct counts...")
    dc_grouping = pd.read_csv(DC_GROUPING_FILE)
    
    # Get unique precincts per DC
    dc_total_precincts = {}
    for _, row in dc_grouping.iterrows():
        dc = row['DC']
        precinct = row['New Pct#']
        if pd.notna(dc) and pd.notna(precinct):
            dc = int(dc)
            if dc not in dc_total_precincts:
                dc_total_precincts[dc] = set()
            dc_total_precincts[dc].add(int(precinct))
    
    # Convert to counts
    dc_total_counts = {dc: len(precincts) for dc, precincts in dc_total_precincts.items()}
    
    # Step 2: Load VSPC - Precinct Distribution.csv
    print("\n2. Loading VSPC - Precinct Distribution.csv...")
    precinct_dist = pd.read_csv(PRECINCT_DISTRIBUTION_FILE)
    precinct_dist_with_dc = precinct_dist[precinct_dist['Primary Captain District'].notna()]
    
    # Step 3: Calculate percentage of precincts per DC per VSPC (only for unassigned DCs)
    print("\n3. Calculating percentage of precincts for unassigned DCs...")
    dc_vspc_data = defaultdict(lambda: defaultdict(lambda: {'count': 0, 'percentage': 0.0}))
    
    for _, row in precinct_dist_with_dc.iterrows():
        dc = int(row['Primary Captain District'])
        vspc = str(row['Assigned VSPC']).strip()
        if pd.notna(vspc) and vspc != '' and dc in unassigned_dcs and dc in dc_total_counts:
            dc_vspc_data[dc][vspc]['count'] += 1
            total = dc_total_counts[dc]
            dc_vspc_data[dc][vspc]['percentage'] = (dc_vspc_data[dc][vspc]['count'] / total) * 100
    
    # Step 4: Assign each unassigned DC to VSPC with highest percentage
    # Handle conflicts by assigning VSPC to DC with highest percentage, then assign others to next best
    print("\n4. Assigning unassigned DCs to VSPCs with highest percentage...")
    
    # First, find each DC's preferred VSPC (highest percentage)
    dc_preferred_vspc = {}
    for dc in sorted(unassigned_dcs):
        if dc in dc_vspc_data and len(dc_vspc_data[dc]) > 0:
            best_vspc = max(dc_vspc_data[dc].items(), key=lambda x: (x[1]['percentage'], x[1]['count']))
            dc_preferred_vspc[dc] = best_vspc[0]
    
    # Group DCs by their preferred VSPC
    vspc_dc_candidates = defaultdict(list)
    for dc, vspc in dc_preferred_vspc.items():
        vspc_dc_candidates[vspc].append(dc)
    
    # Resolve conflicts: assign VSPC to DC with highest percentage
    vspc_to_dc = {}
    assigned_dcs = set()
    
    for vspc in sorted(vspc_dc_candidates.keys()):
        candidates = vspc_dc_candidates[vspc]
        # Pick the DC with the highest percentage at this VSPC
        best_dc = max(candidates, key=lambda dc: (dc_vspc_data[dc][vspc]['percentage'],
                                                  dc_vspc_data[dc][vspc]['count']))
        vspc_to_dc[vspc] = best_dc
        assigned_dcs.add(best_dc)
        pct_data = dc_vspc_data[best_dc][vspc]
        if len(candidates) > 1:
            print(f"   {vspc}: Multiple DCs want this ({candidates}), assigned to DC {best_dc} ({pct_data['percentage']:.1f}%, {pct_data['count']} precincts)")
        else:
            print(f"   DC {best_dc} -> {vspc} ({pct_data['percentage']:.1f}%, {pct_data['count']} precincts)")
    
    # Assign remaining DCs to their next best VSPC
    unassigned_dcs_remaining = set(unassigned_dcs) - assigned_dcs
    if unassigned_dcs_remaining:
        print(f"\n   Assigning remaining {len(unassigned_dcs_remaining)} DCs to next best VSPCs...")
        
        for dc in sorted(unassigned_dcs_remaining):
            if dc in dc_vspc_data and len(dc_vspc_data[dc]) > 0:
                # Get all VSPCs sorted by percentage (descending), excluding already assigned VSPCs
                vspc_options = sorted(dc_vspc_data[dc].items(), 
                                    key=lambda x: (x[1]['percentage'], x[1]['count']), 
                                    reverse=True)
                
                # Find first VSPC not already assigned to another secondary DC
                assigned = False
                for vspc, data in vspc_options:
                    if vspc not in vspc_to_dc:
                        vspc_to_dc[vspc] = dc
                        assigned_dcs.add(dc)
                        print(f"   DC {dc} -> {vspc} ({data['percentage']:.1f}%, {data['count']} precincts) [next best]")
                        assigned = True
                        break
                
                if not assigned:
                    print(f"   DC {dc} -> No available VSPC found")
    
    # Step 5: Load VSPC Locations.csv and add/update Secondary Captain District column
    print("\n5. Adding/updating Secondary Captain District column to VSPC Locations.csv...")
    vspc_locations = pd.read_csv(VSPC_LOCATIONS_FILE)
    
    # Find the index of Primary Captain District column
    primary_col_idx = vspc_locations.columns.get_loc('Primary Captain District')
    
    # Check if Secondary Captain District column already exists
    if 'Secondary Captain District' in vspc_locations.columns:
        # Update existing column
        vspc_locations['Secondary Captain District'] = vspc_locations['VSPC'].map(vspc_to_dc).astype('Int64')
        # Reorder to put it right after Primary Captain District
        cols = list(vspc_locations.columns)
        cols.remove('Secondary Captain District')
        cols.insert(primary_col_idx + 1, 'Secondary Captain District')
        vspc_locations = vspc_locations[cols]
    else:
        # Insert new column right after Primary Captain District
        secondary_dcs = vspc_locations['VSPC'].map(vspc_to_dc).astype('Int64')
        vspc_locations.insert(primary_col_idx + 1, 'Secondary Captain District', secondary_dcs)
    
    # Count assignments
    assigned_count = vspc_locations['Secondary Captain District'].notna().sum()
    print(f"   Assigned {len(vspc_to_dc)} Secondary DCs to {assigned_count} VSPCs")
    
    # Show assignments
    print("\n   Secondary DC Assignments:")
    for vspc in sorted(vspc_to_dc.keys()):
        dc = vspc_to_dc[vspc]
        if dc in dc_vspc_data and vspc in dc_vspc_data[dc]:
            pct_data = dc_vspc_data[dc][vspc]
            print(f"     {vspc} -> DC {dc} ({pct_data['percentage']:.1f}%, {pct_data['count']} precincts)")
    
    # Step 6: Save updated file
    print("\n6. Saving updated VSPC Locations.csv...")
    vspc_locations.to_csv(VSPC_LOCATIONS_FILE, index=False)
    print(f"   ✓ Saved to {VSPC_LOCATIONS_FILE}")
    
    print("\n" + "="*60)
    print("COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()
