#!/usr/bin/env python3
"""
VSPC Rebalancing Script - Voter Volume Based
Rebalances precincts to prioritize voter volume while maintaining geographic constraints.
"""

import pandas as pd
import numpy as np
from math import radians, cos, sin, asin, sqrt
from pathlib import Path
import sys

# Configuration
WORKSPACE_ROOT = Path(__file__).parent
VOTER_DATA_FILE = WORKSPACE_ROOT / "2022 Precinct Table (4) (1).csv"
GEO_ASSIGNMENTS_FILE = WORKSPACE_ROOT / "v5" / "VSPC_v5 - Full_Assignments_Geo.csv"
REBALANCED_FILE = WORKSPACE_ROOT / "v5" / "VSPC_v5 - Full_Assignments_Rebalanced.csv"
OUTPUT_DIR = WORKSPACE_ROOT / "v5_rebalanced_voter_volume"

# Rebalancing parameters
TARGET_TOLERANCE = 0.15  # 15% tolerance around target
MAX_ITERATIONS = 100
RURAL_VSPC_THRESHOLD = 3  # VSPCs with ≤3 precincts are considered rural


def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points on Earth (in km).
    
    Args:
        lon1, lat1: Longitude and latitude of first point (in decimal degrees)
        lon2, lat2: Longitude and latitude of second point (in decimal degrees)
    
    Returns:
        Distance in kilometers
    """
    # Convert to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    # Radius of Earth in kilometers
    r = 6371
    
    return r * c


def load_and_prepare_data():
    """Load all data files and prepare for rebalancing."""
    print("Loading data files...")
    
    # Load voter data
    print(f"  Loading voter data from: {VOTER_DATA_FILE}")
    voter_data = pd.read_csv(VOTER_DATA_FILE)
    
    # Clean voter counts (remove commas, convert to int)
    voter_data['Voter_Count_Clean'] = (
        voter_data['Voter Count']
        .astype(str)
        .str.replace(',', '')
        .replace('', '0')
        .astype(int)
    )
    
    # Create mapping: 3-digit precinct number -> voter count
    # The "Precinct" column in voter data is 3-digit (e.g., 101)
    # The "PRECINCT" column in assignments is also 3-digit
    precinct_to_voters = dict(zip(
        voter_data['Precinct'].astype(str).str.zfill(3),
        voter_data['Voter_Count_Clean']
    ))
    
    print(f"  Loaded {len(precinct_to_voters)} precinct voter counts")
    
    # Load geographic assignments
    print(f"  Loading geographic assignments from: {GEO_ASSIGNMENTS_FILE}")
    geo_assignments = pd.read_csv(GEO_ASSIGNMENTS_FILE)
    
    # Add voter counts to assignments
    geo_assignments['PRECINCT_STR'] = geo_assignments['PRECINCT'].astype(str).str.zfill(3)
    geo_assignments['Voter_Count'] = geo_assignments['PRECINCT_STR'].map(precinct_to_voters).fillna(0).astype(int)
    
    # Check if Voter_Coun column exists and compare
    if 'Voter_Coun' in geo_assignments.columns:
        print("  Note: Voter_Coun column exists in file, but using data from voter file for consistency")
    
    print(f"  Loaded {len(geo_assignments)} precinct assignments")
    print(f"  Total voters: {geo_assignments['Voter_Count'].sum():,}")
    
    return geo_assignments, precinct_to_voters


def find_vspc_distances(precinct_row, vspc_dict):
    """
    Find distances from a precinct to all VSPCs.
    
    Args:
        precinct_row: Row from assignments dataframe with Precinct_Lat, Precinct_Lon
        vspc_dict: Dictionary mapping VSPC_Name -> (lat, lon)
    
    Returns:
        List of tuples (VSPC_Name, distance_km) sorted by distance
    """
    distances = []
    prec_lat = precinct_row['Precinct_Lat']
    prec_lon = precinct_row['Precinct_Lon']
    
    for vspc_name, (vspc_lat, vspc_lon) in vspc_dict.items():
        dist = haversine(prec_lon, prec_lat, vspc_lon, vspc_lat)
        distances.append((vspc_name, dist))
    
    # Sort by distance
    distances.sort(key=lambda x: x[1])
    return distances


def check_east_west_constraint(precinct_row, current_vspc, target_vspc, vspc_dict):
    """
    Check if reassignment violates east/west cross-county constraint.
    
    This is a simplified check - may need refinement based on actual boundaries.
    For now, we'll use the COMM column (commission sub-area code) as a proxy.
    
    Args:
        precinct_row: Row with precinct data
        current_vspc: Current VSPC name
        target_vspc: Target VSPC name
        vspc_dict: VSPC location dictionary
    
    Returns:
        True if reassignment is allowed, False if it violates constraint
    """
    # TODO: Implement proper east/west boundary checking
    # For now, allow all reassignments (this needs to be refined)
    # Could check COMM column or use longitude-based heuristics
    return True


def identify_rural_vspcs(geo_assignments):
    """Identify rural VSPCs (those with very few precincts)."""
    geo_counts = geo_assignments.groupby('VSPC_Name')['PRECINCT'].count()
    rural_vspcs = set(geo_counts[geo_counts <= RURAL_VSPC_THRESHOLD].index)
    print(f"  Identified {len(rural_vspcs)} rural VSPCs: {sorted(rural_vspcs)}")
    return rural_vspcs


def rebalance_by_voter_volume(geo_assignments, rural_vspcs, vspc_dict):
    """
    Rebalance precincts to balance voter volume across VSPCs.
    
    Args:
        geo_assignments: DataFrame with geographic assignments
        rural_vspcs: Set of rural VSPC names (protected from losing precincts)
        vspc_dict: Dictionary mapping VSPC_Name -> (lat, lon)
    
    Returns:
        DataFrame with new VSPC assignments in 'VSPC_New' column
    """
    print("\n=== Starting Rebalancing ===")
    
    # Start with geographic assignments
    df = geo_assignments.copy()
    df['VSPC_New'] = df['VSPC_Name'].copy()
    
    # Calculate target voter count per VSPC
    total_voters = df['Voter_Count'].sum()
    num_vspcs = df['VSPC_Name'].nunique()
    target_voters = total_voters / num_vspcs
    tolerance = target_voters * TARGET_TOLERANCE
    
    print(f"  Total voters: {total_voters:,}")
    print(f"  Number of VSPCs: {num_vspcs}")
    print(f"  Target voters per VSPC: {target_voters:,.0f}")
    print(f"  Tolerance: ±{tolerance:,.0f} ({TARGET_TOLERANCE*100:.0f}%)")
    
    # Sort precincts by voter count (largest first for better balance)
    precincts_sorted = df.sort_values('Voter_Count', ascending=False).copy()
    
    # Iterative rebalancing
    for iteration in range(MAX_ITERATIONS):
        # Calculate current distribution
        current_voters = df.groupby('VSPC_New')['Voter_Count'].sum().to_dict()
        
        # Find over/under loaded VSPCs
        overloaded = [
            vspc for vspc, voters in current_voters.items()
            if voters > target_voters + tolerance and vspc not in rural_vspcs
        ]
        underloaded = [
            vspc for vspc, voters in current_voters.items()
            if voters < target_voters - tolerance
        ]
        
        if not overloaded or not underloaded:
            print(f"\n  Rebalancing converged after {iteration} iterations")
            break
        
        if iteration % 10 == 0:
            print(f"  Iteration {iteration}: {len(overloaded)} overloaded, {len(underloaded)} underloaded")
        
        # Try to move precincts from overloaded to underloaded
        moved = False
        for _, precinct in precincts_sorted.iterrows():
            current_vspc = precinct['VSPC_New']
            
            if current_vspc not in overloaded:
                continue
            
            # Find distances to all VSPCs
            distances = find_vspc_distances(precinct, vspc_dict)
            
            if len(distances) < 2:
                continue  # Need at least 2 VSPCs
            
            closest = distances[0][0]
            second_closest = distances[1][0]
            
            # Only consider second-closest VSPC
            if second_closest in underloaded:
                # Check geographic constraints
                if check_east_west_constraint(precinct, current_vspc, second_closest, vspc_dict):
                    # Reassign
                    df.loc[df['PRECINCT'] == precinct['PRECINCT'], 'VSPC_New'] = second_closest
                    moved = True
                    break
        
        if not moved:
            print(f"\n  No more moves possible after {iteration} iterations")
            break
    
    return df


def generate_output_files(rebalanced_df, geo_assignments):
    """Generate output files matching v5 structure."""
    print("\n=== Generating Output Files ===")
    
    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)
    print(f"  Output directory: {OUTPUT_DIR}")
    
    # 1. Full Assignments Rebalanced
    full_rebalanced = geo_assignments.copy()
    full_rebalanced['VSPC_Rebalanced'] = rebalanced_df['VSPC_New']
    
    output_file = OUTPUT_DIR / "VSPC_v5 - Full_Assignments_Rebalanced.csv"
    full_rebalanced.to_csv(output_file, index=False)
    print(f"  Created: {output_file.name}")
    
    # 2. VSPC Precinct Map Rebalanced
    map_rebalanced = rebalanced_df[[
        'VSPC_New', 'Address', 'City', 'State', 'ZIP', 'PRECINCT'
    ]].copy()
    map_rebalanced.columns = ['VSPC_Name', 'Address', 'City', 'State', 'ZIP', 'PRECINCT_3']
    map_rebalanced = map_rebalanced.drop_duplicates().sort_values(['VSPC_Name', 'PRECINCT_3'])
    
    output_file = OUTPUT_DIR / "VSPC_v5 - VSPC_Precinct_Map_Rebalanced.csv"
    map_rebalanced.to_csv(output_file, index=False)
    print(f"  Created: {output_file.name}")
    
    # 3. VSPC Summary
    summary = rebalanced_df.groupby('VSPC_New').agg({
        'PRECINCT': 'count',
        'Voter_Count': 'sum'
    }).reset_index()
    summary.columns = ['VSPC_Name', 'Rebalanced_Count', 'Total_Voters']
    summary = summary.sort_values('Total_Voters', ascending=False)
    
    output_file = OUTPUT_DIR / "VSPC_v5 - VSPC_Summary.csv"
    summary.to_csv(output_file, index=False)
    print(f"  Created: {output_file.name}")
    
    return summary


def print_distribution_comparison(geo_assignments, rebalanced_df):
    """Print before/after distribution comparison."""
    print("\n" + "="*60)
    print("DISTRIBUTION COMPARISON")
    print("="*60)
    
    # Current (Geographic) distribution
    print("\n--- GEOGRAPHIC ASSIGNMENT (Current) ---")
    geo_dist = geo_assignments.groupby('VSPC_Name').agg({
        'PRECINCT': 'count',
        'Voter_Count': 'sum'
    }).sort_values('Voter_Count', ascending=False)
    geo_dist.columns = ['Precinct_Count', 'Total_Voters']
    print(geo_dist.head(10))
    print(f"\nTotal Voters: {geo_dist['Total_Voters'].sum():,}")
    print(f"Average: {geo_dist['Total_Voters'].mean():,.0f}")
    print(f"Std Dev: {geo_dist['Total_Voters'].std():,.0f}")
    print(f"Min: {geo_dist['Total_Voters'].min():,.0f}")
    print(f"Max: {geo_dist['Total_Voters'].max():,.0f}")
    
    # New (Rebalanced) distribution
    print("\n--- REBALANCED BY VOTER VOLUME (New) ---")
    new_dist = rebalanced_df.groupby('VSPC_New').agg({
        'PRECINCT': 'count',
        'Voter_Count': 'sum'
    }).sort_values('Voter_Count', ascending=False)
    new_dist.columns = ['Precinct_Count', 'Total_Voters']
    print(new_dist.head(10))
    print(f"\nTotal Voters: {new_dist['Total_Voters'].sum():,}")
    print(f"Average: {new_dist['Total_Voters'].mean():,.0f}")
    print(f"Std Dev: {new_dist['Total_Voters'].std():,.0f}")
    print(f"Min: {new_dist['Total_Voters'].min():,.0f}")
    print(f"Max: {new_dist['Total_Voters'].max():,.0f}")
    
    # Improvement metrics
    print("\n--- IMPROVEMENT ---")
    improvement = ((geo_dist['Total_Voters'].std() - new_dist['Total_Voters'].std()) / 
                   geo_dist['Total_Voters'].std() * 100)
    print(f"Std Dev Reduction: {improvement:.1f}%")
    print(f"Max/Min Ratio (Geo): {geo_dist['Total_Voters'].max() / geo_dist['Total_Voters'].min():.2f}")
    print(f"Max/Min Ratio (Rebalanced): {new_dist['Total_Voters'].max() / new_dist['Total_Voters'].min():.2f}")


def main():
    """Main execution function."""
    print("="*60)
    print("VSPC REBALANCING - VOTER VOLUME BASED")
    print("="*60)
    
    try:
        # Load and prepare data
        geo_assignments, precinct_to_voters = load_and_prepare_data()
        
        # Get unique VSPC locations
        vspc_locations = geo_assignments[['VSPC_Name', 'VSPC_Lat', 'VSPC_Lon']].drop_duplicates()
        vspc_dict = {
            row['VSPC_Name']: (row['VSPC_Lat'], row['VSPC_Lon'])
            for _, row in vspc_locations.iterrows()
        }
        print(f"\n  Found {len(vspc_dict)} unique VSPCs")
        
        # Identify rural VSPCs
        rural_vspcs = identify_rural_vspcs(geo_assignments)
        
        # Rebalance
        rebalanced_df = rebalance_by_voter_volume(geo_assignments, rural_vspcs, vspc_dict)
        
        # Generate output files
        summary = generate_output_files(rebalanced_df, geo_assignments)
        
        # Print comparison
        print_distribution_comparison(geo_assignments, rebalanced_df)
        
        print("\n" + "="*60)
        print("REBALANCING COMPLETE")
        print("="*60)
        print(f"\nOutput files saved to: {OUTPUT_DIR}")
        print("\nNext steps:")
        print("  1. Review the distribution comparison above")
        print("  2. Check output files for any constraint violations")
        print("  3. Manually adjust if needed")
        print("  4. Update Rulebook to reflect voter-volume-based rebalancing")
        
    except FileNotFoundError as e:
        print(f"ERROR: File not found: {e}")
        print(f"Please ensure all data files are in the correct locations.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

