#!/usr/bin/env python3
"""Fix sanity check CSV with correct VSPC addresses from official source."""

import pandas as pd
from math import radians, cos, sin, asin, sqrt

def haversine_miles(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return 6371 * 0.621371 * c

# Correct VSPC addresses from official source
# https://www.arapahoeco.gov/your_county/arapahoevotes/voting_locations/voter_service_polling_centers.php
correct_vspc_addresses = {
    'Arapahoe Community College': {
        'Address': '5900 S Santa Fe Dr',
        'City': 'Littleton',
        'State': 'CO',
        'ZIP': '80120'
    },
    'Arapahoe County CentrePoint Plaza': {
        'Address': '14980 E Alameda Dr',
        'City': 'Aurora',
        'State': 'CO',
        'ZIP': '80012'
    },
    'Arapahoe County Fairgrounds': {
        'Address': '25690 E Quincy Ave',
        'City': 'Aurora',
        'State': 'CO',
        'ZIP': '80016'
    },
    'Arapahoe County Lima Plaza': {
        'Address': '6954 S Lima St',
        'City': 'Centennial',
        'State': 'CO',
        'ZIP': '80112'
    },
    'Aurora Center for Active Adults': {
        'Address': '30 Del Mar Cir',
        'City': 'Aurora',
        'State': 'CO',
        'ZIP': '80011'
    },
    'Aurora Public Schools Educational Service Center 4': {
        'Address': '1085 Peoria St',
        'City': 'Aurora',
        'State': 'CO',
        'ZIP': '80011'
    },
    'Aurora Public Schools Professional Learning & Conference Center': {
        'Address': '15771 E 1st Ave',
        'City': 'Aurora',
        'State': 'CO',
        'ZIP': '80011'
    },
    'Beck Recreation Center': {
        'Address': '800 Telluride St',
        'City': 'Aurora',
        'State': 'CO',
        'ZIP': '80011'
    },
    'Bemis Public Library': {
        'Address': '6014 S Datura St',
        'City': 'Littleton',
        'State': 'CO',
        'ZIP': '80120'
    },
    'Central Recreation Center': {
        'Address': '18150 E Vassar Pl',
        'City': 'Aurora',
        'State': 'CO',
        'ZIP': '80013'
    },
    'Cherry Creek School District Instructional Support Facility': {
        'Address': '5416 S Riviera Way',
        'City': 'Centennial',
        'State': 'CO',
        'ZIP': '80112'
    },
    'City of Aurora Municipal Center': {
        'Address': '15151 E Alameda Pkwy',
        'City': 'Aurora',
        'State': 'CO',
        'ZIP': '80012'
    },
    'City of Sheridan Municipal Building': {
        'Address': '4101 S Federal Blvd',
        'City': 'Sheridan',
        'State': 'CO',
        'ZIP': '80110'
    },
    'Community College of Aurora CentreTech Campus': {
        'Address': '16000 E CentreTech Pkwy',
        'City': 'Aurora',
        'State': 'CO',
        'ZIP': '80011'
    },
    'Cook Park Recreation Center': {
        'Address': '7100 Cherry Creek S Dr',
        'City': 'Denver',
        'State': 'CO',
        'ZIP': '80224'
    },
    'Englewood Civic Center': {
        'Address': '1000 Englewood Pkwy',
        'City': 'Englewood',
        'State': 'CO',
        'ZIP': '80110'
    },
    'Greenwood Village City Hall': {
        'Address': '6060 S Quebec St',
        'City': 'Greenwood Village',
        'State': 'CO',
        'ZIP': '80111'
    },
    'Heather Gardens': {
        'Address': '2888 S Heather Gardens Way',
        'City': 'Aurora',
        'State': 'CO',
        'ZIP': '80014'
    },
    'Kelver Library': {
        'Address': '585 S Main St',
        'City': 'Byers',
        'State': 'CO',
        'ZIP': '80103'
    },
    'Mission Viejo Library': {
        'Address': '15324 E Hampden Cir',
        'City': 'Aurora',
        'State': 'CO',
        'ZIP': '80013'
    },
    'Parkside Village Retirement Resort': {
        'Address': '14501 E Crestline Dr',
        'City': 'Aurora',
        'State': 'CO',
        'ZIP': '80015'
    },
    'Pickens Technical College': {
        'Address': '500 Airport Blvd Bldg E',
        'City': 'Aurora',
        'State': 'CO',
        'ZIP': '80011'
    },
    'Smoky Hill Library': {
        'Address': '5430 S Biscay Cir',
        'City': 'Centennial',
        'State': 'CO',
        'ZIP': '80015'
    },
    'Southglenn Library': {
        'Address': '6972 S Vine St',
        'City': 'Centennial',
        'State': 'CO',
        'ZIP': '80122'
    },
    'Tallyns Reach Library': {
        'Address': '23911 E Arapahoe Rd',
        'City': 'Aurora',
        'State': 'CO',
        'ZIP': '80016'
    },
    'The Avenue Church': {
        'Address': '13231 E Mississippi Ave',
        'City': 'Aurora',
        'State': 'CO',
        'ZIP': '80012'
    }
}

# Load data
print('Loading data...')
rebalanced = pd.read_csv('v6/VSPC_v6 - Full_Assignments_Rebalanced.csv')

# Calculate distances using correct VSPC coordinates
print('Calculating distances with correct VSPC addresses...')
distances = []
correct_addresses = []
correct_cities = []
correct_states = []
correct_zips = []

for _, row in rebalanced.iterrows():
    vspc_name = row['VSPC_Rebalanced']
    
    # Get correct address from lookup
    if vspc_name in correct_vspc_addresses:
        addr_info = correct_vspc_addresses[vspc_name]
        correct_addresses.append(addr_info['Address'])
        correct_cities.append(addr_info['City'])
        correct_states.append(addr_info['State'])
        correct_zips.append(addr_info['ZIP'])
    else:
        # Fallback to existing address if not in lookup
        correct_addresses.append(row['Address'])
        correct_cities.append(row['City'] if pd.notna(row['City']) else '')
        correct_states.append(row['State'] if pd.notna(row['State']) else '')
        correct_zips.append(row['ZIP'] if pd.notna(row['ZIP']) else '')
        print(f'  WARNING: {vspc_name} not in address lookup, using existing address')
    
    # Calculate distance using VSPC coordinates
    dist_miles = haversine_miles(
        row['Precinct_Lon'], row['Precinct_Lat'],
        row['VSPC_Lon'], row['VSPC_Lat']
    )
    distances.append(dist_miles)

rebalanced['Distance_Miles'] = distances
rebalanced['VSPC_Address_Correct'] = correct_addresses
rebalanced['VSPC_City_Correct'] = correct_cities
rebalanced['VSPC_State_Correct'] = correct_states
rebalanced['VSPC_ZIP_Correct'] = correct_zips

# Calculate total voters per VSPC
vspc_totals = rebalanced.groupby('VSPC_Rebalanced')['Voter_Count'].sum().to_dict()
rebalanced['VSPC_Total_Voters'] = rebalanced['VSPC_Rebalanced'].map(vspc_totals)

# Create corrected sanity check file
sanity_check = rebalanced[[
    'PRECINCT',
    'Voter_Count',
    'VSPC_Total_Voters',
    'VSPC_Rebalanced',
    'VSPC_Address_Correct',
    'VSPC_City_Correct',
    'VSPC_State_Correct',
    'VSPC_ZIP_Correct',
    'Distance_Miles'
]].copy()

# Rename columns
sanity_check.columns = [
    'Precinct_Number',
    'Precinct_Voters',
    'VSPC_Total_Voters',
    'VSPC_Name',
    'VSPC_Address',
    'VSPC_City',
    'VSPC_State',
    'VSPC_ZIP',
    'Distance_Miles'
]

# Sort by VSPC name, then by precinct number
sanity_check = sanity_check.sort_values(['VSPC_Name', 'Precinct_Number'])

# Round distance to 2 decimal places
sanity_check['Distance_Miles'] = sanity_check['Distance_Miles'].round(2)

# Save to CSV
output_file = 'v6/VSPC_v6 - Sanity_Check.csv'
sanity_check.to_csv(output_file, index=False)

print(f'\n✅ Created corrected: {output_file}')
print(f'Total rows: {len(sanity_check)}')

# Verify addresses are now correct
print('\n=== VERIFYING CORRECTED ADDRESSES ===')
print('\nArapahoe County CentrePoint Plaza:')
centrepoint = sanity_check[sanity_check['VSPC_Name'] == 'Arapahoe County CentrePoint Plaza']
unique_addrs = centrepoint['VSPC_Address'].unique()
print(f'  Unique addresses: {list(unique_addrs)}')
print(f'  Count: {len(centrepoint)} precincts')

print('\nArapahoe County Fairgrounds:')
fairgrounds = sanity_check[sanity_check['VSPC_Name'] == 'Arapahoe County Fairgrounds']
unique_addrs_fg = fairgrounds['VSPC_Address'].unique()
print(f'  Unique addresses: {list(unique_addrs_fg)}')
print(f'  Count: {len(fairgrounds)} precincts')

print('\nSample (first 10 rows):')
print(sanity_check.head(10).to_string(index=False))

