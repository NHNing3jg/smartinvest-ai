-- Create DB manually in pgAdmin: smartinvest_dw
-- Then run this script inside that DB.

CREATE SCHEMA IF NOT EXISTS smartinvest;

CREATE TABLE IF NOT EXISTS smartinvest.dim_asset (
  asset_id SERIAL PRIMARY KEY,
  ticker TEXT NOT NULL UNIQUE,
  asset_type TEXT NOT NULL DEFAULT 'stock'  -- stock | index
);

CREATE TABLE IF NOT EXISTS smartinvest.dim_time (
  date_id DATE PRIMARY KEY,
  year INT,
  month INT,
  day INT,
  week INT,
  quarter INT
);

CREATE TABLE IF NOT EXISTS smartinvest.fact_market_daily (
  date_id DATE NOT NULL REFERENCES smartinvest.dim_time(date_id),
  asset_id INT NOT NULL REFERENCES smartinvest.dim_asset(asset_id),
  open NUMERIC,
  high NUMERIC,
  low NUMERIC,
  close NUMERIC,
  adj_close NUMERIC,
  volume BIGINT,
  dividends NUMERIC,
  stock_splits NUMERIC,
  PRIMARY KEY (date_id, asset_id)
);

CREATE TABLE IF NOT EXISTS smartinvest.dim_macro_series (
  series_id TEXT PRIMARY KEY,       -- e.g., FEDFUNDS, CPIAUCSL
  label TEXT
);

CREATE TABLE IF NOT EXISTS smartinvest.fact_macro_daily (
  date_id DATE NOT NULL REFERENCES smartinvest.dim_time(date_id),
  series_id TEXT NOT NULL REFERENCES smartinvest.dim_macro_series(series_id),
  value NUMERIC,
  PRIMARY KEY (date_id, series_id)
);
