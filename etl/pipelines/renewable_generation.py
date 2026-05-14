import time
import pandas as pd
import sys
sys.path.insert(0, '/opt/airflow/etl')

from common.eurostat_client import fetch_dataset, COUNTRIES, COUNTRY_NAMES
from common.transformer import melt_eurostat_wide
from common.loader import upsert, log_run

PIPELINE = 'renewable_generation'

SOURCE_MAP = {
    'RA000': 'total_renewables',
    'RA100': 'hydro',
    'RA110': 'hydro_pure',
    'RA120': 'pumped_hydro',
    'RA200': 'geothermal',
    'RA300': 'wind',
    'RA310': 'wind_onshore',
    'RA320': 'wind_offshore',
    'RA400': 'solar',
    'RA410': 'solar_pv',
    'RA420': 'solar_thermal',
    'RA500': 'ocean',
    'RA600': 'solid_biofuels',
    'RA700': 'biogas',
    'RA800': 'liquid_biofuels',
}

def run():
    start = time.time()
    total_rows = 0
    try:
        df_raw = fetch_dataset('nrg_t_renew')
        geo_col = [c for c in df_raw.columns if 'geo' in c.lower() or 'TIME' in c][0]
        df_raw = df_raw.rename(columns={geo_col: 'geo'})

        id_cols = [c for c in ['freq','unit','siec','geo'] if c in df_raw.columns]
        df = melt_eurostat_wide(df_raw, id_cols=id_cols, value_name='value_ktoe')

        df = df[df['geo'].isin(COUNTRIES)]
        # Keep only KTOE unit for consistency
        if 'unit' in df.columns:
            df = df[df['unit'] == 'KTOE']

        df['country_code'] = df['geo']
        df['country_name'] = df['geo'].map(COUNTRY_NAMES)
        df['source'] = df.get('siec', pd.Series(dtype=str)).map(SOURCE_MAP)
        df = df.dropna(subset=['source'])

        keep = ['country_code','country_name','year','source','value_ktoe','flag']
        final = df[[c for c in keep if c in df.columns]]

        result = upsert(final, 'renewable_generation',
                        conflict_cols=['country_code','year','source'])
        total_rows = result['rows_attempted']
        log_run(PIPELINE, total_rows, 0, 'success', time.time() - start)

    except Exception as e:
        log_run(PIPELINE, total_rows, 0, 'failed', time.time() - start, str(e))
        raise

if __name__ == '__main__':
    run()