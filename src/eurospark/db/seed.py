import pandas as pd
from supabase import create_client
from eurospark.config import settings

import time

def seed_table(supabase, table: str, df: pd.DataFrame, batch_size=1000):
    df = df.astype(object).where(pd.notnull(df), None)

    records = df.to_dict(orient="records")

    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]

        success = False
        for attempt in range(3):
            try:
                supabase.schema("eurospark").table(table).insert(batch).execute()
                success = True
                break
            except Exception as e:
                print(f"Retry {attempt+1} for batch {i}: {e}")

        if success:
            print(f"{table}: Inserted {i + len(batch)} / {len(records)}")
        else:
            print(f"❌ FAILED batch starting at {i}")

if __name__ == "__main__":
    print ("Starting database seeding...")
    sb = create_client(settings.supabase_url, settings.supabase_key)
    seed_table(sb, "electricity_prices", pd.read_csv("data/electricity_prices_clean.csv"))
    seed_table(sb, "renewable_capacity", pd.read_csv("data/renewable_capacity_clean.csv"))
    seed_table(sb, "energy_consumption", pd.read_csv("data/energy_consumption_clean.csv"))
    print ("Database seeding complete!")