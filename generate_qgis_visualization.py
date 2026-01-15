#!/usr/bin/env python3
"""
Generate QGIS visualization files for VSPC rebalancing analysis.
Creates GeoJSON files that can be loaded into QGIS to visualize:
- Precinct assignments (especially Trails Recreation Center)
- VSPC locations
- Potential reassignment opportunities
- Distance constraints
"""

import pandas as pd
import json
from pathlib import Path
from math import radians, cos, sin, asin, sqrt

# Configuration
WORKSPACE_ROOT = Path(__file__).parent
V8_DIR = WORKSPACE_ROOT / "v8"
OUTPUT_DIR = WORKSPACE_ROOT / "qgis_visualization"
OUTPUT_DIR.mkdir(exist_ok=True)
MASTER_PRECINCTS_FILE = WORKSPACE_ROOT / "master_precincts.csv"
MASTER_VSPCS_FILE = WORKSPACE_ROOT / "master_vspcs.csv"

# Rebalancing parameters (from generate_v8_rebalanced.py)
MAX_CLOSEST_VSPCS = 4
MIN_DISTANCE_KM = 30  # 30km = ~18.6 miles


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


def create_point_feature(lon, lat, properties):
    """Create a GeoJSON Point feature."""
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [lon, lat]
        },
        "properties": properties
    }


def create_line_feature(coords_list, properties):
    """Create a GeoJSON LineString feature."""
    return {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": coords_list
        },
        "properties": properties
    }


def create_circle_feature(center_lon, center_lat, radius_km, num_points=64):
    """Create a circular polygon feature (for distance buffers)."""
    coords = []
    for i in range(num_points + 1):
        angle = 2 * 3.14159265359 * i / num_points
        # Approximate circle using lat/lon (good enough for visualization)
        # 1 degree latitude ≈ 111 km
        # 1 degree longitude ≈ 111 km * cos(latitude)
        lat_offset = (radius_km / 111.0) * cos(angle)
        lon_offset = (radius_km / (111.0 * cos(radians(center_lat)))) * sin(angle)
        coords.append([center_lon + lon_offset, center_lat + lat_offset])
    
    return {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [coords]
        },
        "properties": {}
    }


