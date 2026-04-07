"""
In-memory merge of District Captain (Primary Captain District) from DC-PL-grouping.csv.

VSPC - Precinct Distribution.csv intentionally does NOT include this column.
Scripts that need DC per precinct call prepare_precinct_dist_for_dc() after loading the CSV.
"""

import pandas as pd

PRECINCT_COORDINATORS_COLUMN = "Precinct Coordinators"


def normalize_precinct_coordinators_column(df: pd.DataFrame) -> pd.DataFrame:
    """Avoid 1.0 float artifacts when pandas reads mixed blank/numeric cells."""
    if PRECINCT_COORDINATORS_COLUMN not in df.columns:
        return df
    df = df.copy()

    def norm(value):
        if pd.isna(value) or value == "" or (isinstance(value, str) and value.strip() == ""):
            return ""
        try:
            return str(int(float(value)))
        except (ValueError, TypeError):
            return str(value).strip()

    df[PRECINCT_COORDINATORS_COLUMN] = df[PRECINCT_COORDINATORS_COLUMN].map(norm)
    return df


def precinct_to_dc_map(dc_grouping: pd.DataFrame) -> dict:
    """Map 3-digit precinct string -> DC int (first occurrence wins)."""
    precinct_to_dc = {}
    for _, row in dc_grouping.iterrows():
        dc = row["DC"]
        pv = row["New Pct#"]
        if pd.notna(dc) and pd.notna(pv):
            k = str(int(float(pv)))
            if k not in precinct_to_dc:
                precinct_to_dc[k] = int(dc)
    return precinct_to_dc


def with_primary_captain_district(
    precinct_dist: pd.DataFrame, dc_grouping: pd.DataFrame
) -> pd.DataFrame:
    """
    Return a copy of precinct_dist with Primary Captain District for analytics only.
    Not written to VSPC - Precinct Distribution.csv.
    """
    m = precinct_to_dc_map(dc_grouping)
    out = precinct_dist.copy()
    out["Primary Captain District"] = (
        out["Precinct"].astype(int).astype(str).map(m).astype("Int64")
    )
    return out


def prepare_precinct_dist_for_dc(
    precinct_dist: pd.DataFrame, dc_grouping: pd.DataFrame
) -> pd.DataFrame:
    """Normalize coordinator counts, then attach Primary Captain District in memory."""
    precinct_dist = normalize_precinct_coordinators_column(precinct_dist)
    return with_primary_captain_district(precinct_dist, dc_grouping)
