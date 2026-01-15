#!/usr/bin/env python3
"""
Generate VSPC Assignment Spreadsheets - Ripple/Cascade Rebalancing Algorithm

Uses a ripple effect where precincts move away from their nearest VSPC,
creating cascading effects that distribute load more evenly.
Uses Voter_Count from geographic file as fallback for newer precincts not in 2022 data.

This is the current version-agnostic script. Historical versions are preserved
in `Archived Resources/v1/` through `Archived Resources/v14/` for reference.
"""

import pandas as pd
import numpy as np
from math import radians, cos, sin, asin, sqrt
from pathlib import Path
import sys

# Configuration
WORKSPACE_ROOT = Path(__file__).parent
OUTPUT_DIR = WORKSPACE_ROOT / "output"
MASTER_PRECINCTS_FILE = WORKSPACE_ROOT / "master_precincts.csv"
MASTER_VSPCS_FILE = WORKSPACE_ROOT / "master_vspcs.csv"
VOTER_REGISTRATION_FILE = WORKSPACE_ROOT / "CE-VR011B_EXTERNAL_20260113_021047_03.txt"

# Rebalancing parameters - Ripple/Cascade approach (Voter Volume Focused)
TARGET_TOLERANCE = 0.25  # 25% tolerance for voter volume
MAX_ITERATIONS = 1000  # Higher limit for ripple effect
MAX_CLOSEST_VSPCS_TO_CHECK = 10  # Check up to 10th closest VSPC (no distance limit)


def haversine(lon1, lat1, lon2, lat2):
    """Calculate distance between two lat/lon points in km."""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return 6371 * c


def find_vspc_distances(precinct_row, vspc_dict):
    """Find distances from a precinct to all VSPCs, sorted by distance."""
    distances = []
    prec_lat = precinct_row['Precinct_Lat']
    prec_lon = precinct_row['Precinct_Lon']
    
    for vspc_name, (vspc_lat, vspc_lon) in vspc_dict.items():
        dist = haversine(prec_lon, prec_lat, vspc_lon, vspc_lat)
        distances.append((vspc_name, dist))
    
    distances.sort(key=lambda x: x[1])
    return distances


def load_voter_registration_data():
    """Load current voter registration data and count active voters by precinct."""
    print("  Loading current voter registration data...")
    from collections import defaultdict
    import csv
    
    precinct_to_voters = defaultdict(int)
    
    if VOTER_REGISTRATION_FILE.exists():
        with open(VOTER_REGISTRATION_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f, delimiter='|')
            for row in reader:
                if row.get('STATUS') == 'Active' and row.get('PRECINCT'):
                    precinct_code = row['PRECINCT'].strip()
                    if len(precinct_code) >= 3:
                        # Extract last 3 digits as precinct number
                        precinct_3digit = precinct_code[-3:]
                        if precinct_3digit.isdigit():
                            precinct_to_voters[precinct_3digit] += 1
        
        print(f"    Loaded {len(precinct_to_voters)} precincts with {sum(precinct_to_voters.values()):,} active voters")
    else:
        print(f"    Warning: Voter registration file not found: {VOTER_REGISTRATION_FILE}")
    
    return dict(precinct_to_voters)


