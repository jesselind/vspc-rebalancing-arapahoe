#!/usr/bin/env python3
"""
Enhanced analysis of Trails Recreation Center rebalancing problem.
Identifies why the algorithm is stuck and suggests solutions.
"""

import pandas as pd
from pathlib import Path
from math import radians, cos, sin, asin, sqrt

WORKSPACE_ROOT = Path(__file__).parent
V8_DIR = WORKSPACE_ROOT / "v8"
MASTER_PRECINCTS_FILE = WORKSPACE_ROOT / "master_precincts.csv"
MASTER_VSPCS_FILE = WORKSPACE_ROOT / "master_vspcs.csv"


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


def analyze_trails_problem():
    """Analyze why Trails Recreation Center can't be rebalanced."""
    print("="*60)
    print("TRAILS RECREATION CENTER REBALANCING ANALYSIS")
    print("="*60)
    
    # Load data
    print("\nLoading data...")
    master_precincts = pd.read_csv(MASTER_PRECINCTS_FILE)
    master_vspcs = pd.read_csv(MASTER_VSPCS_FILE)
    precinct_dist = pd.read_csv(V8_DIR / "VSPC - Precinct Distribution.csv")
    vspc_summary = pd.read_csv(V8_DIR / "VSPC Summary.csv")
    
    # Merge to get precinct coordinates from master file
    master_precincts['Precinct_Lat'] = master_precincts['Precinct_Latitude']
    master_precincts['Precinct_Lon'] = master_precincts['Precinct_Longitude']
    precinct_dist = precinct_dist.merge(
        master_precincts[['PRECINCT', 'Precinct_Lat', 'Precinct_Lon']],
        left_on='Precinct',
        right_on='PRECINCT',
        how='left'
    )
    
    # Create VSPC dictionary from master file
    vspc_dict = {}
    vspc_info = {}
    for _, row in master_vspcs.iterrows():
        vspc_name = row['VSPC_Name']
        vspc_dict[vspc_name] = (row['VSPC_Latitude'], row['VSPC_Longitude'])
        
        # Get assignment info from summary if available
        vspc_row = vspc_summary[vspc_summary['Assigned VSPC'] == vspc_name]
        if len(vspc_row) > 0:
            vspc_info[vspc_name] = {
                'voters': vspc_row.iloc[0]['Voters Assigned'],
                'precincts': vspc_row.iloc[0]['Precincts Assigned']
            }
        else:
            vspc_info[vspc_name] = {'voters': 0, 'precincts': 0}
    
    # Calculate target
    total_voters = precinct_dist['Voters'].sum()
    target_voters = total_voters / len(vspc_dict)
    tolerance = target_voters * 0.25
    
    print(f"\nTarget: {target_voters:,.0f} voters per VSPC (±{tolerance:,.0f})")
    
    # Focus on Trails
    trails_vspc = "Trails Recreation Center"
    trails_precincts = precinct_dist[precinct_dist['Assigned VSPC'] == trails_vspc].copy()
    trails_voters = trails_precincts['Voters'].sum()
    
    print(f"\n{trails_vspc}:")
    print(f"  Current: {trails_voters:,} voters in {len(trails_precincts)} precincts")
    print(f"  Target: {target_voters:,.0f} voters")
    print(f"  Need to move: {trails_voters - target_voters:,.0f} voters ({len(trails_precincts)} precincts)")
    
    # Analyze potential targets for each Trails precinct
    print("\n" + "="*60)
    print("ANALYZING POTENTIAL REASSIGNMENT TARGETS")
    print("="*60)
    
    # Group by potential target VSPC
    target_analysis = {}
    
    for _, precinct in trails_precincts.iterrows():
        if pd.isna(precinct['Precinct_Lat']) or pd.isna(precinct['Precinct_Lon']):
            continue
        
        distances = find_vspc_distances(precinct, vspc_dict)
        
        if len(distances) < 2:
            continue
        
        # Check 2nd, 3rd, 4th closest (skip 1st as it's Trails)
        for i in range(1, min(5, len(distances))):
            candidate_vspc = distances[i][0]
            candidate_dist_km = distances[i][1]
            candidate_dist_mi = candidate_dist_km * 0.621371
            
            # Only consider within 30km
            if candidate_dist_km > 30:
                continue
            
            if candidate_vspc not in target_analysis:
                target_analysis[candidate_vspc] = {
                    'current_voters': vspc_info[candidate_vspc]['voters'],
                    'current_precincts': vspc_info[candidate_vspc]['precincts'],
                    'precincts_that_could_move': [],
                    'total_voters_available': 0,
                    'avg_distance_mi': 0
                }
            
            target_analysis[candidate_vspc]['precincts_that_could_move'].append({
                'precinct': int(precinct['Precinct']),
                'voters': int(precinct['Voters']),
                'distance_mi': candidate_dist_mi
            })
            target_analysis[candidate_vspc]['total_voters_available'] += int(precinct['Voters'])
    
    # Calculate average distances
    for vspc, data in target_analysis.items():
        if data['precincts_that_could_move']:
            data['avg_distance_mi'] = sum(p['distance_mi'] for p in data['precincts_that_could_move']) / len(data['precincts_that_could_move'])
    
    # Sort by potential capacity
    print("\nPotential Target VSPCs (sorted by capacity to accept more):")
    print("-" * 60)
    
    sorted_targets = sorted(
        target_analysis.items(),
        key=lambda x: (
            x[1]['current_voters'] < target_voters,  # Underloaded first
            -(x[1]['current_voters'] - target_voters)  # Then by how much under
        )
    )
    
    for vspc, data in sorted_targets:
        current = data['current_voters']
        capacity = target_voters - current
        available = data['total_voters_available']
        num_precincts = len(data['precincts_that_could_move'])
        avg_dist = data['avg_distance_mi']
        
        status = "UNDERLOADED" if current < target_voters - tolerance else \
                 "AT TARGET" if abs(current - target_voters) <= tolerance else \
                 "OVERLOADED"
        
        print(f"\n{vspc}:")
        print(f"  Status: {status}")
        print(f"  Current: {current:,} voters ({data['current_precincts']} precincts)")
        print(f"  Capacity: {capacity:+,.0f} voters")
        print(f"  Could accept: {available:,} voters from {num_precincts} Trails precincts")
        print(f"  Avg distance: {avg_dist:.2f} miles")
        
        if capacity > 0 and available > 0:
            can_accept = min(capacity, available)
            print(f"  ✅ Can accept: {can_accept:,} voters ({min(num_precincts, int(can_accept / (available/num_precincts)))} precincts)")
        elif current < target_voters + tolerance * 2:  # Within 50% of target
            print(f"  ⚠️  Could accept more if we relax constraints (currently {current/target_voters:.1f}x target)")
    
    # Summary statistics
    print("\n" + "="*60)
    print("SUMMARY & RECOMMENDATIONS")
    print("="*60)
    
    underloaded = [v for v, d in target_analysis.items() if d['current_voters'] < target_voters - tolerance]
    at_target = [v for v, d in target_analysis.items() if abs(d['current_voters'] - target_voters) <= tolerance]
    slightly_over = [v for v, d in target_analysis.items() if target_voters < d['current_voters'] <= target_voters + tolerance * 2]
    
    print(f"\nTarget VSPCs by status:")
    print(f"  Underloaded (< target - 25%): {len(underloaded)}")
    print(f"  At target (±25%): {len(at_target)}")
    print(f"  Slightly over (target to +50%): {len(slightly_over)}")
    
    total_capacity_underloaded = sum(target_voters - target_analysis[v]['current_voters'] for v in underloaded)
    total_available = sum(target_analysis[v]['total_voters_available'] for v in target_analysis.keys())
    
    print(f"\nCapacity analysis:")
    print(f"  Total capacity in underloaded VSPCs: {total_capacity_underloaded:,.0f} voters")
    print(f"  Total voters available from Trails: {total_available:,.0f} voters")
    print(f"  Need to move: {trails_voters - target_voters:,.0f} voters")
    
    if total_capacity_underloaded < trails_voters - target_voters:
        print(f"\n❌ PROBLEM: Not enough capacity in underloaded VSPCs!")
        print(f"   Need {trails_voters - target_voters:,.0f} voters, but only {total_capacity_underloaded:,.0f} available")
        print(f"\n💡 SOLUTION OPTIONS:")
        print(f"   1. Relax constraint: Allow moves to VSPCs up to +50% over target")
        print(f"   2. Increase distance limit: Allow moves up to 40-50km instead of 30km")
        print(f"   3. Allow moves to 5th-6th closest VSPCs (currently only 2nd-4th)")
        print(f"   4. Manual intervention: Identify specific precincts to move")
    else:
        print(f"\n✅ Capacity exists, but algorithm may be stuck due to:")
        print(f"   - Distance constraints (30km limit)")
        print(f"   - Only checking 2nd-4th closest VSPCs")
        print(f"   - Iteration limits or ordering issues")
    
    # Save detailed analysis
    analysis_rows = []
    for vspc, data in sorted(target_analysis.items(), key=lambda x: x[1]['current_voters']):
        for precinct_info in data['precincts_that_could_move']:
            analysis_rows.append({
                'target_vspc': vspc,
                'target_current_voters': data['current_voters'],
                'target_capacity': target_voters - data['current_voters'],
                'precinct': precinct_info['precinct'],
                'precinct_voters': precinct_info['voters'],
                'distance_mi': round(precinct_info['distance_mi'], 2),
                'target_status': 'UNDERLOADED' if data['current_voters'] < target_voters - tolerance else \
                                'AT_TARGET' if abs(data['current_voters'] - target_voters) <= tolerance else \
                                'OVERLOADED'
            })
    
    analysis_df = pd.DataFrame(analysis_rows)
    output_file = WORKSPACE_ROOT / "trails_rebalancing_detailed_analysis.csv"
    analysis_df.to_csv(output_file, index=False)
    print(f"\n✅ Detailed analysis saved to: {output_file}")


if __name__ == '__main__':
    analyze_trails_problem()
