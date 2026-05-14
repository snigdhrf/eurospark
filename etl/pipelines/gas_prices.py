import time
import pandas as pd
import sys
sys.path.insert(0, '/opt/airflow/etl')

from common.eurostat_client import fetch_dataset, COUNTRIES, COUNTRY_NAMES
from common.transformer import melt_eurostat_wide
from common.loader import upsert, log_run

PIPELINE = 'gas_prices'
DATASETS = {
    'household': 'nrg_pc_202',
    'industry':  'nrg_pc_203',
}

def run():
    start = time.time()
    total_rows = 0
    try:
        frames = []
        for consumer_type, code in DATASETS.items():
            df_raw = fetch_dataset(code)
            geo_col = [c for c in df_raw.columns if 'geo' in c.lower() or 'TIME' in c][0]
            df_raw = df_raw.rename(columns={geo_col: 'geo'})

            id_cols = [c for c in ['freq','unit','tax','currency','nrg_cons','geo']
                       if c in df_raw.columns]
            df = melt_eurostat_wide(df_raw, id_cols=id_cols, value_name='price_eur_gj')

            df = df[df['geo'].isin(COUNTRIES)]
            df['consumer_type'] = consumer_type
            df['country_code']  = df['geo']
            df['country_name']  = df['geo'].map(COUNTRY_NAMES)
            df['tax_included']  = df.get('tax', pd.Series(dtype=str)).apply(
                lambda x: True if str(x).upper() in ('I_TAX', 'TAX') else False
            )
            df['price_band'] = df.get('nrg_cons', pd.Series(dtype=str))

            keep = ['country_code','country_name','year','semester',
                    'consumer_type','price_band','price_eur_gj','tax_included','flag']
            frames.append(df[[c for c in keep if c in df.columns]])

        final = pd.concat(frames, ignore_index=True)
        result = upsert(final, 'gas_prices',
            conflict_cols=['country_code','year','semester',
                           'consumer_type','price_band','tax_included'])
        total_rows = result['rows_attempted']
        log_run(PIPELINE, total_rows, 0, 'success', time.time() - start)

    except Exception as e:
        log_run(PIPELINE, total_rows, 0, 'failed', time.time() - start, str(e))
        raise

if __name__ == '__main__':
    run()