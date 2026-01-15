#!/usr/bin/env python3
"""
Generate V8 Spreadsheet - Complete VSPC Workbook with all 32 VSPCs
Creates rebalanced assignments with all 32 VSPCs included.
"""

import pandas as pd
import numpy as np
from math import radians, cos, sin, asin, sqrt
from pathlib import Path
import sys

# Configuration
WORKSPACE_ROOT = Path(__file__).parent
V5_DIR = WORKSPACE_ROOT / "v5"
V8_DIR = WORKSPACE_ROOT / "v8"
VOTER_DATA_FILE = WORKSPACE_ROOT / "2022 Precinct Table (4) (1).csv"

# Rebalancing parameters - Back to proven v6 approach with cross-county constraints
TARGET_TOLERANCE = 0.25  # 25% tolerance
MAX_ITERATIONS = 300  # Reasonable iterations
RURAL_VSPC_THRESHOLD = 3
MAX_CLOSEST_VSPCS = 4  # Allow moves to 2nd-4th closest VSPC (slightly more flexibility)
MIN_DISTANCE_KM = 30  # Allow moves up to 30km (~18.6 miles) away (reasonable limit)

# New VSPCs to add (with coordinates from geocoding)
NEW_VSPCS = {
    'City of Glendale Municipal Building': {
        'Address': '950 S. Birch Street',
        'City': 'Glendale',
        'State': 'CO',
        'ZIP': '80246',
        'VSPC_Lat': 39.699078,
        'VSPC_Lon': -104.936013
    },
    'Community College of Aurora Lowry Campus': {
        'Address': '710 Alton Way',
        'City': 'Denver',
        'State': 'CO',
        'ZIP': '80230',
        'VSPC_Lat': 39.702851,
        'VSPC_Lon': -104.879361
    },
    'Martin Luther King, Jr. Library': {
        'Address': '9898 E. Colfax Ave',
        'City': 'Aurora',
        'State': 'CO',
        'ZIP': '80010',
        'VSPC_Lat': 39.739659,
        'VSPC_Lon': -104.873538
    },
    'Murphy Creek Golf Course': {
        'Address': '1700 S. Old Tom Morris Rd.',
        'City': 'Aurora',
        'State': 'CO',
        'ZIP': '80018',
        'VSPC_Lat': 39.683763,
        'VSPC_Lon': -104.709516
    },
    'Trails Recreation Center': {
        'Address': '16799 E. Lake Ave.',
        'City': 'Centennial',
        'State': 'CO',
        'ZIP': '80016',
        'VSPC_Lat': 39.610379,
        'VSPC_Lon': -104.795841
    },
    'Vista PEAK': {
        'Address': '24500 E. 6th Ave',
        'City': 'Aurora',
        'State': 'CO',
        'ZIP': '80018',
        'VSPC_Lat': 39.723954,
        'VSPC_Lon': -104.701549
    }
}


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
    """
    Check if reassignment violates geographic constraints.
    
    Prevents cross-county moves (e.g., SW to NE quadrant) like precinct 132 issue.
    Distance limit is handled by MIN_DISTANCE_KM in the main algorithm.
    
    Returns:
        True if reassignment is allowed, False if it violates constraints
    """
    prec_lat = precinct_row['Precinct_Lat']
    prec_lon = precinct_row['Precinct_Lon']
    
    # Get VSPC coordinates
    if current_vspc not in vspc_dict or target_vspc not in vspc_dict:
        return False
    
    current_lat, current_lon = vspc_dict[current_vspc]
    target_lat, target_lon = vspc_dict[target_vspc]
    
    # Detect major cross-county moves using quadrant analysis
    # Divide county into quadrants based on approximate center
    # Approximate center of Arapahoe County: ~39.65°N, 104.90°W
    county_center_lat = 39.65
    county_center_lon = -104.90
    
    # Determine quadrants
    def get_quadrant(lat, lon):
        """Return quadrant: 'NE', 'NW', 'SE', 'SW'"""
        if lat >= county_center_lat:
            return 'NE' if lon >= county_center_lon else 'NW'
        else:
            return 'SE' if lon >= county_center_lon else 'SW'
    
    prec_quadrant = get_quadrant(prec_lat, prec_lon)
    current_quadrant = get_quadrant(current_lat, current_lon)
    target_quadrant = get_quadrant(target_lat, target_lon)
    
    # Prevent moves that cross opposite quadrants (e.g., SW to NE, NW to SE)
    # This prevents issues like precinct 132 being moved from SW (Englewood) to NE (MLK Library)
    opposite_pairs = [('SW', 'NE'), ('NE', 'SW'), ('NW', 'SE'), ('SE', 'NW')]
    if (current_quadrant, target_quadrant) in opposite_pairs:
        # Only allow if target is in same quadrant as precinct (reasonable move)
        if target_quadrant != prec_quadrant:
            return False
    
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


