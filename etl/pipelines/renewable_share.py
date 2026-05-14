import time
import pandas as pd
import sys
sys.path.insert(0, '/opt/airflow/etl')

from common.eurostat_client import fetch_dataset, COUNTRIES, COUNTRY_NAMES
from common.transformer import melt_eurostat_wide
from common.loader import upsert, log_run

PIPELINE = 'renewable_share'

# Sector code → readable label mapping
SECTOR_MAP = {
    'REN':    'total',
    'REN_ELC':'electricity',
    'REN_HCE':'heating_cooling',
    'REN_TRA':'transport',
}

def run():
    start = time.time()
    total_rows = 0
    try:
        df_raw = fetch_dataset('nrg_ind_ren')
        geo_col = [c for c in df_raw.columns if 'geo' in c.lower() or 'TIME' in c][0]
        df_raw = df_raw.rename(columns={geo_col: 'geo'})

        id_cols = [c for c in ['freq','unit','nrg_bal','geo'] if c in df_raw.columns]
        df = melt_eurostat_wide(df_raw, id_cols=id_cols, value_name='share_pct')

        df = df[df['geo'].isin(COUNTRIES)]
        df['country_code'] = df['geo']
        df['country_name'] = df['geo'].map(COUNTRY_NAMES)
        df['sector'] = df.get('nrg_bal', pd.Series(dtype=str)).map(SECTOR_MAP)
        df = df.dropna(subset=['sector'])   # drop rows with unknown sector codes

        keep = ['country_code','country_name','year','sector','share_pct','flag']
        final = df[[c for c in keep if c in df.columns]]

        result = upsert(final, 'renewable_share',
                        conflict_cols=['country_code','year','sector'])
        total_rows = result['rows_attempted']
        log_run(PIPELINE, total_rows, 0, 'success', time.time() - start)

    except Exception as e:
        log_run(PIPELINE, total_rows, 0, 'failed', time.time() - start, str(e))
        raise

if __name__ == '__main__':
    run()