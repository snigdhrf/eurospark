import os
import time
import psycopg
# import psycopg.extras
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

def _get_conn():
    """
    Connects to Supabase via the direct Postgres connection string.
    Set SUPABASE_DB_URL in your environment or GitHub Secrets.
    Format: postgresql://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres
    """
    url = os.environ.get('SUPABASE_DB_URL')
    if not url:
        raise EnvironmentError("SUPABASE_DB_URL environment variable not set")
    return psycopg.connect(url)

def upsert(
    df: pd.DataFrame,
    table: str,
    conflict_cols: list[str],
    schema: str = 'eurospark'
) -> dict:
    """
    Upsert a DataFrame into a Supabase table.

    Uses ON CONFLICT DO UPDATE so:
    - New rows are inserted
    - Existing rows (matched on conflict_cols) are updated if values changed
      (e.g. a provisional figure gets revised to a final one)
    - Truly identical rows are silently ignored (no wasted writes)

    Returns a summary dict: { rows_attempted, status }
    """
    if df.empty:
        print(f"[loader] Skipping {table} — empty DataFrame")
        return {'rows_attempted': 0, 'status': 'skipped'}

    # Replace NaN/NaT with None so psycopg2 writes NULL cleanly
    df = df.where(pd.notnull(df), None)

    cols = list(df.columns)
    values = [tuple(row) for row in df.itertuples(index=False)]

    # Build the SQL
    conflict_clause = ', '.join(conflict_cols)
    update_cols = [c for c in cols if c not in conflict_cols + ['id']]
    update_clause = ', '.join(f"{c} = EXCLUDED.{c}" for c in update_cols)
    if update_cols:
        update_clause += ", updated_at = NOW()"

    try:
        with _get_conn() as conn:
            placeholders = ', '.join(['%s'] * len(cols))

            sql = f"""
                INSERT INTO {schema}.{table} ({', '.join(cols)})
                VALUES ({placeholders})
                ON CONFLICT ({conflict_clause})
                DO UPDATE SET {update_clause}
            """

            with conn.cursor() as cur:
                cur.executemany(sql, values)
            conn.commit()
        print(f"[loader] {table}: upserted {len(values)} rows")
        return {'rows_attempted': len(values), 'status': 'success'}
    except Exception as e:
        print(f"[loader] ERROR upserting {table}: {e}")
        raise

def log_run(
    pipeline_name: str,
    rows_upserted: int,
    rows_skipped: int,
    status: str,
    duration_sec: float,
    error_msg: str = None,
    schema: str = 'eurospark'
):
    """Write a record to pipeline_runs for monitoring."""
    sql = f"""
        INSERT INTO {schema}.pipeline_runs
            (pipeline_name, rows_upserted, rows_skipped, status, duration_sec, error_msg)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    try:
        with _get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (
                    pipeline_name, rows_upserted, rows_skipped,
                    status, round(duration_sec, 2), error_msg
                ))
            conn.commit()
    except Exception as e:
        print(f"[loader] WARNING: Could not write pipeline log: {e}")