def add_new_vspcs_to_assignments(geo_assignments):
    """Add new VSPCs to the assignments and recalculate closest VSPC for each precinct."""
    print("\n=== Adding 6 New VSPCs ===")
    
    # Get existing VSPC locations
    existing_vspcs = geo_assignments[['VSPC_Name', 'VSPC_Lat', 'VSPC_Lon', 'Address', 'City', 'State', 'ZIP']].drop_duplicates()
    
    # Create VSPC dictionary with all VSPCs (existing + new)
    vspc_dict = {}
    vspc_info = {}
    
    # Add existing VSPCs
    for _, row in existing_vspcs.iterrows():
        vspc_dict[row['VSPC_Name']] = (row['VSPC_Lat'], row['VSPC_Lon'])
        vspc_info[row['VSPC_Name']] = {
            'Address': row['Address'],
            'City': row['City'],
            'State': row['State'],
            'ZIP': row['ZIP'],
            'VSPC_Lat': row['VSPC_Lat'],
            'VSPC_Lon': row['VSPC_Lon']
        }
    
    # Add new VSPCs
    for vspc_name, info in NEW_VSPCS.items():
        vspc_dict[vspc_name] = (info['VSPC_Lat'], info['VSPC_Lon'])
        vspc_info[vspc_name] = info
        print(f"  Added: {vspc_name}")
    
    print(f"\n  Total VSPCs: {len(vspc_dict)} (26 existing + 6 new)")
    
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
    num_vspcs = len(vspc_dict)  # All 32 VSPCs
    target_voters = total_voters / num_vspcs
    tolerance = target_voters * TARGET_TOLERANCE
    
    print(f"  Total voters: {total_voters:,}")
    print(f"  Number of VSPCs: {num_vspcs}")
    print(f"  Target voters per VSPC: {target_voters:,.0f} (±{tolerance:,.0f})")
    print(f"  Allowing moves to {MAX_CLOSEST_VSPCS} closest VSPCs")
    
    # Pre-calculate distances for efficiency
    print("  Pre-calculating distances...")
    precinct_distances = {}
    for _, precinct in df.iterrows():
        distances = find_vspc_distances(precinct, vspc_dict)
        precinct_distances[precinct['PRECINCT']] = distances
    
    prev_max = None
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
        
        # If we have extreme overloads (6x+ over target), use relaxed constraint
        has_extreme_overload = any(voters > target_voters * 5 for _, _, _, voters in overloaded_list)
        
        underloaded = [
            vspc for vspc, voters in current_voters.items()
            if voters < target_voters - tolerance
        ]
        
        # For extreme overloads (like Trails), also allow moves to VSPCs that are
        # slightly over target but still below 150% of target (relaxed constraint)
        can_accept_more = [
            vspc for vspc, voters in current_voters.items()
            if voters < target_voters * 1.5  # Allow moves to VSPCs up to 50% over target
        ]
        
        if not overloaded:
            print(f"  Converged after {iteration} iterations")
            break
        
        # If no underloaded VSPCs but we have extreme overloads, use relaxed constraint
        if not underloaded and has_extreme_overload:
            print(f"  No underloaded VSPCs found, using relaxed constraint (up to 150% of target) for extreme overloads")
            underloaded = can_accept_more
        elif not underloaded:
            print(f"  Converged after {iteration} iterations (no underloaded VSPCs)")
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
                
                # Try 2nd, 3rd, 4th closest VSPCs (skip closest as it's current)
                for i in range(1, min(MAX_CLOSEST_VSPCS + 1, len(distances))):
                    candidate_vspc = distances[i][0]
                    distance_km = distances[i][1]
                    
                    # Don't move if too far away
                    if distance_km > MIN_DISTANCE_KM:
                        continue
                    
                    # Check if candidate can accept more voters
                    candidate_current = current_voters.get(candidate_vspc, 0)
                    
                    # For extreme overloads, allow moves to VSPCs up to 150% of target
                    # Otherwise, only move to underloaded VSPCs
                    if has_extreme_overload:
                        can_accept = candidate_current < target_voters * 1.5
                    else:
                        can_accept = candidate_vspc in underloaded
                    
                    if can_accept:
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


