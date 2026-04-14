CREATE SCHEMA eurospark;

CREATE TABLE eurospark.electricity_prices (
  id SERIAL PRIMARY KEY,
  country_code TEXT NOT NULL,
  country_name TEXT NOT NULL,
  year INT NOT NULL,
  quarter TEXT,
  consumer_type TEXT NOT NULL,  -- 'household' or 'industrial'
  price_eur_kwh NUMERIC(8,5) NOT NULL,
  currency TEXT DEFAULT 'EUR'
);

CREATE TABLE eurospark.renewable_capacity (
  id SERIAL PRIMARY KEY,
  country_code TEXT NOT NULL,
  country_name TEXT NOT NULL,
  year INT NOT NULL,
  source TEXT NOT NULL,    -- 'wind', 'solar', 'hydro', 'total_renewable'
  capacity_gw NUMERIC(10,3),
  share_pct NUMERIC(5,2)
);

CREATE TABLE eurospark.energy_consumption (
  id SERIAL PRIMARY KEY,
  country_code TEXT NOT NULL,
  country_name TEXT NOT NULL,
  year INT NOT NULL,
  sector TEXT NOT NULL,    -- 'industry', 'transport', 'households', 'services'
  consumption_mtoe NUMERIC(10,3)
);

GRANT USAGE ON SCHEMA eurospark TO anon, authenticated, service_role;

GRANT ALL ON ALL TABLES IN SCHEMA eurospark TO anon, authenticated, service_role;

GRANT ALL ON ALL SEQUENCES IN SCHEMA eurospark TO anon, authenticated, service_role;

CREATE OR REPLACE FUNCTION public.execute_readonly_sql(query TEXT)
RETURNS json AS $$
DECLARE result json;
BEGIN
  -- Only allow SELECT queries
  IF query !~* '^SELECT' THEN
    RAISE EXCEPTION 'Only SELECT queries are allowed';
  END IF;

  -- Force schema + wrap results as JSON array
  EXECUTE format(
    'SET LOCAL search_path TO eurospark;
     SELECT json_agg(t) FROM (%s) t LIMIT 1000',
    query
  ) INTO result;

  RETURN COALESCE(result, '[]'::json);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- NOTIFY pgrst, 'reload schema';

CREATE OR REPLACE FUNCTION public.get_eurospark_schema()
RETURNS json AS $$
BEGIN
  RETURN (
    SELECT json_agg(
      json_build_object(
        'table', table_name,
        'columns', (
          SELECT json_agg(column_name)
          FROM information_schema.columns
          WHERE table_name = t.table_name
        )
      )
    )
    FROM information_schema.tables t
    WHERE table_schema = 'eurospark'
  );
END;
$$ LANGUAGE plpgsql;