def generate_qgis_files():
    """Generate GeoJSON files for QGIS visualization."""
    print("="*60)
    print("GENERATING QGIS VISUALIZATION FILES")
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
                'precincts': vspc_row.iloc[0]['Precincts Assigned'],
                'address': row['Address'],
                'city': row['City']
            }
        else:
            vspc_info[vspc_name] = {
                'voters': 0,
                'precincts': 0,
                'address': row['Address'],
                'city': row['City']
            }
    
    print(f"  Loaded {len(precinct_dist)} precincts")
    print(f"  Loaded {len(vspc_dict)} VSPCs")
    
    # Focus on Trails Recreation Center
    trails_vspc = "Trails Recreation Center"
    trails_precincts = precinct_dist[precinct_dist['Assigned VSPC'] == trails_vspc].copy()
    print(f"\n  Trails Recreation Center: {len(trails_precincts)} precincts, {trails_precincts['Voters'].sum():,} voters")
    
    # Calculate target
    total_voters = precinct_dist['Voters'].sum()
    target_voters = total_voters / len(vspc_dict)
    print(f"  Target per VSPC: {target_voters:,.0f} voters")
    print(f"  Trails is {trails_precincts['Voters'].sum() / target_voters:.1f}x over target")
    
    # 1. Generate Precinct Points (all precincts)
    print("\n1. Generating precinct points...")
    precinct_features = []
    for _, row in precinct_dist.iterrows():
        if pd.isna(row['Precinct_Lat']) or pd.isna(row['Precinct_Lon']):
            continue
        
        is_trails = row['Assigned VSPC'] == trails_vspc
        is_reassigned = str(row['Reassigned']).lower() == 'true'
        
        precinct_features.append(create_point_feature(
            row['Precinct_Lon'],
            row['Precinct_Lat'],
            {
                "precinct": int(row['Precinct']),
                "voters": int(row['Voters']),
                "nearest_vspc": str(row['Nearest VSPC']),
                "assigned_vspc": str(row['Assigned VSPC']),
                "distance_to_nearest_mi": float(row['Distance to Nearest VSPC (mi.)']),
                "distance_to_assigned_mi": float(row['Distance to Assigned VSPC (mi.)']),
                "distance_diff_mi": float(row['Distance Difference (mi.)']),
                "reassigned": "Yes" if is_reassigned else "No",
                "is_trails": "Yes" if is_trails else "No",
                "color": "#FF0000" if is_trails else ("#00FF00" if is_reassigned else "#888888")
            }
        ))
    
    precinct_geojson = {
        "type": "FeatureCollection",
        "features": precinct_features
    }
    
    with open(OUTPUT_DIR / "precincts.geojson", 'w') as f:
        json.dump(precinct_geojson, f, indent=2)
    print(f"   Saved: precincts.geojson ({len(precinct_features)} features)")
    
    # 2. Generate VSPC Points
    print("\n2. Generating VSPC points...")
    vspc_features = []
    for vspc_name, (lat, lon) in vspc_dict.items():
        info = vspc_info.get(vspc_name, {})
        is_trails = vspc_name == trails_vspc
        is_overloaded = info.get('voters', 0) > target_voters * 1.25
        is_underloaded = info.get('voters', 0) < target_voters * 0.75
        
        vspc_features.append(create_point_feature(
            lon,
            lat,
            {
                "vspc_name": str(vspc_name),
                "voters": int(info.get('voters', 0)),
                "precincts": int(info.get('precincts', 0)),
                "address": str(info.get('address', '')),
                "city": str(info.get('city', '')),
                "is_trails": "Yes" if is_trails else "No",
                "is_overloaded": "Yes" if is_overloaded else "No",
                "is_underloaded": "Yes" if is_underloaded else "No",
                "target_ratio": round(info.get('voters', 0) / target_voters if target_voters > 0 else 0, 2),
                "color": "#FF0000" if is_trails else ("#FF8800" if is_overloaded else ("#00FF00" if is_underloaded else "#0000FF"))
            }
        ))
    
    vspc_geojson = {
        "type": "FeatureCollection",
        "features": vspc_features
    }
    
    with open(OUTPUT_DIR / "vspcs.geojson", 'w') as f:
        json.dump(vspc_geojson, f, indent=2)
    print(f"   Saved: vspcs.geojson ({len(vspc_features)} features)")
    
    # 3. Generate potential reassignment lines (for Trails Recreation Center precincts)
    print("\n3. Analyzing potential reassignments for Trails Recreation Center...")
    reassignment_lines = []
    reassignment_analysis = []
    
    for _, precinct in trails_precincts.iterrows():
        if pd.isna(precinct['Precinct_Lat']) or pd.isna(precinct['Precinct_Lon']):
            continue
        
        # Find distances to all VSPCs
        distances = find_vspc_distances(precinct, vspc_dict)
        
        if len(distances) < 2:
            continue
        
        current_vspc = trails_vspc
        current_dist = distances[0][1]  # Should be Trails
        
        # Check 2nd, 3rd, 4th closest VSPCs
        potential_targets = []
        for i in range(1, min(MAX_CLOSEST_VSPCS + 1, len(distances))):
            candidate_vspc = distances[i][0]
            candidate_dist_km = distances[i][1]
            candidate_dist_mi = candidate_dist_km * 0.621371
            
            # Check if within distance limit
            if candidate_dist_km > MIN_DISTANCE_KM:
                continue
            
            # Get candidate VSPC info
            candidate_info = vspc_info.get(candidate_vspc, {})
            candidate_voters = candidate_info.get('voters', 0)
            is_underloaded = candidate_voters < target_voters * 0.75
            
            potential_targets.append({
                'vspc': candidate_vspc,
                'distance_km': candidate_dist_km,
                'distance_mi': candidate_dist_mi,
                'current_voters': candidate_voters,
                'is_underloaded': is_underloaded
            })
            
            # Create line from precinct to candidate VSPC
            candidate_coords = vspc_dict[candidate_vspc]
            reassignment_lines.append(create_line_feature(
                [
                    [precinct['Precinct_Lon'], precinct['Precinct_Lat']],
                    [candidate_coords[1], candidate_coords[0]]  # lon, lat
                ],
                {
                    "precinct": int(precinct['Precinct']),
                    "voters": int(precinct['Voters']),
                    "from_vspc": str(current_vspc),
                    "to_vspc": str(candidate_vspc),
                    "distance_mi": round(candidate_dist_mi, 2),
                    "to_vspc_voters": int(candidate_voters),
                    "to_vspc_underloaded": "Yes" if is_underloaded else "No",
                    "color": "#00FF00" if is_underloaded else "#FFFF00"
                }
            ))
        
        reassignment_analysis.append({
            'precinct': int(precinct['Precinct']),
            'voters': int(precinct['Voters']),
            'current_vspc': current_vspc,
            'potential_targets': len(potential_targets),
            'underloaded_targets': sum(1 for t in potential_targets if t['is_underloaded'])
        })
    
    reassignment_geojson = {
        "type": "FeatureCollection",
        "features": reassignment_lines
    }
    
    with open(OUTPUT_DIR / "reassignment_opportunities.geojson", 'w') as f:
        json.dump(reassignment_geojson, f, indent=2)
    print(f"   Saved: reassignment_opportunities.geojson ({len(reassignment_lines)} features)")
    
    # Save analysis summary
    analysis_df = pd.DataFrame(reassignment_analysis)
    analysis_df.to_csv(OUTPUT_DIR / "trails_reassignment_analysis.csv", index=False)
    print(f"   Saved: trails_reassignment_analysis.csv")
    
    # 4. Generate distance buffer around Trails Recreation Center
    print("\n4. Generating distance buffers...")
    trails_coords = vspc_dict[trails_vspc]
    buffer_features = [
        create_circle_feature(
            trails_coords[1], trails_coords[0],  # lon, lat
            radius_km,
            num_points=64
        )
        for radius_km in [10, 20, 30]  # 10km, 20km, 30km buffers
    ]
    
    buffer_geojson = {
        "type": "FeatureCollection",
        "features": buffer_features
    }
    
    with open(OUTPUT_DIR / "distance_buffers.geojson", 'w') as f:
        json.dump(buffer_geojson, f, indent=2)
    print(f"   Saved: distance_buffers.geojson (3 buffer rings)")
    
    # 5. Generate summary report
    print("\n5. Generating summary report...")
    summary_lines = [
        "# Trails Recreation Center Rebalancing Analysis",
        "",
        f"**Current Status:**",
        f"- Precincts assigned: {len(trails_precincts)}",
        f"- Voters assigned: {trails_precincts['Voters'].sum():,}",
        f"- Target voters: {target_voters:,.0f}",
        f"- Over target by: {(trails_precincts['Voters'].sum() / target_voters - 1) * 100:.1f}%",
        "",
        f"**Reassignment Opportunities:**",
        f"- Precincts with potential targets: {sum(1 for a in reassignment_analysis if a['potential_targets'] > 0)}",
        f"- Precincts with underloaded targets: {sum(1 for a in reassignment_analysis if a['underloaded_targets'] > 0)}",
        "",
        f"**QGIS Files Generated:**",
        f"- precincts.geojson - All precinct points (red = Trails, green = reassigned, gray = other)",
        f"- vspcs.geojson - All VSPC locations (red = Trails, orange = overloaded, green = underloaded)",
        f"- reassignment_opportunities.geojson - Lines showing potential moves (green = to underloaded VSPC)",
        f"- distance_buffers.geojson - 10km, 20km, 30km buffers around Trails Recreation Center",
        f"- trails_reassignment_analysis.csv - Detailed analysis of each precinct",
        "",
        "**QGIS Styling Suggestions:**",
        "- Precincts: Use 'color' field for styling",
        "- VSPCs: Use 'color' field, size by 'voters'",
        "- Reassignment lines: Use 'color' field, width by 'voters'",
        "- Buffers: Semi-transparent fill, no outline",
    ]
    
    with open(OUTPUT_DIR / "README.md", 'w') as f:
        f.write('\n'.join(summary_lines))
    print(f"   Saved: README.md")
    
    print(f"\n✅ QGIS visualization files generated in {OUTPUT_DIR}")
    print(f"\n   To use in QGIS:")
    print(f"   1. Open QGIS")
    print(f"   2. Layer > Add Layer > Add Vector Layer")
    print(f"   3. Select the .geojson files from {OUTPUT_DIR}")
    print(f"   4. Style using the 'color' property in each layer")


if __name__ == '__main__':
    generate_qgis_files()
