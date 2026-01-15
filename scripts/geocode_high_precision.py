#!/usr/bin/env python3
"""
Geocode all VSPC addresses to get ultra-high-precision coordinates.
Uses multiple geocoding services to get maximum precision.
"""

import pandas as pd
import time
import requests
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

# File paths
MASTER_VSPCS_FILE = 'master_vspcs.csv'

def geocode_with_nominatim(address, city, state, zip_code):
    """Geocode using Nominatim with raw response for higher precision."""
    geolocator = Nominatim(user_agent="vspc_geocoding_high_precision")
    full_address = f"{address}, {city}, {state} {zip_code}, USA"
    
    try:
        # Use raw=True to get the raw response with more precision
        location = geolocator.geocode(full_address, timeout=10, exactly_one=True)
        if location:
            # Try to get raw response for higher precision
            raw = geolocator.geocode(full_address, timeout=10, exactly_one=True, raw=True)
            if raw and 'lat' in raw.raw and 'lon' in raw.raw:
                return float(raw.raw['lat']), float(raw.raw['lon'])
            return location.latitude, location.longitude
        return None, None
    except Exception as e:
        print(f"    Nominatim error: {e}")
        return None, None

def geocode_with_photon(address, city, state, zip_code):
    """Geocode using Photon (OpenStreetMap-based, often higher precision)."""
    full_address = f"{address}, {city}, {state} {zip_code}"
    url = "https://photon.komoot.io/api/"
    params = {
        'q': full_address,
        'limit': 1
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'features' in data and len(data['features']) > 0:
                coords = data['features'][0]['geometry']['coordinates']
                return coords[1], coords[0]  # lat, lon (Photon returns lon, lat)
        return None, None
    except Exception as e:
        print(f"    Photon error: {e}")
        return None, None

def geocode_with_geocoding_earth(address, city, state, zip_code):
    """Geocode using Geocoding.earth (free tier, high precision)."""
    full_address = f"{address}, {city}, {state} {zip_code}, USA"
    url = "https://api.geocoding.earth/v1/search"
    params = {
        'text': full_address,
        'api_key': ''  # Free tier doesn't require key
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'features' in data and len(data['features']) > 0:
                coords = data['features'][0]['geometry']['coordinates']
                return coords[1], coords[0]  # lat, lon
        return None, None
    except Exception as e:
        print(f"    Geocoding.earth error: {e}")
        return None, None

def geocode_address_high_precision(address, city, state, zip_code):
    """
    Try multiple geocoding services to get highest precision coordinates.
    Returns (latitude, longitude) with maximum available precision.
    """
    # Try Photon first (often has good precision)
    lat, lon = geocode_with_photon(address, city, state, zip_code)
    if lat and lon:
        print(f"    Using Photon: {lat}, {lon}")
        return lat, lon
    
    # Try Nominatim with raw response
    lat, lon = geocode_with_nominatim(address, city, state, zip_code)
    if lat and lon:
        print(f"    Using Nominatim: {lat}, {lon}")
        return lat, lon
    
    # Try Geocoding.earth as fallback
    lat, lon = geocode_with_geocoding_earth(address, city, state, zip_code)
    if lat and lon:
        print(f"    Using Geocoding.earth: {lat}, {lon}")
        return lat, lon
    
    return None, None

def has_high_precision(lat, lon):
    """Check if coordinates have very high precision (>= 13 decimal places)."""
    if pd.isna(lat) or pd.isna(lon):
        return False
    lat_str = str(lat)
    lon_str = str(lon)
    if '.' in lat_str and '.' in lon_str:
        lat_decimals = len(lat_str.split('.')[1]) if '.' in lat_str else 0
        lon_decimals = len(lon_str.split('.')[1]) if '.' in lon_str else 0
        return lat_decimals >= 13 and lon_decimals >= 13
    return False

def main():
    print("="*60)
    print("GEOCODING VSPC ADDRESSES FOR ULTRA-HIGH-PRECISION COORDINATES")
    print("="*60)
    
    # Load master VSPCs file
    print("\nLoading master_vspcs.csv...")
    df = pd.read_csv(MASTER_VSPCS_FILE)
    print(f"  Loaded {len(df)} VSPCs")
    
    # Track updates
    updated_count = 0
    skipped_count = 0
    failed_count = 0
    
    print("\nGeocoding addresses for maximum precision...")
    print("  (This may take a few minutes due to rate limiting)")
    
    for idx, row in df.iterrows():
        vspc_name = row['VSPC_Name']
        current_lat = row['VSPC_Latitude']
        current_lon = row['VSPC_Longitude']
        
        # Check if already has very high precision (13+ decimals)
        if has_high_precision(current_lat, current_lon):
            print(f"  ✓ {vspc_name} - Already has very high precision")
            skipped_count += 1
            continue
        
        # Geocode the address
        print(f"  🔍 Geocoding: {vspc_name}")
        new_lat, new_lon = geocode_address_high_precision(
            row['Address'],
            row['City'],
            row['State'],
            row['ZIP']
        )
        
        if new_lat and new_lon:
            # Update coordinates
            df.at[idx, 'VSPC_Latitude'] = new_lat
            df.at[idx, 'VSPC_Longitude'] = new_lon
            updated_count += 1
        else:
            print(f"     ⚠️  Failed to geocode - keeping existing coordinates")
            failed_count += 1
        
        # Rate limiting
        if idx < len(df) - 1:
            time.sleep(1.2)
    
    # Save updated file
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"  Updated: {updated_count} VSPCs")
    print(f"  Skipped (already high precision): {skipped_count} VSPCs")
    print(f"  Failed: {failed_count} VSPCs")
    
    if updated_count > 0:
        # Create backup
        backup_file = MASTER_VSPCS_FILE.replace('.csv', '_backup2.csv')
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