def load_and_prepare_data():
    """Load all data files and prepare for rebalancing."""
    print("Loading data files...")
    
    # PRIMARY SOURCE: Load current voter registration data (most up-to-date)
    current_precinct_voters = load_voter_registration_data()
    
    # Load master precincts file (immutable data)
    print("  Loading master precincts file...")
    master_precincts = pd.read_csv(MASTER_PRECINCTS_FILE)
    master_precincts['PRECINCT_STR'] = master_precincts['PRECINCT_STR'].astype(str)
    
    # Load master VSPCs file (immutable data)
    print("  Loading master VSPCs file...")
    master_vspcs = pd.read_csv(MASTER_VSPCS_FILE)
    
    # Build geo_assignments structure from master files
    # Start with precinct data
    geo_assignments = master_precincts.copy()
    
    # Rename coordinate columns to match expected format
    geo_assignments['Precinct_Lat'] = geo_assignments['Precinct_Latitude']
    geo_assignments['Precinct_Lon'] = geo_assignments['Precinct_Longitude']
    
    # Map voter counts: Use current registration data first, then 2022 data from master file
    geo_assignments['Voter_Count'] = geo_assignments['PRECINCT_STR'].map(current_precinct_voters)
    
    # Fallback to 2022 data from master file
    missing_mask = geo_assignments['Voter_Count'].isna()
    geo_assignments.loc[missing_mask, 'Voter_Count'] = geo_assignments.loc[missing_mask, 'Voter_Count_2022']
    
    # Fill any remaining NaN with 0
    geo_assignments['Voter_Count'] = geo_assignments['Voter_Count'].fillna(0).astype(int)
    
    # Create VSPC dictionary from master_vspcs for distance calculations
    # We'll calculate initial VSPC assignments on-the-fly in add_new_vspcs_to_assignments
    # For now, add placeholder VSPC columns that will be filled when we calculate nearest VSPC
    geo_assignments['VSPC_Name'] = None  # Will be calculated
    geo_assignments['VSPC_Lat'] = None
    geo_assignments['VSPC_Lon'] = None
    geo_assignments['Address'] = None
    geo_assignments['City'] = None
    geo_assignments['State'] = None
    geo_assignments['ZIP'] = None
    
    # Create precinct_to_voters dict for return (current registration takes precedence)
    precinct_to_voters_2022 = dict(zip(
        master_precincts['PRECINCT_STR'],
        master_precincts['Voter_Count_2022']
    ))
    all_precinct_to_voters = {**precinct_to_voters_2022, **current_precinct_voters}
    
    print(f"    Loaded {len(geo_assignments)} precincts from master file")
    print(f"    Loaded {len(master_vspcs)} VSPCs from master file")
    
    return geo_assignments, all_precinct_to_voters


def add_new_vspcs_to_assignments(geo_assignments):
    """Add new VSPCs to the assignments and recalculate closest VSPC for each precinct."""
    print("\n=== Loading VSPCs and Calculating Initial Assignments ===")
    
    # Load all VSPCs from master file (includes all 32 VSPCs)
    master_vspcs = pd.read_csv(MASTER_VSPCS_FILE)
    
    # Create VSPC dictionary with all VSPCs from master file
    vspc_dict = {}
    vspc_info = {}
    
    # Add all VSPCs from master file
    for _, row in master_vspcs.iterrows():
        vspc_name = row['VSPC_Name']
        vspc_lat = row['VSPC_Latitude']
        vspc_lon = row['VSPC_Longitude']
        
        vspc_dict[vspc_name] = (vspc_lat, vspc_lon)
        vspc_info[vspc_name] = {
            'Address': row['Address'],
            'City': row['City'],
            'State': row['State'],
            'ZIP': row['ZIP'],
            'VSPC_Lat': vspc_lat,
            'VSPC_Lon': vspc_lon
        }
    
    print(f"  Loaded {len(vspc_dict)} VSPCs from master file")
    
    # Recalculate closest VSPC for each precinct
    print("\n  Recalculating closest VSPC for each precinct...")
    new_assignments = []
    
    for _, precinct in geo_assignments.iterrows():
        distances = find_vspc_distances(precinct, vspc_dict)
        closest_vspc = distances[0][0]
        
        # Get info for closest VSPC
        closest_info = vspc_info[closest_vspc]
        
        # Create new row with closest VSPC
        new_row = precinct.copy()
        new_row['VSPC_Name'] = closest_vspc
        new_row['Address'] = closest_info['Address']
        new_row['City'] = closest_info['City']
        new_row['State'] = closest_info['State']
        new_row['ZIP'] = closest_info['ZIP']
        new_row['VSPC_Lat'] = closest_info['VSPC_Lat']
        new_row['VSPC_Lon'] = closest_info['VSPC_Lon']
        
        new_assignments.append(new_row)
    
    updated_assignments = pd.DataFrame(new_assignments)
    
    # Show distribution
    print("\n  New VSPC distribution:")
    vspc_counts = updated_assignments.groupby('VSPC_Name')['PRECINCT'].count().sort_values(ascending=False)
    for vspc, count in vspc_counts.items():
        voters = updated_assignments[updated_assignments['VSPC_Name'] == vspc]['Voter_Count'].sum()
        print(f"    {vspc}: {count} precincts, {voters:,} voters")
    
    return updated_assignments, vspc_dict, vspc_info