def generate_v8_files():
    """Generate all V8 CSV files."""
    print("="*60)
    print("GENERATING V8 SPREADSHEET FILES WITH ALL 32 VSPCs")
    print("="*60)
    
    # Create v8 directory
    V8_DIR.mkdir(exist_ok=True)
    print(f"\nOutput directory: {V8_DIR}")
    
    # Load and prepare data
    geo_assignments, precinct_to_voters = load_and_prepare_data()
    
    # Add new VSPCs and recalculate closest assignments
    updated_geo_assignments, vspc_dict, vspc_info = add_new_vspcs_to_assignments(geo_assignments)
    
    # Identify rural VSPCs (based on updated assignments)
    rural_vspcs = identify_rural_vspcs(updated_geo_assignments)
    print(f"\n  Rural VSPCs (protected): {sorted(rural_vspcs)}")
    
    # Rebalance
    rebalanced_df = rebalance_by_voter_volume(updated_geo_assignments, rural_vspcs, vspc_dict)
    
    # Show final distribution
    print("\n=== Final Rebalanced Distribution ===")
    final_voters = rebalanced_df.groupby('VSPC_New')['Voter_Count'].sum().sort_values(ascending=False)
    final_precincts = rebalanced_df.groupby('VSPC_New')['PRECINCT'].count()
    total_voters = rebalanced_df['Voter_Count'].sum()
    target = total_voters / 32
    
    print(f"Target: {target:,.0f} voters per VSPC")
    print("\nVSPC Distribution:")
    for vspc in final_voters.index:
        voters = final_voters[vspc]
        precincts = final_precincts[vspc]
        pct = (voters / target - 1) * 100
        print(f"  {vspc}: {voters:,} voters ({precincts} precincts) [{pct:+.1f}%]")
    
    print("\n=== Generating V8 Files ===")
    
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
    updated_geo_assignments['VSPC_Rebalanced'] = updated_geo_assignments['VSPC_Name']
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
        # Keep full precision for calculations
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
            # Keep full precision for calculations
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
        # Create mapping from PRECINCT to HYPERLINK
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
    # Only include columns that exist
    column_order = [col for col in column_order if col in precinct_dist.columns]
    precinct_dist = precinct_dist[column_order]
    
    # Format mileage columns to 2 decimal places (ensures consistent formatting like 0.00, 1.00)
    mileage_cols = ['Distance to Nearest VSPC (mi.)', 'Distance to Assigned VSPC (mi.)', 'Distance Difference (mi.)']
    for col in mileage_cols:
        if col in precinct_dist.columns:
            # Ensure zeros show as "0.00" not ".00" by explicitly formatting with leading zero
            def format_mileage(x):
                if pd.isna(x):
                    return "0.00"
                val = float(x)
                # Explicitly format to ensure leading zero for values < 1.0
                return f"{val:.2f}"
            precinct_dist[col] = precinct_dist[col].apply(format_mileage)
    
    precinct_dist = precinct_dist.sort_values(['Assigned VSPC', 'Precinct'])
    precinct_dist.to_csv(V8_DIR / "VSPC - Precinct Distribution.csv", index=False)
    
    # 2. Generate Summary (one row per VSPC)
    print("  2. VSPC Summary.csv")
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
    summary.to_csv(V8_DIR / "VSPC Summary.csv", index=False)
    
    print(f"\n✅ V8 files generated in {V8_DIR}")
    print(f"   - VSPC - Precinct Distribution.csv ({len(precinct_dist)} rows)")
    print(f"   - VSPC Summary.csv ({len(summary)} rows)")


if __name__ == '__main__':
    generate_v8_files()
