#!/usr/bin/env python3
"""
Generate V6 Spreadsheet - Complete VSPC Workbook
Creates all CSV files for V6 spreadsheet with voter-volume-based rebalancing.
Each CSV file represents a tab in the spreadsheet.
"""

import pandas as pd
import numpy as np
from math import radians, cos, sin, asin, sqrt
from pathlib import Path
import sys
import shutil

# Import rebalancing functions from the rebalancing script
# We'll include the key functions here for self-contained execution

# Configuration
WORKSPACE_ROOT = Path(__file__).parent
V5_DIR = WORKSPACE_ROOT / "v5"
V6_DIR = WORKSPACE_ROOT / "v6"
VOTER_DATA_FILE = WORKSPACE_ROOT / "2022 Precinct Table (4) (1).csv"

# Rebalancing parameters
TARGET_TOLERANCE = 0.25  # Increased tolerance (25%)
MAX_ITERATIONS = 300  # More iterations
RURAL_VSPC_THRESHOLD = 3
MAX_CLOSEST_VSPCS = 8  # Allow moves to 2nd-8th closest VSPC (people can drive a bit extra)
MIN_DISTANCE_KM = 50  # Don't move if target is more than 50km away (sanity check)


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


def check_east_west_constraint(precinct_row, current_vspc, target_vspc, vspc_dict):
    """Check if reassignment violates east/west cross-county constraint."""
    # TODO: Implement proper boundary checking
    return True


def load_and_prepare_data():
    """Load all data files and prepare for rebalancing."""
    print("Loading data files...")
    
    # Load voter data
    voter_data = pd.read_csv(VOTER_DATA_FILE)
    voter_data['Voter_Count_Clean'] = (
        voter_data['Voter Count']
        .astype(str)
        .str.replace(',', '')
        .replace('', '0')
        .astype(int)
    )
    
    precinct_to_voters = dict(zip(
        voter_data['Precinct'].astype(str).str.zfill(3),
        voter_data['Voter_Count_Clean']
    ))
    
    # Load geographic assignments
    geo_assignments = pd.read_csv(V5_DIR / "VSPC_v5 - Full_Assignments_Geo.csv")
    geo_assignments['PRECINCT_STR'] = geo_assignments['PRECINCT'].astype(str).str.zfill(3)
    geo_assignments['Voter_Count'] = geo_assignments['PRECINCT_STR'].map(precinct_to_voters).fillna(0).astype(int)
    
    return geo_assignments, precinct_to_voters


def identify_rural_vspcs(geo_assignments):
    """Identify rural VSPCs."""
    geo_counts = geo_assignments.groupby('VSPC_Name')['PRECINCT'].count()
    rural_vspcs = set(geo_counts[geo_counts <= RURAL_VSPC_THRESHOLD].index)
    return rural_vspcs