def rebalance_by_ripple_cascade(geo_assignments, vspc_dict):
    """
    Rebalance using ripple/cascade algorithm - VOTER VOLUME FOCUSED.
    
    Key principles:
    1. Each precinct uses its NEAREST VSPC as reference point
    2. Precincts can only move AWAY from their nearest VSPC (to 2nd, 3rd, etc. closest)
    3. Focus on balancing VOTER VOLUME (not precinct count)
    4. Move from overloaded (voters > target + tolerance) to underloaded (voters < target - tolerance)
    5. Sequential processing: start with most overloaded, cascade outward
    6. Stop when voter distribution is balanced (within tolerance)
    """
    print("\n=== Starting Ripple/Cascade Rebalancing (Voter Volume Focused) ===")
    
    df = geo_assignments.copy()
    df['VSPC_New'] = df['VSPC_Name'].copy()
    
    total_voters = df['Voter_Count'].sum()
    num_vspcs = len(vspc_dict)
    target_voters = total_voters / num_vspcs
    tolerance = target_voters * TARGET_TOLERANCE
    
    print(f"  Total voters: {total_voters:,}")
    print(f"  Number of VSPCs: {num_vspcs}")
    print(f"  Target voters per VSPC: {target_voters:,.0f} (±{tolerance:,.0f})")
    print(f"  Stop condition: All VSPCs within ±{TARGET_TOLERANCE*100:.0f}% of target voter volume")
    print(f"  No distance limits - ripple will sort itself out organically")
    
    # Pre-calculate distances and nearest VSPC for each precinct
    print("  Pre-calculating distances and nearest VSPCs...")
    precinct_distances = {}
    precinct_nearest_vspc = {}
    
    for _, precinct in df.iterrows():
        distances = find_vspc_distances(precinct, vspc_dict)
        precinct_distances[precinct['PRECINCT']] = distances
        precinct_nearest_vspc[precinct['PRECINCT']] = distances[0][0]  # Store nearest VSPC
    
    distribution_round = 0
    
    while distribution_round < MAX_ITERATIONS:
        current_voters = df.groupby('VSPC_New')['Voter_Count'].sum().to_dict()
        current_precincts = df.groupby('VSPC_New')['PRECINCT'].count().to_dict()
        
        # Check stop condition: all VSPCs within tolerance of target voter volume
        overloaded_count = sum(1 for voters in current_voters.values() if voters > target_voters + tolerance)
        
        if overloaded_count == 0:
            print(f"\n  ✅ Converged after {distribution_round} distribution rounds")
            print(f"     All VSPCs within ±{TARGET_TOLERANCE*100:.0f}% of target voter volume")
            break
        
        # Find the LARGEST VSPC (by voter count) - recalculated after each distribution
        largest_vspc = max(current_voters.items(), key=lambda x: x[1])
        largest_vspc_name, largest_vspc_voters = largest_vspc
        largest_vspc_precincts = current_precincts.get(largest_vspc_name, 0)
        largest_vspc_ratio = largest_vspc_voters / target_voters
        
        if largest_vspc_voters <= target_voters + tolerance:
            print(f"\n  ✅ Converged after {distribution_round} distribution rounds")
            print(f"     Largest VSPC is within tolerance")
            break
        
        print(f"\n  Distribution Round {distribution_round + 1}: Processing {largest_vspc_name}")
        print(f"    Current: {largest_vspc_voters:,} voters ({largest_vspc_precincts} precincts, {largest_vspc_ratio:.2f}x target)")
        print(f"    Target: {target_voters:,.0f} voters")
        print(f"    Need to distribute: {largest_vspc_voters - target_voters:,.0f} voters")
        
        # Distribute this VSPC's excess voters through ripple/cascade
        # Continue until this VSPC is balanced OR no more moves are possible
        inner_iteration = 0
        vspc_initial_voters = largest_vspc_voters
        
        while inner_iteration < 500:  # Limit iterations per VSPC distribution
            current_voters = df.groupby('VSPC_New')['Voter_Count'].sum().to_dict()
            current_vspc_voters = current_voters.get(largest_vspc_name, 0)
            
            # Check if this VSPC is now balanced
            if current_vspc_voters <= target_voters + tolerance:
                print(f"    ✅ {largest_vspc_name} balanced: {current_vspc_voters:,} voters (distributed {vspc_initial_voters - current_vspc_voters:,} voters)")
                break
            
            # Find underloaded VSPCs (can accept more voters)
            underloaded = [
                vspc for vspc, voters in current_voters.items()
                if voters < target_voters - tolerance
            ]
            
            # For extreme overloads, also allow moves to VSPCs up to 150% of target
            if largest_vspc_ratio > 2.0:
                can_accept_more = [
                    vspc for vspc, voters in current_voters.items()
                    if voters < target_voters * 1.5 and vspc != largest_vspc_name
                ]
                if not underloaded:
                    underloaded = can_accept_more
            
            if not underloaded:
                print(f"    ⚠️  No VSPCs can accept more voters. {largest_vspc_name} remains at {current_vspc_voters:,} voters")
                break
            
            # Get precincts from this VSPC, sorted by voter count (largest first)
            vspc_precincts = df[df['VSPC_New'] == largest_vspc_name].copy()
            vspc_precincts = vspc_precincts.sort_values('Voter_Count', ascending=False)
            
            moved_this_iteration = False
            
            for _, precinct in vspc_precincts.iterrows():
                precinct_id = precinct['PRECINCT']
                precinct_voters = precinct['Voter_Count']
                distances = precinct_distances[precinct_id]
                nearest_vspc = precinct_nearest_vspc[precinct_id]
                current_vspc = precinct['VSPC_New']
                
                # Find current position in distance list
                current_position = None
                for i, (vspc_name, _) in enumerate(distances):
                    if vspc_name == current_vspc:
                        current_position = i
                        break
                
                if current_position is None:
                    continue
                
                # Start from next position after current (move away from nearest)
                start_pos = current_position + 1
                
                if start_pos >= len(distances):
                    continue
                
                # Try to move to next closest VSPC that can accept more voters
                for i in range(start_pos, min(MAX_CLOSEST_VSPCS_TO_CHECK, len(distances))):
                    candidate_vspc = distances[i][0]
                    candidate_current_voters = current_voters.get(candidate_vspc, 0)
                    
                    # Check if candidate can accept more voters
                    if candidate_vspc in underloaded:
                        # Best: move to underloaded VSPC
                        pass
                    elif largest_vspc_ratio > 2.0:
                        # For extreme overloads, allow moves to VSPCs that are:
                        # 1. Below 150% of target
                        # 2. Closer to target than current VSPC
                        if candidate_current_voters >= target_voters * 1.5:
                            continue
                        if candidate_current_voters >= current_vspc_voters:
                            continue
                    else:
                        # Only move to underloaded
                        if candidate_vspc not in underloaded:
                            continue
                    
                    # Accept the move
                    df.loc[df['PRECINCT'] == precinct_id, 'VSPC_New'] = candidate_vspc
                    moved_this_iteration = True
                    break
                
                if moved_this_iteration:
                    break  # Move one precinct at a time
            
            if not moved_this_iteration:
                # No more moves possible for this VSPC
                print(f"    ⚠️  No more moves possible. {largest_vspc_name} remains at {current_vspc_voters:,} voters")
                break
            
            inner_iteration += 1
        
        distribution_round += 1
    
    return df


