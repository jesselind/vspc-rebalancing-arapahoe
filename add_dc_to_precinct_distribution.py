#!/usr/bin/env python3
"""
Deprecated: Primary Captain District is no longer added to VSPC - Precinct Distribution.csv.

DC-aware scripts merge from DC-PL-grouping.csv in memory (see dc_precinct_merge.py).
"""

from pathlib import Path

WORKSPACE_ROOT = Path(__file__).parent


def main():
    print("=" * 60)
    print("add_dc_to_precinct_distribution.py (deprecated)")
    print("=" * 60)
    print()
    print("This script no longer modifies VSPC - Precinct Distribution.csv.")
    print("Primary Captain District is merged from DC-PL-grouping.csv inside:")
    print("  - assign_dc_to_vspc_locations.py")
    print("  - add_secondary_dc.py")
    print("  - create_dc_verification.py")
    print()
    print("Shared helper: dc_precinct_merge.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
