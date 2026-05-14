import pandas as pd
import numpy as np
import re

# Eurostat uses ':' for missing values — not NaN, not None
MISSING_MARKERS = {':', '', 'nan', 'NaN', None}

# Eurostat data quality flags and their meanings
# Agent can use them to caveat uncertain figures
FLAG_MEANINGS = {
    'e': 'estimated',
    'p': 'provisional',       # May be revised in a future release
    'u': 'low_reliability',
    'b': 'break_in_series',   # Methodology changed — compare with caution
    'd': 'definition_differs',
    's': 'eurostat_estimate',
    'c': 'confidential',
    'n': 'not_significant',
    'z': 'not_applicable',
}

def clean_value(val) -> float | None:
    """
    Coerce a raw Eurostat cell to float.
    Returns None for missing markers so we can drop or skip them cleanly.
    """
    if val in MISSING_MARKERS:
        return None
    try:
        return float(str(val).strip().replace(',', '.'))
    except (ValueError, TypeError):
        return None

def parse_flag(val) -> str | None:
    """Extract flag character from a Eurostat flag cell."""
    if val in MISSING_MARKERS:
        return None
    s = str(val).strip()
    return s if s else None

def melt_eurostat_wide(
    df: pd.DataFrame,
    id_cols: list[str],
    value_name: str
) -> pd.DataFrame:
    """
    Eurostat DataFrames arrive in WIDE format:
        one column per time period (e.g. '2020 ', '2021 ', '2022 ')
        plus matching flag columns (e.g. '2020  flag', '2021  flag')

    This melts them into LONG format:
        (id_cols..., year, <value_name>, flag)

    This is the core transform we will call in every pipeline.
    """
    # Identify time-period columns (years) vs flag columns
    all_cols = [c for c in df.columns if c not in id_cols]
    
    
    value_suffix = '_value'
    flag_suffix = '_flag'

    value_cols = [
        c for c in all_cols
        if str(c).endswith(value_suffix)
    ]

    flag_cols = [
        c for c in all_cols
        if str(c).endswith(flag_suffix)
    ]

    flag_col_map = {
        vc: vc.replace(value_suffix, flag_suffix)
        for vc in value_cols
        if vc.replace(value_suffix, flag_suffix) in df.columns
    }

    # Melt values
    melted_val = df.melt(
        id_vars=id_cols,
        value_vars=value_cols,
        var_name='_time_raw',
        value_name='_val_raw'
    )
    melted_val['_time_key'] = (
    melted_val['_time_raw']
    .str.replace(value_suffix, '', regex=False))

    # Melt flags (only for columns that have a flag counterpart)
    if flag_col_map:
        melted_flag = df.melt(
            id_vars=id_cols,
            value_vars=list(flag_col_map.values()),
            var_name='_flag_raw',
            value_name='flag'
        )
        
        melted_flag['_time_key'] = (
        melted_flag['_flag_raw']
        .str.replace(flag_suffix, '', regex=False))

        result = melted_val.merge(
            melted_flag[id_cols + ['_time_key', 'flag']],
            on=id_cols + ['_time_key'],
            how='left')
        
    else:
        result = melted_val.copy()
        result['flag'] = None

    # Parse time period
    # Annual:     '2022 '   → year=2022, semester=None
    # Semiannual: '2022-S1 ' → year=2022, semester='S1'

    result['_time_clean'] = result['_time_key'].str.strip()

    result['year'] = pd.to_numeric(
    result['_time_clean'].str.extract(r'^(\d{4})')[0],
    errors='coerce'
)
    result['semester'] = result['_time_clean'].str.extract(r'(S\d)')[0]
    result = result.dropna(subset=['year'])
    result['year'] = result['year'].astype(int)

    # Clean value and flag
    result[value_name] = result['_val_raw'].apply(clean_value)
    result['flag'] = result['flag'].apply(parse_flag)

    # Drop rows with no value (true missing — colon marker)
    result = result.dropna(subset=[value_name])

    # Drop helper columns
    drop_cols = [
    '_time_raw',
    '_val_raw',
    '_time_clean',
    '_flag_raw',
    '_time_key'
]
    result = result.drop(columns=[c for c in drop_cols if c in result.columns])

    return result.reset_index(drop=True)