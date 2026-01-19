#!/usr/bin/env python3
"""
Add Primary Captain District column to VSPC - Precinct Distribution.csv

Adds the column as the first column and populates it from DC-PL-grouping.csv
by matching precinct numbers.
"""

import pandas as pd
from pathlib import Path

# File paths
WORKSPACE_ROOT = Path(__file__).parent
DC_GROUPING_FILE = WORKSPACE_ROOT / "DC-PL-grouping.csv"
PRECINCT_DISTRIBUTION_FILE = WORKSPACE_ROOT / "output" / "VSPC - Precinct Distribution.csv"

def main():
    print("="*60)
    print("ADDING PRIMARY CAPTAIN DISTRICT TO PRECINCT DISTRIBUTION")
    print("="*60)
    
    # Step 1: Load DC-PL-grouping.csv and create precinct-to-DC mapping
    print("\n1. Loading DC-PL-grouping.csv...")
    dc_grouping = pd.read_csv(DC_GROUPING_FILE)
    
    # Create mapping: precinct (New Pct#) -> DC
    # Use the first occurrence of each precinct (they may appear multiple times)
    # Handle both float and int types for precinct numbers
    precinct_to_dc = {}
    for _, row in dc_grouping.iterrows():
        precinct_val = row['New Pct#']
        dc = row['DC']
        if pd.notna(dc) and pd.notna(precinct_val):
            # Convert to int first (handles float like 102.0 -> 102), then to string
            precinct = str(int(precinct_val))
            if precinct not in precinct_to_dc:
                precinct_to_dc[precinct] = int(dc)
    
    print(f"   Found {len(precinct_to_dc)} unique precinct-to-DC mappings")
    print(f"   DCs found: {sorted(set(precinct_to_dc.values()))}")
    
    # Step 2: Load VSPC - Precinct Distribution.csv
    print("\n2. Loading VSPC - Precinct Distribution.csv...")
    precinct_dist = pd.read_csv(PRECINCT_DISTRIBUTION_FILE)
    print(f"   Loaded {len(precinct_dist)} precinct rows")
    
    # Step 3: Add Primary Captain District column as first column
    print("\n3. Adding Primary Captain District column...")
    
    # Convert Precinct column to string for matching (handle int/float)
    precinct_dist['Precinct_Str'] = precinct_dist['Precinct'].astype(int).astype(str)
    
    # Map DC values (as integers, not floats)
    precinct_dist['Primary Captain District'] = precinct_dist['Precinct_Str'].map(precinct_to_dc).astype('Int64')  # Int64 allows NaN
    
    # Reorder columns to put Primary Captain District first
    cols = ['Primary Captain District'] + [col for col in precinct_dist.columns if col != 'Primary Captain District' and col != 'Precinct_Str']
    precinct_dist = precinct_dist[cols]
    
    # Count how many were matched
    matched_count = precinct_dist['Primary Captain District'].notna().sum()
    unmatched_count = precinct_dist['Primary Captain District'].isna().sum()
    
    print(f"   Matched: {matched_count} precincts")
    print(f"   Unmatched: {unmatched_count} precincts")
    
    if unmatched_count > 0:
        unmatched_precincts = precinct_dist[precinct_dist['Primary Captain District'].isna()]['Precinct'].head(10)
        print(f"\n   Sample unmatched precincts (first 10):")
        for pct in unmatched_precincts:
            print(f"     - {pct}")
    
    # Step 4: Save updated file
    print("\n4. Saving updated file...")
    precinct_dist.to_csv(PRECINCT_DISTRIBUTION_FILE, index=False)
    print(f"   ✓ Saved to {PRECINCT_DISTRIBUTION_FILE}")
    
    print("\n" + "="*60)
    print("COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()
