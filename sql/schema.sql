-- ============================================================
-- EuroSpark Energy Schema
-- Run once in Supabase SQL editor
-- ============================================================

CREATE SCHEMA IF NOT EXISTS eurospark;

-- 1. Electricity prices (households + industry)
CREATE TABLE IF NOT EXISTS eurospark.electricity_prices (
    id              BIGSERIAL PRIMARY KEY,
    country_code    VARCHAR(10)  NOT NULL,
    country_name    VARCHAR(100),
    year            INTEGER      NOT NULL,
    semester        VARCHAR(5),               -- 'S1' or 'S2'
    consumer_type   VARCHAR(20)  NOT NULL,    -- 'household' | 'industry'
    price_band      VARCHAR(30),              -- e.g. 'KWH2500-4999'
    price_eur_kwh   NUMERIC(10,6),
    tax_included    BOOLEAN,
    flag            VARCHAR(5),               -- Eurostat data quality flag
    updated_at      TIMESTAMPTZ  DEFAULT NOW(),
    UNIQUE (country_code, year, semester, consumer_type, price_band, tax_included)
);

-- 2. Gas prices (households + industry)
CREATE TABLE IF NOT EXISTS eurospark.gas_prices (
    id              BIGSERIAL PRIMARY KEY,
    country_code    VARCHAR(10)  NOT NULL,
    country_name    VARCHAR(100),
    year            INTEGER      NOT NULL,
    semester        VARCHAR(5),
    consumer_type   VARCHAR(20)  NOT NULL,
    price_band      VARCHAR(30),
    price_eur_gj    NUMERIC(10,6),
    tax_included    BOOLEAN,
    flag            VARCHAR(5),
    updated_at      TIMESTAMPTZ  DEFAULT NOW(),
    UNIQUE (country_code, year, semester, consumer_type, price_band, tax_included)
);

-- 3. Renewable energy share (% of total consumption)
CREATE TABLE IF NOT EXISTS eurospark.renewable_share (
    id              BIGSERIAL PRIMARY KEY,
    country_code    VARCHAR(10)  NOT NULL,
    country_name    VARCHAR(100),
    year            INTEGER      NOT NULL,
    sector          VARCHAR(50),  -- 'total' | 'electricity' | 'heating_cooling' | 'transport'
    share_pct       NUMERIC(6,2),
    flag            VARCHAR(5),
    updated_at      TIMESTAMPTZ  DEFAULT NOW(),
    UNIQUE (country_code, year, sector)
);

-- 4. Renewable energy generation by source (absolute)
CREATE TABLE IF NOT EXISTS eurospark.renewable_generation (
    id              BIGSERIAL PRIMARY KEY,
    country_code    VARCHAR(10)  NOT NULL,
    country_name    VARCHAR(100),
    year            INTEGER      NOT NULL,
    source          VARCHAR(50),  -- 'wind', 'solar', 'hydro', 'biomass', etc.
    value_ktoe      NUMERIC(12,3),
    flag            VARCHAR(5),
    updated_at      TIMESTAMPTZ  DEFAULT NOW(),
    UNIQUE (country_code, year, source)
);

-- 5. Electricity generation mix
CREATE TABLE IF NOT EXISTS eurospark.electricity_generation_mix (
    id              BIGSERIAL PRIMARY KEY,
    country_code    VARCHAR(10)  NOT NULL,
    country_name    VARCHAR(100),
    year            INTEGER      NOT NULL,
    source          VARCHAR(50),  -- 'nuclear', 'coal', 'gas', 'wind', 'solar', 'hydro', etc.
    value_gwh       NUMERIC(15,3),
    flag            VARCHAR(5),
    updated_at      TIMESTAMPTZ  DEFAULT NOW(),
    UNIQUE (country_code, year, source)
);

-- 6. Energy import dependency
CREATE TABLE IF NOT EXISTS eurospark.energy_import_dependency (
    id              BIGSERIAL PRIMARY KEY,
    country_code    VARCHAR(10)  NOT NULL,
    country_name    VARCHAR(100),
    year            INTEGER      NOT NULL,
    fuel_type       VARCHAR(50),  -- 'total' | 'oil' | 'gas' | 'solid_fuels'
    dependency_pct  NUMERIC(8,2),
    flag            VARCHAR(5),
    updated_at      TIMESTAMPTZ  DEFAULT NOW(),
    UNIQUE (country_code, year, fuel_type)
);

-- 7. Simplified energy balance
CREATE TABLE IF NOT EXISTS eurospark.energy_balance (
    id              BIGSERIAL PRIMARY KEY,
    country_code    VARCHAR(10)  NOT NULL,
    country_name    VARCHAR(100),
    year            INTEGER      NOT NULL,
    flow            VARCHAR(60),  -- 'production' | 'imports' | 'exports' | 'gross_consumption'
    product         VARCHAR(60),  -- 'total' | 'oil' | 'gas' | 'nuclear' | 'renewables'
    value_ktoe      NUMERIC(15,3),
    flag            VARCHAR(5),
    updated_at      TIMESTAMPTZ  DEFAULT NOW(),
    UNIQUE (country_code, year, flow, product)
);

-- 8. Energy intensity (energy per unit of GDP)
CREATE TABLE IF NOT EXISTS eurospark.energy_intensity (
    id                    BIGSERIAL PRIMARY KEY,
    country_code          VARCHAR(10)  NOT NULL,
    country_name          VARCHAR(100),
    year                  INTEGER      NOT NULL,
    value_kgoe_per_keur   NUMERIC(10,4),
    flag                  VARCHAR(5),
    updated_at            TIMESTAMPTZ  DEFAULT NOW(),
    UNIQUE (country_code, year)
);

-- 9. Pipeline run log — tracks every ETL run for debugging + monitoring
CREATE TABLE IF NOT EXISTS eurospark.pipeline_runs (
    id              BIGSERIAL PRIMARY KEY,
    pipeline_name   VARCHAR(80)  NOT NULL,
    run_at          TIMESTAMPTZ  DEFAULT NOW(),
    rows_upserted   INTEGER,
    rows_skipped    INTEGER,
    status          VARCHAR(20),   -- 'success' | 'failed' | 'partial'
    error_msg       TEXT,
    duration_sec    NUMERIC(8,2)
);

-- Indexes for query performance
CREATE INDEX IF NOT EXISTS idx_elec_prices_country_year   ON eurospark.electricity_prices(country_code, year);
CREATE INDEX IF NOT EXISTS idx_gas_prices_country_year    ON eurospark.gas_prices(country_code, year);
CREATE INDEX IF NOT EXISTS idx_ren_share_country_year     ON eurospark.renewable_share(country_code, year);
CREATE INDEX IF NOT EXISTS idx_elec_mix_country_year      ON eurospark.electricity_generation_mix(country_code, year);
CREATE INDEX IF NOT EXISTS idx_import_dep_country_year    ON eurospark.energy_import_dependency(country_code, year);
CREATE INDEX IF NOT EXISTS idx_energy_balance_country_year ON eurospark.energy_balance(country_code, year);