#!/usr/bin/env python3
"""
Export GIS data for QGIS visualization.
Exports VSPC and precinct location data as GeoJSON files that can be loaded into QGIS.
"""

import pandas as pd
import json
from pathlib import Path

# Configuration
WORKSPACE_ROOT = Path(__file__).parent.parent
GIS_DIR = Path(__file__).parent
MASTER_PRECINCTS_FILE = WORKSPACE_ROOT / "master_precincts.csv"
MASTER_VSPCS_FILE = WORKSPACE_ROOT / "master_vspcs.csv"
V11_DIR = WORKSPACE_ROOT / "v11"


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


def export_vspc_locations():
    """Export VSPC locations as GeoJSON."""
    print("Exporting VSPC locations...")
    
    vspcs = pd.read_csv(MASTER_VSPCS_FILE)
    
    features = []
    for _, row in vspcs.iterrows():
        features.append(create_point_feature(
            row['VSPC_Longitude'],
            row['VSPC_Latitude'],
            {
                "name": row['VSPC_Name'],
                "address": row['Address'],
                "city": row['City'],
                "state": row['State'],
                "zip": str(row['ZIP']),
                "latitude": row['VSPC_Latitude'],
                "longitude": row['VSPC_Longitude']
            }
        ))
    
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    output_file = GIS_DIR / "vspc_locations.geojson"
    with open(output_file, 'w') as f:
        json.dump(geojson, f, indent=2)
    
    print(f"  ✅ Exported {len(features)} VSPC locations to {output_file.name}")
    return geojson


def export_precinct_locations():
    """Export precinct locations as GeoJSON."""
    print("Exporting precinct locations...")
    
    precincts = pd.read_csv(MASTER_PRECINCTS_FILE)
    
    features = []
    for _, row in precincts.iterrows():
        features.append(create_point_feature(
            row['Precinct_Longitude'],
            row['Precinct_Latitude'],
            {
                "precinct": int(row['PRECINCT']),
                "precinct_str": str(row['PRECINCT_STR']),
                "colo_prec": str(row['COLO_PREC']),
                "us_cong": int(row['US_CONG']),
                "co_sen": int(row['CO_SEN']),
                "co_hse": int(row['CO_HSE']),
                "arap": int(row['ARAP']),
                "comm": int(row['COMM']),
                "voter_count_2022": int(row['Voter_Count_2022']) if pd.notna(row['Voter_Count_2022']) else 0,
                "voter_count_current": int(row['Voter_Count_Current']) if pd.notna(row['Voter_Count_Current']) else 0,
                "hyperlink": row['HYPERLINK'] if pd.notna(row['HYPERLINK']) else "",
                "latitude": row['Precinct_Latitude'],
                "longitude": row['Precinct_Longitude']
            }
        ))
    
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    output_file = GIS_DIR / "precinct_locations.geojson"
    with open(output_file, 'w') as f:
        json.dump(geojson, f, indent=2)
    
    print(f"  ✅ Exported {len(features)} precinct locations to {output_file.name}")
    return geojson


def export_v11_assignments():
    """Export v11 precinct assignments with location data as GeoJSON."""
    print("Exporting v11 precinct assignments...")
    
    # Load master data
    precincts = pd.read_csv(MASTER_PRECINCTS_FILE)
    vspcs = pd.read_csv(MASTER_VSPCS_FILE)
    
    # Load v11 assignment data
    v11_dist = pd.read_csv(V11_DIR / "VSPC - Precinct Distribution.csv")
    
    # Merge with location data
    precincts_with_locations = precincts.merge(
        v11_dist,
        left_on='PRECINCT_STR',
        right_on='Precinct',
        how='inner'
    )
    
    # Create VSPC location lookup
    vspc_locations = {}
    for _, row in vspcs.iterrows():
        vspc_locations[row['VSPC_Name']] = (row['VSPC_Latitude'], row['VSPC_Longitude'])
    
    features = []
    for _, row in precincts_with_locations.iterrows():
        assigned_vspc = row['Assigned VSPC']
        vspc_lat, vspc_lon = vspc_locations.get(assigned_vspc, (None, None))
        
        features.append(create_point_feature(
            row['Precinct_Longitude'],
            row['Precinct_Latitude'],
            {
                "precinct": int(row['PRECINCT']),
                "precinct_str": str(row['Precinct']),
                "voters": int(row['Voters']),
                "nearest_vspc": str(row['Nearest VSPC']),
                "assigned_vspc": str(assigned_vspc),
                "distance_to_nearest_mi": float(row['Distance to Nearest VSPC (mi.)']) if pd.notna(row['Distance to Nearest VSPC (mi.)']) else 0.0,
                "distance_to_assigned_mi": float(row['Distance to Assigned VSPC (mi.)']) if pd.notna(row['Distance to Assigned VSPC (mi.)']) else 0.0,
                "distance_difference_mi": float(row['Distance Difference (mi.)']) if pd.notna(row['Distance Difference (mi.)']) else 0.0,
                "reassigned": str(row['Reassigned']).lower() == 'true',
                "voters_assigned": int(row['Voters Assigned']),
                "precincts_assigned": int(row['Precincts Assigned']),
                "vspc_address": str(row['Address']),
                "vspc_city": str(row['City']),
                "vspc_state": str(row['State']),
                "vspc_zip": str(row['Zip']),
                "vspc_latitude": vspc_lat,
                "vspc_longitude": vspc_lon,
                "precinct_latitude": row['Precinct_Latitude'],
                "precinct_longitude": row['Precinct_Longitude']
            }
        ))
    
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    output_file = GIS_DIR / "v11_precinct_assignments.geojson"
    with open(output_file, 'w') as f:
        json.dump(geojson, f, indent=2)
    
    print(f"  ✅ Exported {len(features)} v11 precinct assignments to {output_file.name}")
    return geojson


def main():
    """Export all GIS data files."""
    print("="*60)
    print("EXPORTING GIS DATA FOR QGIS")
    print("="*60)
    print(f"\nOutput directory: {GIS_DIR}\n")
    
    # Ensure output directory exists
    GIS_DIR.mkdir(exist_ok=True)
    
    # Export location data
    export_vspc_locations()
    export_precinct_locations()
    
    # Export v11 assignments if available
    if (V11_DIR / "VSPC - Precinct Distribution.csv").exists():
        export_v11_assignments()
    else:
        print(f"\n⚠️  v11 assignment data not found, skipping v11 assignments export")
    
    print(f"\n✅ GIS data export complete!")
    print(f"\nTo use in QGIS:")
    print(f"  1. Open QGIS")
    print(f"  2. Layer > Add Layer > Add Vector Layer")
    print(f"  3. Select the .geojson files from {GIS_DIR}")
    print(f"  4. Style the layers as needed:")
    print(f"     - VSPC locations: Use point markers, size by importance")
    print(f"     - Precinct locations: Use point markers, color by voter count")
    print(f"     - v11 assignments: Use point markers, color by assigned VSPC")


if __name__ == '__main__':
    main()
