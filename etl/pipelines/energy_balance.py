import time
import pandas as pd
import sys
sys.path.insert(0, '/opt/airflow/etl')

from common.eurostat_client import fetch_dataset, COUNTRIES, COUNTRY_NAMES
from common.transformer import melt_eurostat_wide
from common.loader import upsert, log_run

PIPELINE = 'energy_balance'

FLOW_MAP = {
    'PPRD':   'production',
    'IMP':    'imports',
    'EXP':    'exports',
    'INGR':   'gross_inland_consumption',
    'FC':     'final_consumption',
    'TI':     'transformation_input',
    'TO':     'transformation_output',
}

PRODUCT_MAP = {
    'TOTAL':  'total',
    'O4000':  'oil',
    'G3000':  'natural_gas',
    'C0000':  'solid_fuels',
    'N9000':  'nuclear',
    'RA000':  'renewables',
    'E7000':  'electricity',
    'H8000':  'heat',
}

def run():
    start = time.time()
    total_rows = 0
    try:
        df_raw = fetch_dataset('nrg_bal_s')
        geo_col = [c for c in df_raw.columns if 'geo' in c.lower() or 'TIME' in c][0]
        df_raw = df_raw.rename(columns={geo_col: 'geo'})

        id_cols = [c for c in ['freq','unit','siec','nrg_bal','geo'] if c in df_raw.columns]
        df = melt_eurostat_wide(df_raw, id_cols=id_cols, value_name='value_ktoe')

        df = df[df['geo'].isin(COUNTRIES)]
        if 'unit' in df.columns:
            df = df[df['unit'] == 'KTOE']

        df['country_code'] = df['geo']
        df['country_name'] = df['geo'].map(COUNTRY_NAMES)
        df['flow']    = df.get('nrg_bal', pd.Series(dtype=str)).map(FLOW_MAP)
        df['product'] = df.get('siec', pd.Series(dtype=str)).map(PRODUCT_MAP)
        df = df.dropna(subset=['flow', 'product'])

        keep = ['country_code','country_name','year','flow','product','value_ktoe','flag']
        final = df[[c for c in keep if c in df.columns]]

        result = upsert(final, 'energy_balance',
                        conflict_cols=['country_code','year','flow','product'])
        total_rows = result['rows_attempted']
        log_run(PIPELINE, total_rows, 0, 'success', time.time() - start)

    except Exception as e:
        log_run(PIPELINE, total_rows, 0, 'failed', time.time() - start, str(e))
        raise

if __name__ == '__main__':
    run()