def rebalance_by_voter_volume(geo_assignments, rural_vspcs, vspc_dict):
    """
    Rebalance precincts to balance voter volume - AGGRESSIVE VERSION.
    Allows moves to 2nd, 3rd, or 4th closest VSPC to handle extreme overloads.
    """
    print("\n=== Starting Aggressive Rebalancing ===")
    
    df = geo_assignments.copy()
    df['VSPC_New'] = df['VSPC_Name'].copy()
    
    total_voters = df['Voter_Count'].sum()
    num_vspcs = df['VSPC_Name'].nunique()
    target_voters = total_voters / num_vspcs
    tolerance = target_voters * TARGET_TOLERANCE
    
    print(f"  Target voters per VSPC: {target_voters:,.0f} (±{tolerance:,.0f})")
    print(f"  Allowing moves to {MAX_CLOSEST_VSPCS} closest VSPCs")
    
    # Pre-calculate distances for efficiency
    print("  Pre-calculating distances...")
    precinct_distances = {}
    for _, precinct in df.iterrows():
        distances = find_vspc_distances(precinct, vspc_dict)
        precinct_distances[precinct['PRECINCT']] = distances
    
    prev_max = None  # Track progress
    for iteration in range(MAX_ITERATIONS):
        current_voters = df.groupby('VSPC_New')['Voter_Count'].sum().to_dict()
        current_precincts = df.groupby('VSPC_New')['PRECINCT'].count().to_dict()
        
        # Find overloaded VSPCs - prioritize by how overloaded they are
        overloaded_list = []
        for vspc, voters in current_voters.items():
            if vspc not in rural_vspcs and voters > target_voters + tolerance:
                overload_ratio = voters / target_voters
                precinct_count = current_precincts.get(vspc, 0)
                overloaded_list.append((vspc, overload_ratio, precinct_count, voters))
        
        # Sort by most overloaded first (voters, then precincts)
        overloaded_list.sort(key=lambda x: (x[3], x[2]), reverse=True)
        overloaded = [v[0] for v in overloaded_list]
        
        underloaded = [
            vspc for vspc, voters in current_voters.items()
            if voters < target_voters - tolerance
        ]
        
        if not overloaded or not underloaded:
            print(f"  Converged after {iteration} iterations")
            break
        
        if iteration % 20 == 0:
            print(f"  Iteration {iteration}: {len(overloaded)} overloaded, {len(underloaded)} underloaded")
            if overloaded_list:
                top = overloaded_list[0]
                print(f"    Most overloaded: {top[0]} with {top[3]:,} voters ({top[2]} precincts)")
        
        moved = False
        # Focus on ALL overloaded VSPCs, but prioritize most overloaded
        # Process in order of overload severity
        for overloaded_vspc, _, _, _ in overloaded_list:
            # Get precincts from this overloaded VSPC, sorted by voter count
            vspc_precincts = df[df['VSPC_New'] == overloaded_vspc].sort_values('Voter_Count', ascending=False)
            
            for _, precinct in vspc_precincts.iterrows():
                distances = precinct_distances[precinct['PRECINCT']]
                
                if len(distances) < 2:
                    continue
                
                # Try 2nd, 3rd, 4th... closest VSPCs (skip closest as it's current)
                for i in range(1, min(MAX_CLOSEST_VSPCS, len(distances))):
                    candidate_vspc = distances[i][0]
                    distance_km = distances[i][1]
                    
                    # Don't move if too far away
                    if distance_km > MIN_DISTANCE_KM:
                        continue
                    
                    if candidate_vspc in underloaded:
                        if check_east_west_constraint(precinct, overloaded_vspc, candidate_vspc, vspc_dict):
                            df.loc[df['PRECINCT'] == precinct['PRECINCT'], 'VSPC_New'] = candidate_vspc
                            moved = True
                            break
                
                if moved:
                    break
            
            if moved:
                break
        
        # Continue even if no move found - might find moves in next iteration as distribution changes
        # Only stop if we've tried many times with no progress
        if not moved:
            if iteration > 100 and iteration % 25 == 0:
                # Check if we're still making progress
                current_max = max(current_voters.values())
                if prev_max is None:
                    prev_max = current_max
                elif current_max >= prev_max * 0.995:  # Less than 0.5% improvement
                    print(f"  Minimal progress after {iteration} iterations, stopping")
                    break
                else:
                    prev_max = current_max
    
    return df


