#!/usr/bin/env python3
"""
Create verification CSV showing DC assignments and percentage of precincts at each VSPC.
"""

import pandas as pd
from pathlib import Path
from collections import defaultdict

# File paths
WORKSPACE_ROOT = Path(__file__).parent
DC_GROUPING_FILE = WORKSPACE_ROOT / "DC-PL-grouping.csv"
PRECINCT_DISTRIBUTION_FILE = WORKSPACE_ROOT / "output" / "VSPC - Precinct Distribution.csv"
VSPC_LOCATIONS_FILE = WORKSPACE_ROOT / "output" / "VSPC Locations.csv"
OUTPUT_FILE = WORKSPACE_ROOT / "output" / "DC Assignment Verification.csv"

def main():
    print("="*60)
    print("CREATING DC ASSIGNMENT VERIFICATION CSV")
    print("="*60)
    
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
    
    # Step 3: Calculate percentage of precincts per DC per VSPC
    print("\n3. Calculating percentage of precincts per DC per VSPC...")
    dc_vspc_percentages = defaultdict(lambda: defaultdict(float))
    dc_vspc_counts = defaultdict(lambda: defaultdict(int))
    
    for _, row in precinct_dist_with_dc.iterrows():
        dc = int(row['Primary Captain District'])
        vspc = str(row['Assigned VSPC']).strip()
        if pd.notna(vspc) and vspc != '' and dc in dc_total_counts:
            dc_vspc_counts[dc][vspc] += 1
            total = dc_total_counts[dc]
            dc_vspc_percentages[dc][vspc] = (dc_vspc_counts[dc][vspc] / total) * 100
    
    # Step 4: Load VSPC Locations.csv
    print("\n4. Loading VSPC Locations.csv...")
    vspc_locations = pd.read_csv(VSPC_LOCATIONS_FILE)
    
    # Step 5: Create verification data
    print("\n5. Creating verification data...")
    verification_data = []
    
    for _, row in vspc_locations.iterrows():
        vspc = row['VSPC']
        primary_dc = row['Primary Captain District']
        secondary_dc = row['Secondary Captain District'] if 'Secondary Captain District' in row else None
        
        # Get percentages
        primary_pct = None
        if pd.notna(primary_dc):
            primary_dc = int(primary_dc)
            if primary_dc in dc_vspc_percentages and vspc in dc_vspc_percentages[primary_dc]:
                primary_pct = dc_vspc_percentages[primary_dc][vspc]
        
        secondary_pct = None
        if pd.notna(secondary_dc):
            secondary_dc = int(secondary_dc)
            if secondary_dc in dc_vspc_percentages and vspc in dc_vspc_percentages[secondary_dc]:
                secondary_pct = dc_vspc_percentages[secondary_dc][vspc]
        
        verification_data.append({
            'VSPC': vspc,
            'Primary Captain District': int(primary_dc) if pd.notna(primary_dc) else None,
            'Primary DC % of Precincts': round(primary_pct / 100, 4) if primary_pct is not None else None,  # Convert to decimal (0.80 for 80%)
            'Secondary Captain District': int(secondary_dc) if pd.notna(secondary_dc) else None,
            'Secondary DC % of Precincts': round(secondary_pct / 100, 4) if secondary_pct is not None else None  # Convert to decimal
        })
    
    # Step 6: Create DataFrame and save
    print("\n6. Saving verification CSV...")
    verification_df = pd.DataFrame(verification_data)
    
    # Ensure DC columns are integers (not floats)
    verification_df['Primary Captain District'] = verification_df['Primary Captain District'].astype('Int64')
    verification_df['Secondary Captain District'] = verification_df['Secondary Captain District'].astype('Int64')
    
    verification_df.to_csv(OUTPUT_FILE, index=False)
    print(f"   ✓ Saved to {OUTPUT_FILE}")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total VSPCs: {len(verification_df)}")
    print(f"VSPCs with Primary DC: {verification_df['Primary Captain District'].notna().sum()}")
    print(f"VSPCs with Secondary DC: {verification_df['Secondary Captain District'].notna().sum()}")
    
    # Show any low percentage assignments (potential issues)
    print("\nLow percentage assignments (< 0.20 or 20%):")
    low_primary = verification_df[
        (verification_df['Primary DC % of Precincts'].notna()) & 
        (verification_df['Primary DC % of Precincts'] < 0.20)
    ]
    if len(low_primary) > 0:
        for _, row in low_primary.iterrows():
            pct = row['Primary DC % of Precincts'] * 100
            print(f"  {row['VSPC']}: Primary DC {int(row['Primary Captain District'])} ({pct:.1f}%)")
    
    low_secondary = verification_df[
        (verification_df['Secondary DC % of Precincts'].notna()) & 
        (verification_df['Secondary DC % of Precincts'] < 0.20)
    ]
    if len(low_secondary) > 0:
        for _, row in low_secondary.iterrows():
            pct = row['Secondary DC % of Precincts'] * 100
            print(f"  {row['VSPC']}: Secondary DC {int(row['Secondary Captain District'])} ({pct:.1f}%)")
    
    if len(low_primary) == 0 and len(low_secondary) == 0:
        print("  None - all assignments look good!")

if __name__ == "__main__":
    main()