def generate_assignments():
    """Generate all assignment CSV files."""
    print("="*60)
    print("GENERATING VSPC ASSIGNMENT FILES - RIPPLE/CASCADE ALGORITHM")
    print("="*60)
    
    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)
    print(f"\nOutput directory: {OUTPUT_DIR}")
    
    # Load and prepare data
    geo_assignments, precinct_to_voters = load_and_prepare_data()
    
    # Add new VSPCs and recalculate closest assignments
    updated_geo_assignments, vspc_dict, vspc_info = add_new_vspcs_to_assignments(geo_assignments)
    
    # Rebalance using ripple/cascade
    rebalanced_df = rebalance_by_ripple_cascade(updated_geo_assignments, vspc_dict)
    
    # Show final distribution
    print("\n=== Final Rebalanced Distribution ===")
    final_precincts = rebalanced_df.groupby('VSPC_New')['PRECINCT'].count().sort_values(ascending=False)
    final_voters = rebalanced_df.groupby('VSPC_New')['Voter_Count'].sum().sort_values(ascending=False)
    total_voters = rebalanced_df['Voter_Count'].sum()
    target_voters = total_voters / len(vspc_dict)
    tolerance = target_voters * TARGET_TOLERANCE
    
    print(f"Target: {target_voters:,.0f} voters per VSPC (±{tolerance:,.0f})")
    print("\nVSPC Distribution (sorted by voter count):")
    for vspc in final_voters.index:
        voters = final_voters[vspc]
        precinct_count = final_precincts[vspc]
        pct_diff = (voters / target_voters - 1) * 100
        status = "✅" if abs(pct_diff) <= TARGET_TOLERANCE * 100 else ("⚠️" if voters > target_voters else "📉")
        print(f"  {status} {vspc}: {voters:,} voters ({precinct_count} precincts) [{pct_diff:+.1f}%]")
    
    print("\n=== Generating Output Files ===")
    
    # Update rebalanced assignments with correct VSPC info
    rebalanced_output = updated_geo_assignments.copy()
    rebalanced_output['VSPC_Rebalanced'] = rebalanced_df['VSPC_New']
    
    # Update VSPC info for rebalanced assignments
    for vspc_name in rebalanced_output['VSPC_Rebalanced'].unique():
        if vspc_name in vspc_info:
            mask = rebalanced_output['VSPC_Rebalanced'] == vspc_name
            info = vspc_info[vspc_name]
            rebalanced_output.loc[mask, 'Address'] = info['Address']
            rebalanced_output.loc[mask, 'City'] = info['City']
            rebalanced_output.loc[mask, 'State'] = info['State']
            rebalanced_output.loc[mask, 'ZIP'] = info['ZIP']
            rebalanced_output.loc[mask, 'VSPC_Lat'] = info['VSPC_Lat']
            rebalanced_output.loc[mask, 'VSPC_Lon'] = info['VSPC_Lon']
    
    # Calculate Secondary (second-closest VSPC) for each precinct
    print("  Calculating Secondary VSPC assignments...")
    secondary_vspcs = []
    for _, row in updated_geo_assignments.iterrows():
        distances = find_vspc_distances(row, vspc_dict)
        if len(distances) > 1:
            secondary_vspcs.append(distances[1][0])
        else:
            secondary_vspcs.append(distances[0][0] if distances else '')
    
    updated_geo_assignments['Secondary'] = secondary_vspcs
    rebalanced_output['Secondary'] = secondary_vspcs
    
    # Add nearest VSPC (geographic baseline) to rebalanced output
    print("  Adding nearest VSPC (geographic baseline)...")
    rebalanced_output = rebalanced_output.merge(
        updated_geo_assignments[['PRECINCT', 'VSPC_Name']],
        on='PRECINCT',
        how='left',
        suffixes=('', '_Nearest')
    )
    rebalanced_output['Nearest_VSPC'] = rebalanced_output['VSPC_Name']
    rebalanced_output['Reassigned'] = (rebalanced_output['VSPC_Rebalanced'] != rebalanced_output['Nearest_VSPC'])
    
    # Calculate distances for rebalanced assignments
    print("  Calculating distances for rebalanced assignments...")
    distances_rebalanced = []
    for _, row in rebalanced_output.iterrows():
        dist_miles = haversine(
            row['Precinct_Lon'], row['Precinct_Lat'],
            row['VSPC_Lon'], row['VSPC_Lat']
        ) * 0.621371  # Convert km to miles
        distances_rebalanced.append(dist_miles)
    rebalanced_output['Distance_To_Assigned_Miles'] = distances_rebalanced
    
    # Calculate distances to nearest VSPC (geographic baseline)
    print("  Calculating distances to nearest VSPC...")
    distances_nearest = []
    for _, row in rebalanced_output.iterrows():
        nearest_vspc = row['Nearest_VSPC']
        if nearest_vspc in vspc_info:
            nearest_info = vspc_info[nearest_vspc]
            dist_miles = haversine(
                row['Precinct_Lon'], row['Precinct_Lat'],
                nearest_info['VSPC_Lon'], nearest_info['VSPC_Lat']
            ) * 0.621371  # Convert km to miles
            distances_nearest.append(dist_miles)
        else:
            distances_nearest.append(0.0)
    rebalanced_output['Distance_To_Nearest_Miles'] = distances_nearest
    
    # Calculate difference (assigned - nearest) - keep full precision
    rebalanced_output['Distance_Difference_Miles'] = (
        rebalanced_output['Distance_To_Assigned_Miles'] - 
        rebalanced_output['Distance_To_Nearest_Miles']
    )
    
    # Add HYPERLINK column from original geo_assignments if not already present
    if 'HYPERLINK' not in rebalanced_output.columns:
        precinct_to_hyperlink = dict(zip(
            geo_assignments['PRECINCT'].astype(str).str.zfill(3),
            geo_assignments['HYPERLINK']
        ))
        rebalanced_output['HYPERLINK'] = rebalanced_output['PRECINCT'].astype(str).str.zfill(3).map(precinct_to_hyperlink)
    
    # 1. Generate Precinct Distribution (one row per precinct)
    print("  1. VSPC - Precinct Distribution.csv")
    precinct_dist = rebalanced_output[[
        'PRECINCT', 'Voter_Count', 'Nearest_VSPC', 'Distance_To_Nearest_Miles',
        'VSPC_Rebalanced', 'Distance_To_Assigned_Miles', 'Distance_Difference_Miles',
        'Address', 'City', 'State', 'ZIP', 'Reassigned', 'HYPERLINK'
    ]].copy()
    precinct_dist.columns = [
        'Precinct', 'Voters', 'Nearest VSPC', 'Distance to Nearest VSPC (mi.)',
        'Assigned VSPC', 'Distance to Assigned VSPC (mi.)', 'Distance Difference (mi.)',
        'Address', 'City', 'State', 'Zip', 'Reassigned', 'Precinct Map URL'
    ]
    
    # Calculate VSPC totals
    vspc_totals = precinct_dist.groupby('Assigned VSPC').agg({
        'Voters': 'sum',
        'Precinct': 'count'
    }).reset_index()
    vspc_totals.columns = ['Assigned VSPC', 'Voters Assigned', 'Precincts Assigned']
    
    precinct_dist = precinct_dist.merge(vspc_totals, on='Assigned VSPC')
    
    # Reorder columns
    column_order = [
        'Precinct', 'Voters', 'Nearest VSPC', 'Distance to Nearest VSPC (mi.)',
        'Assigned VSPC', 'Distance to Assigned VSPC (mi.)', 'Distance Difference (mi.)',
        'Reassigned', 'Voters Assigned', 'Precincts Assigned', 'Address', 'City', 'State', 'Zip', 'Precinct Map URL'
    ]
    column_order = [col for col in column_order if col in precinct_dist.columns]
    precinct_dist = precinct_dist[column_order]
    
    # Format mileage columns to 2 decimal places
    mileage_cols = ['Distance to Nearest VSPC (mi.)', 'Distance to Assigned VSPC (mi.)', 'Distance Difference (mi.)']
    for col in mileage_cols:
        if col in precinct_dist.columns:
            def format_mileage(x):
                if pd.isna(x):
                    return "0.00"
                val = float(x)
                return f"{val:.2f}"
            precinct_dist[col] = precinct_dist[col].apply(format_mileage)
    
    precinct_dist = precinct_dist.sort_values('Precinct')
    precinct_dist.to_csv(OUTPUT_DIR / "VSPC - Precinct Distribution.csv", index=False)
    
    # 2. Generate Summary (one row per VSPC)
    print("  2. VSPC Locations.csv")
    summary = vspc_totals.copy()
    summary = summary.merge(
        rebalanced_output[['VSPC_Rebalanced', 'Address', 'City', 'State', 'ZIP']].drop_duplicates(),
        left_on='Assigned VSPC',
        right_on='VSPC_Rebalanced',
        how='right'
    )
    summary = summary[[
        'Assigned VSPC', 'Voters Assigned', 'Precincts Assigned',
        'Address', 'City', 'State', 'ZIP'
    ]].drop_duplicates()
    summary = summary.sort_values('Assigned VSPC')
    summary.to_csv(OUTPUT_DIR / "VSPC Locations.csv", index=False)
    
    # 3. Generate Summary Statistics
    print("  3. Summary Statistics.csv")
    total_vspcs = len(vspc_dict)
    total_precincts = len(precinct_dist)
    # Count reassigned precincts (where Reassigned = True)
    total_precincts_reassigned = len(precinct_dist[precinct_dist['Reassigned'] == True])
    
    stats_data = {
        'Metric': [
            'Total Number of VSPCs',
            'Total Number of Precincts',
            'Total Number of Precincts Reassigned'
        ],
        'Value': [
            total_vspcs,
            total_precincts,
            total_precincts_reassigned
        ]
    }
    stats_df = pd.DataFrame(stats_data)
    stats_df.to_csv(OUTPUT_DIR / "Summary Statistics.csv", index=False)
    
    print(f"\n✅ Assignment files generated in {OUTPUT_DIR}")
    print(f"   - VSPC - Precinct Distribution.csv ({len(precinct_dist)} rows)")
    print(f"   - VSPC Locations.csv ({len(summary)} rows)")
    print(f"   - Summary Statistics.csv ({len(stats_df)} rows)")


if __name__ == '__main__':
    generate_assignments()
