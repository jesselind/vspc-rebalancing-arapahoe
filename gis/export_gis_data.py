#!/usr/bin/env python3
"""
Export GIS data for QGIS visualization.
Exports VSPC and precinct location data as GeoJSON files.
"""

import pandas as pd
import json
from pathlib import Path

# Configuration
WORKSPACE_ROOT = Path(__file__).parent.parent
GIS_DIR = Path(__file__).parent
MASTER_PRECINCTS_FILE = WORKSPACE_ROOT / "master_precincts.csv"
MASTER_VSPCS_FILE = WORKSPACE_ROOT / "master_vspcs.csv"


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


def main():
    """Main function."""
    print("="*60)
    print("EXPORTING GIS DATA")
    print("="*60)
    print()
    
    export_vspc_locations()
    
    print()
    print("✅ GIS data export complete!")


if __name__ == '__main__':
    main()
