#!/usr/bin/env python3
"""
Assign colors to precincts based on their assigned VSPC colors.

This script:
1. Loads VSPC color assignments from vspc_color_mapping.json
2. Loads precinct assignments from VSPC - Precinct Distribution.csv
3. Loads precinct location data from master_precincts.csv
4. Creates a GeoJSON file with precincts colored to match their assigned VSPC

When VSPC colors change, running this script will automatically update precinct colors.
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict

# Configuration
WORKSPACE_ROOT = Path(__file__).parent.parent
GIS_DIR = Path(__file__).parent
MASTER_PRECINCTS_FILE = WORKSPACE_ROOT.parent / "master_precincts.csv"
VSPC_COLOR_MAPPING_FILE = GIS_DIR / "vspc_color_mapping.json"
PRECINCT_DISTRIBUTION_FILE = WORKSPACE_ROOT / "VSPC - Precinct Distribution.csv"
OUTPUT_FILE = GIS_DIR / "precinct_locations_colored.geojson"


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


def load_vspc_colors() -> Dict[str, str]:
    """Load VSPC color mapping from JSON file."""
    print("Loading VSPC color assignments...")
    
    if not VSPC_COLOR_MAPPING_FILE.exists():
        print(f"  ❌ Error: {VSPC_COLOR_MAPPING_FILE.name} not found!")
        print(f"     Run assign_vspc_colors.py first to generate VSPC colors.")
        return {}
    
    with open(VSPC_COLOR_MAPPING_FILE, 'r') as f:
        colors = json.load(f)
    
    print(f"  ✅ Loaded colors for {len(colors)} VSPCs")
    return colors


def assign_precinct_colors():
    """Assign colors to precincts based on their assigned VSPC."""
    print("="*60)
    print("ASSIGNING PRECINCT COLORS FROM VSPC COLORS")
    print("="*60)
    print()
    
    # Load VSPC colors
    vspc_colors = load_vspc_colors()
    if not vspc_colors:
        return
    
    # Load precinct assignments
    print("Loading precinct assignments...")
    if not PRECINCT_DISTRIBUTION_FILE.exists():
        print(f"  ❌ Error: {PRECINCT_DISTRIBUTION_FILE.name} not found!")
        return
    
    precinct_dist = pd.read_csv(PRECINCT_DISTRIBUTION_FILE)
    print(f"  ✅ Loaded {len(precinct_dist)} precinct assignments")
    
    # Load master precincts for location data
    print("Loading precinct location data...")
    if not MASTER_PRECINCTS_FILE.exists():
        print(f"  ❌ Error: {MASTER_PRECINCTS_FILE.name} not found!")
        return
    
    master_precincts = pd.read_csv(MASTER_PRECINCTS_FILE)
    print(f"  ✅ Loaded {len(master_precincts)} precinct locations")
    
    # Merge precinct assignments with location data
    print("Merging precinct assignments with location data...")
    precincts_with_assignments = master_precincts.merge(
        precinct_dist,
        left_on='PRECINCT_STR',
        right_on='Precinct',
        how='inner'
    )
    print(f"  ✅ Merged {len(precincts_with_assignments)} precincts")
    
    # Create GeoJSON features with colors
    print("Creating GeoJSON features with colors...")
    features = []
    missing_colors = []
    missing_assignments = []
    
    for _, row in precincts_with_assignments.iterrows():
        assigned_vspc = row['Assigned VSPC']
        
        # Get color for this precinct's assigned VSPC
        precinct_color = vspc_colors.get(assigned_vspc)
        
        if precinct_color is None:
            missing_colors.append((row['PRECINCT'], assigned_vspc))
            precinct_color = "#CCCCCC"  # Default gray if VSPC color not found
        
        # Create feature with all precinct data plus color
        feature = create_point_feature(
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
                "assigned_vspc": str(assigned_vspc),
                "voters": int(row['Voters']) if pd.notna(row['Voters']) else 0,
                "nearest_vspc": str(row['Nearest VSPC']) if pd.notna(row['Nearest VSPC']) else "",
                "distance_to_assigned_mi": float(row['Distance to Assigned VSPC (mi.)']) if pd.notna(row['Distance to Assigned VSPC (mi.)']) else 0.0,
                "reassigned": str(row['Reassigned']).lower() == 'true' if pd.notna(row['Reassigned']) else False,
                # Color properties - these are what QGIS will use
                "color": precinct_color,
                "color_hex": precinct_color,
                "latitude": row['Precinct_Latitude'],
                "longitude": row['Precinct_Longitude']
            }
        )
        features.append(feature)
    
    # Report any issues
    if missing_colors:
        print(f"\n  ⚠️  WARNING: {len(missing_colors)} precincts assigned to VSPCs without colors:")
        for precinct, vspc in missing_colors[:10]:  # Show first 10
            print(f"     Precinct {precinct} -> {vspc}")
        if len(missing_colors) > 10:
            print(f"     ... and {len(missing_colors) - 10} more")
    
    # Create GeoJSON
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    # Save to file
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(geojson, f, indent=2)
    
    print(f"\n  ✅ Created {OUTPUT_FILE.name} with {len(features)} colored precincts")
    
    # Summary statistics
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total precincts: {len(features)}")
    print(f"Precincts with colors: {len(features) - len(missing_colors)}")
    if missing_colors:
        print(f"Precincts missing colors: {len(missing_colors)}")
    
    # Count precincts per VSPC color
    color_counts = {}
    for feature in features:
        color = feature['properties']['color']
        color_counts[color] = color_counts.get(color, 0) + 1
    
    print(f"\nUnique colors used: {len([c for c in color_counts.keys() if c != '#CCCCCC'])}")
    print(f"\n✅ Precinct color assignment complete!")
    print(f"\nTo use in QGIS:")
    print(f"  1. Load {OUTPUT_FILE.name} in QGIS")
    print(f"  2. In Symbology, use 'Categorized' by 'assigned_vspc'")
    print(f"  3. For each category, set the color to match the 'color' property")
    print(f"  4. Or use 'Single Symbol' and set the color data-defined override to 'color' property")


if __name__ == '__main__':
    assign_precinct_colors()
