import time
import pandas as pd
import sys
sys.path.insert(0, '/opt/airflow/etl')

from common.eurostat_client import fetch_dataset, COUNTRIES, COUNTRY_NAMES
from common.transformer import melt_eurostat_wide
from common.loader import upsert, log_run

PIPELINE = 'import_dependency'

FUEL_MAP = {
    'TOTAL':  'total',
    'O4000':  'oil',
    'G3000':  'natural_gas',
    'C0000':  'solid_fuels',
}

def run():
    start = time.time()
    total_rows = 0
    try:
        df_raw = fetch_dataset('nrg_ind_id')
        geo_col = [c for c in df_raw.columns if 'geo' in c.lower() or 'TIME' in c][0]
        df_raw = df_raw.rename(columns={geo_col: 'geo'})

        id_cols = [c for c in ['freq','unit','siec','geo'] if c in df_raw.columns]
        df = melt_eurostat_wide(df_raw, id_cols=id_cols, value_name='dependency_pct')

        df = df[df['geo'].isin(COUNTRIES)]
        df['country_code'] = df['geo']
        df['country_name'] = df['geo'].map(COUNTRY_NAMES)
        df['fuel_type'] = df.get('siec', pd.Series(dtype=str)).map(FUEL_MAP)
        df = df.dropna(subset=['fuel_type'])

        keep = ['country_code','country_name','year','fuel_type','dependency_pct','flag']
        final = df[[c for c in keep if c in df.columns]]

        result = upsert(final, 'energy_import_dependency',
                        conflict_cols=['country_code','year','fuel_type'])
        total_rows = result['rows_attempted']
        log_run(PIPELINE, total_rows, 0, 'success', time.time() - start)

    except Exception as e:
        log_run(PIPELINE, total_rows, 0, 'failed', time.time() - start, str(e))
        raise

if __name__ == '__main__':
    run()