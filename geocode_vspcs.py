#!/usr/bin/env python3
"""
Geocode all VSPC addresses to get high-precision coordinates.
Uses OpenStreetMap Nominatim (free, no API key required).
"""

import pandas as pd
import time
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

# File paths
MASTER_VSPCS_FILE = 'master_vspcs.csv'

def geocode_address(address, city, state, zip_code):
    """
    Geocode an address using Nominatim.
    Returns (latitude, longitude) or (None, None) if failed.
    """
    geolocator = Nominatim(user_agent="vspc_geocoding")
    
    # Build full address string
    full_address = f"{address}, {city}, {state} {zip_code}, USA"
    
    try:
        location = geolocator.geocode(full_address, timeout=10)
        if location:
            return location.latitude, location.longitude
        else:
            print(f"  ⚠️  No results for: {full_address}")
            return None, None
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        print(f"  ⚠️  Geocoding error for {full_address}: {e}")
        return None, None

def has_high_precision(lat, lon):
    """Check if coordinates have high precision (>= 10 decimal places)."""
    if pd.isna(lat) or pd.isna(lon):
        return False
    lat_str = str(lat)
    lon_str = str(lon)
    # Check if there's a decimal point and count digits after it
    if '.' in lat_str and '.' in lon_str:
        lat_decimals = len(lat_str.split('.')[1]) if '.' in lat_str else 0
        lon_decimals = len(lon_str.split('.')[1]) if '.' in lon_str else 0
        return lat_decimals >= 10 and lon_decimals >= 10
    return False

def main():
    print("="*60)
    print("GEOCODING VSPC ADDRESSES FOR HIGH-PRECISION COORDINATES")
    print("="*60)
    
    # Load master VSPCs file
    print("\nLoading master_vspcs.csv...")
    df = pd.read_csv(MASTER_VSPCS_FILE)
    print(f"  Loaded {len(df)} VSPCs")
    
    # Track updates
    updated_count = 0
    skipped_count = 0
    failed_count = 0
    
    print("\nGeocoding addresses...")
    print("  (This may take a few minutes due to rate limiting)")
    
    for idx, row in df.iterrows():
        vspc_name = row['VSPC_Name']
        current_lat = row['VSPC_Latitude']
        current_lon = row['VSPC_Longitude']
        
        # Check if already has high precision
        if has_high_precision(current_lat, current_lon):
            print(f"  ✓ {vspc_name} - Already has high precision")
            skipped_count += 1
            continue
        
        # Geocode the address
        print(f"  🔍 Geocoding: {vspc_name}")
        new_lat, new_lon = geocode_address(
            row['Address'],
            row['City'],
            row['State'],
            row['ZIP']
        )
        
        if new_lat and new_lon:
            # Update coordinates
            df.at[idx, 'VSPC_Latitude'] = new_lat
            df.at[idx, 'VSPC_Longitude'] = new_lon
            print(f"     Updated: {new_lat}, {new_lon}")
            updated_count += 1
        else:
            print(f"     ⚠️  Failed to geocode - keeping existing coordinates")
            failed_count += 1
        
        # Rate limiting: Nominatim allows 1 request per second
        if idx < len(df) - 1:  # Don't sleep after last item
            time.sleep(1.1)  # Slightly more than 1 second to be safe
    
    # Save updated file
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"  Updated: {updated_count} VSPCs")
    print(f"  Skipped (already high precision): {skipped_count} VSPCs")
    print(f"  Failed: {failed_count} VSPCs")
    
    if updated_count > 0 or failed_count == 0:
        # Create backup
        backup_file = MASTER_VSPCS_FILE.replace('.csv', '_backup.csv')
        print(f"\nCreating backup: {backup_file}")
        pd.read_csv(MASTER_VSPCS_FILE).to_csv(backup_file, index=False)
        
        # Save updated file
        print(f"Saving updated coordinates to {MASTER_VSPCS_FILE}...")
        df.to_csv(MASTER_VSPCS_FILE, index=False)
        print("  ✅ Done!")
    else:
        print("\n  ⚠️  No updates made. File not modified.")

if __name__ == '__main__':
    main()