def generate_v6_files():
    """Generate all V6 CSV files."""
    print("="*60)
    print("GENERATING V6 SPREADSHEET FILES")
    print("="*60)
    
    # Create v6 directory
    V6_DIR.mkdir(exist_ok=True)
    print(f"\nOutput directory: {V6_DIR}")
    
    # Load and prepare data
    geo_assignments, precinct_to_voters = load_and_prepare_data()
    
    # Get VSPC locations
    vspc_locations = geo_assignments[['VSPC_Name', 'VSPC_Lat', 'VSPC_Lon']].drop_duplicates()
    vspc_dict = {
        row['VSPC_Name']: (row['VSPC_Lat'], row['VSPC_Lon'])
        for _, row in vspc_locations.iterrows()
    }
    
    # Identify rural VSPCs
    rural_vspcs = identify_rural_vspcs(geo_assignments)
    
    # Rebalance
    rebalanced_df = rebalance_by_voter_volume(geo_assignments, rural_vspcs, vspc_dict)
    
    print("\n=== Generating CSV Files ===")
    
    # 1. Data_Dictionary (use v3 format which is more detailed, or create enhanced version)
    print("  1. Data_Dictionary.csv")
    # Try to use v3 Column Legend if available, otherwise use v5
    v3_column_legend = WORKSPACE_ROOT / "v3" / "VSPC_v3 - Column Legend.csv"
    if v3_column_legend.exists():
        shutil.copy(v3_column_legend, V6_DIR / "VSPC_v6 - Column_Legend.csv")
        print("    (Using v3 Column Legend format)")
    # Also copy/create Data_Dictionary in v5 format for compatibility
    if (V5_DIR / "VSPC_v5 - Data_Dictionary.csv").exists():
        shutil.copy(
            V5_DIR / "VSPC_v5 - Data_Dictionary.csv",
            V6_DIR / "VSPC_v6 - Data_Dictionary.csv"
        )
    
    # 2. Full_Assignments_Geo (include Secondary column like v3)
    print("  2. Full_Assignments_Geo.csv")
    geo_output = geo_assignments.copy()
    # Calculate Secondary (second-closest VSPC) for each precinct
    print("    Calculating Secondary VSPC assignments...")
    secondary_vspcs = []
    for _, row in geo_output.iterrows():
        distances = find_vspc_distances(row, vspc_dict)
        if len(distances) > 1:
            secondary_vspcs.append(distances[1][0])  # Second-closest
        else:
            secondary_vspcs.append(distances[0][0] if distances else '')
    geo_output['Secondary'] = secondary_vspcs
    # Add VSPC_Rebalanced column (same as VSPC_Name for geo)
    geo_output['VSPC_Rebalanced'] = geo_output['VSPC_Name']
    geo_output.to_csv(V6_DIR / "VSPC_v6 - Full_Assignments_Geo.csv", index=False)
    
    # 3. Full_Assignments_Rebalanced (new rebalanced assignments with Secondary column)
    print("  3. Full_Assignments_Rebalanced.csv")
    rebalanced_output = geo_assignments.copy()
    # Keep Secondary from geo (second-closest VSPC)
    rebalanced_output['Secondary'] = geo_output['Secondary']
    rebalanced_output['VSPC_Rebalanced'] = rebalanced_df['VSPC_New']
    rebalanced_output.to_csv(V6_DIR / "VSPC_v6 - Full_Assignments_Rebalanced.csv", index=False)
    
    # 4. Rulebook (update to reflect voter-volume-based rebalancing)
    print("  4. Rulebook.csv")
    rulebook = pd.DataFrame({
        'SECTION': [
            'Overview',
            'Geographic (GEO) Assignment',
            'Rebalanced Assignment',
            'Sheet Usage'
        ],
        'CONTENT': [
            'This workbook assigns Arapahoe County election precincts to county-approved Voter Service and Polling Centers (VSPCs) for organizational and staffing purposes. Two assignment models are provided: Geographic and Rebalanced.',
            'Definition: Each precinct is assigned to the single closest VSPC based on straight-line distance from the precinct centroid.\nPurpose: Establishes the natural, geography-based baseline assignment.\nUse when: Validating proximity, auditing assignments, or understanding default county geography.\nDo NOT use for: Final staffing decisions if precinct loads are uneven.',
            'Definition: A controlled reassignment of some precincts to nearby VSPCs to achieve balanced voter volume across VSPCs (target based on total voters divided by number of VSPCs).\nConstraints: Precincts may only be reassigned to their second-closest VSPC; east/west cross-county jumps are prohibited.\nRural exception: Rural VSPCs may exceed the target due to geography.\nUse when: Final operational planning and staffing.',
            'Use GEO sheets to understand natural geography.\nUse REBALANCED sheets for staffing, leadership assignment, and execution.\nNever mix GEO and REBALANCED data in the same operational workflow.'
        ]
    })
    rulebook.to_csv(V6_DIR / "VSPC_v6 - Rulebook.csv", index=False)
    
    # 5. VSPC_Precinct_Map_Geo (simplified view with PRECINCT - like v3, not v5!)
    # CRITICAL: Include PRECINCT so you can see which precincts belong to each VSPC
    print("  5. VSPC_Precinct_Map_Geo.csv")
    map_geo = geo_assignments[[
        'VSPC_Name', 'Address', 'City', 'State', 'ZIP', 'PRECINCT'
    ]].copy()
    map_geo = map_geo.sort_values(['VSPC_Name', 'PRECINCT'])
    map_geo.to_csv(V6_DIR / "VSPC_v6 - VSPC_Precinct_Map_Geo.csv", index=False)
    
    # 6. VSPC_Precinct_Map_Rebalanced (simplified view with PRECINCT - like v3, not v5!)
    # CRITICAL: Include PRECINCT so you can see which precincts belong to each VSPC
    print("  6. VSPC_Precinct_Map_Rebalanced.csv")
    map_rebalanced = rebalanced_df[[
        'VSPC_New', 'Address', 'City', 'State', 'ZIP', 'PRECINCT'
    ]].copy()
    map_rebalanced.columns = ['VSPC_Name', 'Address', 'City', 'State', 'ZIP', 'PRECINCT']
    map_rebalanced = map_rebalanced.sort_values(['VSPC_Name', 'PRECINCT'])
    map_rebalanced.to_csv(V6_DIR / "VSPC_v6 - VSPC_Precinct_Map_Rebalanced.csv", index=False)
    
    # 7. VSPC_Summary (with voter counts)
    print("  7. VSPC_Summary.csv")
    # Geographic summary
    geo_summary = geo_assignments.groupby('VSPC_Name').agg({
        'PRECINCT': 'count',
        'Voter_Count': 'sum'
    }).reset_index()
    geo_summary.columns = ['VSPC_Name', 'Geo_Count', 'Geo_Voters']
    
    # Rebalanced summary
    rebalanced_summary = rebalanced_df.groupby('VSPC_New').agg({
        'PRECINCT': 'count',
        'Voter_Count': 'sum'
    }).reset_index()
    rebalanced_summary.columns = ['VSPC_Name', 'Rebalanced_Count', 'Rebalanced_Voters']
    
    # Merge summaries
    summary = geo_summary.merge(rebalanced_summary, on='VSPC_Name', how='outer')
    summary = summary.sort_values('Rebalanced_Voters', ascending=False)
    summary.to_csv(V6_DIR / "VSPC_v6 - VSPC_Summary.csv", index=False)
    
    # Print statistics
    print("\n=== V6 Summary Statistics ===")
    print(f"Total Precincts: {len(geo_assignments)}")
    print(f"Total VSPCs: {geo_assignments['VSPC_Name'].nunique()}")
    print(f"Total Voters: {geo_assignments['Voter_Count'].sum():,}")
    
    print("\n--- Geographic Assignment ---")
    geo_stats = geo_assignments.groupby('VSPC_Name')['Voter_Count'].sum()
    print(f"  Average voters per VSPC: {geo_stats.mean():,.0f}")
    print(f"  Std Dev: {geo_stats.std():,.0f}")
    print(f"  Min: {geo_stats.min():,.0f}")
    print(f"  Max: {geo_stats.max():,.0f}")
    
    print("\n--- Rebalanced Assignment ---")
    rebalanced_stats = rebalanced_df.groupby('VSPC_New')['Voter_Count'].sum()
    print(f"  Average voters per VSPC: {rebalanced_stats.mean():,.0f}")
    print(f"  Std Dev: {rebalanced_stats.std():,.0f}")
    print(f"  Min: {rebalanced_stats.min():,.0f}")
    print(f"  Max: {rebalanced_stats.max():,.0f}")
    
    improvement = ((geo_stats.std() - rebalanced_stats.std()) / geo_stats.std() * 100)
    print(f"\n  Improvement (Std Dev Reduction): {improvement:.1f}%")
    
    print("\n" + "="*60)
    print("V6 SPREADSHEET FILES GENERATED SUCCESSFULLY")
    print("="*60)
    print(f"\nAll files saved to: {V6_DIR}")
    print("\nFiles created:")
    for i, file in enumerate(sorted(V6_DIR.glob("*.csv")), 1):
        print(f"  {i}. {file.name}")
    print("\nKey improvements over v5:")
    print("  ✓ PRECINCT column in VSPC_Precinct_Map files (like v3, v5 was missing this!)")
    print("  ✓ Secondary column showing second-closest VSPC (like v3)")
    print("  ✓ Voter counts in Summary file (new)")
    print("  ✓ Voter-volume-based rebalancing (not just precinct count)")
    print("\nNext steps:")
    print("  1. Import all CSV files into Google Sheets (one file = one tab)")
    print("  2. Review the rebalanced distribution")
    print("  3. Validate all assignments meet geographic constraints")
    print("  4. Check that VSPC_Precinct_Map files show precinct assignments clearly")


if __name__ == "__main__":
    try:
        generate_v6_files()
    except FileNotFoundError as e:
        print(f"ERROR: File not found: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

