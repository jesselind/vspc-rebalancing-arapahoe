#!/usr/bin/env python3
"""
Assign Primary Captain District to each VSPC location.

Primary: Assign DC to VSPC with highest percentage of their precincts
Secondary: If primary unavailable, use geographic proximity
"""

import pandas as pd
from pathlib import Path
from collections import defaultdict
from math import radians, cos, sin, asin, sqrt

# File paths
WORKSPACE_ROOT = Path(__file__).parent
DC_GROUPING_FILE = WORKSPACE_ROOT / "DC-PL-grouping.csv"
PRECINCT_DISTRIBUTION_FILE = WORKSPACE_ROOT / "output" / "VSPC - Precinct Distribution.csv"
VSPC_LOCATIONS_FILE = WORKSPACE_ROOT / "output" / "VSPC Locations.csv"
MASTER_PRECINCTS_FILE = WORKSPACE_ROOT / "master_precincts.csv"
MASTER_VSPCS_FILE = WORKSPACE_ROOT / "master_vspcs.csv"

def haversine(lon1, lat1, lon2, lat2):
    """Calculate distance between two lat/lon points in kilometers."""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return 6371 * c  # Earth radius in km

def main():
    print("="*60)
    print("ASSIGNING PRIMARY CAPTAIN DISTRICT TO VSPC LOCATIONS")
    print("="*60)
    
    # Step 1: Load DC-PL-grouping.csv to get total precinct count per DC
    print("\n1. Loading DC-PL-grouping.csv to get DC precinct counts...")
    dc_grouping = pd.read_csv(DC_GROUPING_FILE)
    
    # Get unique precincts per DC (where Role='DC' indicates the DC's precincts)
    # Actually, all rows with a DC value represent that DC's precincts
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
    print(f"   Found {len(dc_total_counts)} DCs with total precinct counts")
    for dc in sorted(dc_total_counts.keys()):
        print(f"   DC {dc}: {dc_total_counts[dc]} total precincts")
    
    # Step 2: Load VSPC - Precinct Distribution.csv
    print("\n2. Loading VSPC - Precinct Distribution.csv...")
    precinct_dist = pd.read_csv(PRECINCT_DISTRIBUTION_FILE)
    print(f"   Loaded {len(precinct_dist)} precinct rows")
    
    # Filter out rows without DC assignment
    precinct_dist_with_dc = precinct_dist[precinct_dist['Primary Captain District'].notna()]
    print(f"   Rows with DC assignment: {len(precinct_dist_with_dc)}")
    
    # Step 3: Calculate percentage of precincts per DC per VSPC
    print("\n3. Calculating percentage of precincts per DC per VSPC...")
    # Structure: dc -> {vspc -> (count, percentage)}
    dc_vspc_data = defaultdict(lambda: defaultdict(lambda: {'count': 0, 'percentage': 0.0}))
    
    for _, row in precinct_dist_with_dc.iterrows():
        dc = int(row['Primary Captain District'])
        vspc = str(row['Assigned VSPC']).strip()
        if pd.notna(vspc) and vspc != '' and dc in dc_total_counts:
            dc_vspc_data[dc][vspc]['count'] += 1
            # Calculate percentage
            total = dc_total_counts[dc]
            dc_vspc_data[dc][vspc]['percentage'] = (dc_vspc_data[dc][vspc]['count'] / total) * 100
    
    print(f"   Found {len(dc_vspc_data)} DCs with precinct assignments")
    
    # Step 4: Load geographic data for proximity calculations
    print("\n4. Loading geographic data...")
    master_precincts = pd.read_csv(MASTER_PRECINCTS_FILE)
    master_vspcs = pd.read_csv(MASTER_VSPCS_FILE)
    
    # Create precinct coordinate mapping
    precinct_coords = {}
    for _, row in master_precincts.iterrows():
        pct = int(row['PRECINCT'])
        precinct_coords[pct] = (row['Precinct_Latitude'], row['Precinct_Longitude'])
    
    # Create VSPC coordinate mapping
    vspc_coords = {}
    for _, row in master_vspcs.iterrows():
        vspc = row['VSPC_Name']
        vspc_coords[vspc] = (row['VSPC_Latitude'], row['VSPC_Longitude'])
    
    print(f"   Loaded coordinates for {len(precinct_coords)} precincts and {len(vspc_coords)} VSPCs")
    
    # Step 5: For each DC, calculate average distance to each VSPC
    print("\n5. Calculating average distances from DC precincts to VSPCs...")
    dc_vspc_distances = defaultdict(lambda: defaultdict(float))
    
    for dc, precincts in dc_total_precincts.items():
        for vspc, (vspc_lat, vspc_lon) in vspc_coords.items():
            distances = []
            for pct in precincts:
                if pct in precinct_coords:
                    pct_lat, pct_lon = precinct_coords[pct]
                    dist = haversine(pct_lon, pct_lat, vspc_lon, vspc_lat)
                    distances.append(dist)
            if distances:
                dc_vspc_distances[dc][vspc] = sum(distances) / len(distances)
    
    # Step 6: Primary assignment - assign each DC to VSPC with highest percentage
    print("\n6. Primary assignment: Assigning each DC to VSPC with highest percentage...")
    dc_to_best_vspc = {}
    
    for dc in sorted(dc_vspc_data.keys()):
        vspc_data = dc_vspc_data[dc]
        if vspc_data:
            # Find VSPC with maximum percentage (tiebreaker: most precincts, then closest)
            best_vspc = max(vspc_data.items(), 
                          key=lambda x: (x[1]['percentage'], 
                                       x[1]['count'],
                                       -dc_vspc_distances[dc].get(x[0], float('inf'))))
            dc_to_best_vspc[dc] = best_vspc[0]
            print(f"   DC {dc} -> {best_vspc[0]} ({best_vspc[1]['percentage']:.1f}%, {best_vspc[1]['count']} precincts)")
    
    # Step 7: Resolve conflicts - assign VSPC to DC with highest percentage
    print("\n7. Resolving conflicts (ensuring each VSPC gets exactly one DC)...")
    vspc_to_dc = {}
    assigned_dcs = set()
    
    # Group DCs by their preferred VSPC
    vspc_dc_candidates = defaultdict(list)
    for dc, vspc in dc_to_best_vspc.items():
        vspc_dc_candidates[vspc].append(dc)
    
    # For each VSPC, assign it to the DC with the highest percentage
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
            print(f"   {vspc} -> DC {best_dc} ({pct_data['percentage']:.1f}%, {pct_data['count']} precincts)")
    
    # Show unassigned DCs
    unassigned_dcs = set(dc_to_best_vspc.keys()) - assigned_dcs
    if unassigned_dcs:
        print(f"\n   Unassigned DCs ({len(unassigned_dcs)}): {sorted(unassigned_dcs)}")
    
    # Step 8: Assign remaining unassigned VSPCs
    all_vspcs = set(precinct_dist_with_dc['Assigned VSPC'].unique())
    unassigned_vspcs = all_vspcs - set(vspc_to_dc.keys())
    
    if unassigned_vspcs:
        print(f"\n8. Assigning remaining {len(unassigned_vspcs)} VSPCs...")
        
        for vspc in sorted(unassigned_vspcs):
            vspc_precincts = precinct_dist_with_dc[precinct_dist_with_dc['Assigned VSPC'] == vspc]
            if len(vspc_precincts) > 0:
                # Count precincts per DC and calculate percentages
                dc_scores = {}
                for _, row in vspc_precincts.iterrows():
                    dc = int(row['Primary Captain District'])
                    if dc in dc_total_counts:
                        if dc not in dc_scores:
                            dc_scores[dc] = 0
                        dc_scores[dc] += 1
                
                if dc_scores:
                    # Calculate percentages and find best DC
                    for dc in dc_scores.keys():
                        dc_scores[dc] = (dc_scores[dc] / dc_total_counts[dc]) * 100
                    
                    # Primary: highest percentage, Secondary: closest distance
                    best_dc = max(dc_scores.items(), 
                                 key=lambda x: (x[1], 
                                              -dc_vspc_distances[x[0]].get(vspc, float('inf'))))
                    vspc_to_dc[vspc] = best_dc[0]
                    if best_dc[0] not in assigned_dcs:
                        assigned_dcs.add(best_dc[0])
                        if best_dc[0] in unassigned_dcs:
                            unassigned_dcs.remove(best_dc[0])
                    dist = dc_vspc_distances[best_dc[0]].get(vspc, 0)
                    print(f"   {vspc} -> DC {best_dc[0]} ({best_dc[1]:.1f}%, {dist:.2f} km avg distance)")
                else:
                    print(f"   {vspc} -> No DC assignments found for precincts at this VSPC")
            else:
                # No precincts with DC assignments - use geographic proximity
                if unassigned_dcs:
                    # Find closest unassigned DC
                    best_dc = min(unassigned_dcs, 
                                 key=lambda dc: dc_vspc_distances[dc].get(vspc, float('inf')))
                    vspc_to_dc[vspc] = best_dc
                    assigned_dcs.add(best_dc)
                    unassigned_dcs.remove(best_dc)
                    dist = dc_vspc_distances[best_dc].get(vspc, 0)
                    print(f"   {vspc} -> DC {best_dc} (geographic proximity, {dist:.2f} km avg distance)")
    
    # Step 9: Load VSPC Locations.csv and update Primary Captain District column
    print("\n9. Updating VSPC Locations.csv...")
    vspc_locations = pd.read_csv(VSPC_LOCATIONS_FILE)
    
    # Update Primary Captain District column
    vspc_locations['Primary Captain District'] = vspc_locations['VSPC'].map(vspc_to_dc).astype('Int64')
    
    # Count assignments
    assigned_count = vspc_locations['Primary Captain District'].notna().sum()
    print(f"   Assigned {assigned_count} out of {len(vspc_locations)} VSPCs")
    
    # Show unassigned VSPCs
    unassigned = vspc_locations[vspc_locations['Primary Captain District'].isna()]
    if len(unassigned) > 0:
        print(f"\n   Unassigned VSPCs ({len(unassigned)}):")
        for _, row in unassigned.iterrows():
            print(f"     - {row['VSPC']}")
    
    # Step 10: Save updated file
    print("\n10. Saving updated VSPC Locations.csv...")
    vspc_locations.to_csv(VSPC_LOCATIONS_FILE, index=False)
    print(f"   ✓ Saved to {VSPC_LOCATIONS_FILE}")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total VSPCs: {len(vspc_locations)}")
    print(f"VSPCs with DC assigned: {assigned_count}")
    print(f"VSPCs without DC assigned: {len(unassigned)}")
    print(f"Total DCs assigned to VSPCs: {len(assigned_dcs)}")
    print(f"Total DCs unassigned: {len(unassigned_dcs)}")
    print("\nVSPC Assignments:")
    for vspc in sorted(vspc_to_dc.keys()):
        dc = vspc_to_dc[vspc]
        if dc in dc_vspc_data and vspc in dc_vspc_data[dc]:
            pct_data = dc_vspc_data[dc][vspc]
            dist = dc_vspc_distances[dc].get(vspc, 0)
            print(f"  {vspc} -> DC {dc} ({pct_data['percentage']:.1f}%, {pct_data['count']} precincts, {dist:.2f} km avg)")

if __name__ == "__main__":
    main()
