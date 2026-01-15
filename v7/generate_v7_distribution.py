#!/usr/bin/env python3
"""
Generate V7 Precinct Distribution CSV with Area Leads, District Captains, 
Precinct Leads, and Hand Counter positions.
"""

import pandas as pd
import os

def generate_v7_distribution():
    """Generate the V7 Precinct Distribution CSV file."""
    
    # Read the v6 sanity check file
    input_file = 'v6/VSPC_v6 - Sanity_Check.csv'
    output_dir = 'v7'
    output_file = os.path.join(output_dir, 'VSPC - Precinct Distribution.csv')
    
    # Create v7 directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Read the existing data
    df = pd.read_csv(input_file)
    
    # Add new columns for staffing
    # Area Lead - one per VSPC (will be filled manually)
    df['Area Lead'] = ''
    
    # District Captain (DC) - for alignment with GOP District Captain assignments
    df['District Captain (DC)'] = ''
    
    # Precinct Lead - one per precinct
    df['Precinct Lead'] = ''
    
    # Hand Counter positions (12 positions to allow for 10+ requirement)
    for i in range(1, 13):
        df[f'Hand Counter {i}'] = ''
    
    # Reorder columns for better readability
    # Start with precinct info, then VSPC info, then staffing info
    column_order = [
        'Precinct',
        'Voters',
        'Voter Service Polling Center (VSPC)',
        'VSPC Total Voters',
        'Address',
        'City',
        'State',
        'Zip',
        'Distance From Precinct (mi.)',
        'Area Lead',
        'District Captain (DC)',
        'Precinct Lead',
    ]
    
    # Add hand counter columns
    column_order.extend([f'Hand Counter {i}' for i in range(1, 13)])
    
    # Reorder the dataframe
    df = df[column_order]
    
    # Sort by VSPC name, then by Precinct number for easier review
    df = df.sort_values(['Voter Service Polling Center (VSPC)', 'Precinct'])
    
    # Save to CSV
    df.to_csv(output_file, index=False)
    
    print(f"✅ Created: {output_file}")
    print(f"   Total rows: {len(df)}")
    print(f"   Total columns: {len(df.columns)}")
    print(f"   Unique VSPCs: {df['Voter Service Polling Center (VSPC)'].nunique()}")
    print(f"\nColumns added:")
    print(f"   - Area Lead (one per VSPC)")
    print(f"   - District Captain (DC)")
    print(f"   - Precinct Lead (one per precinct)")
    print(f"   - Hand Counter 1-12 (12 positions per precinct)")

if __name__ == '__main__':
    generate_v7_distribution()



