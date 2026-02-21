-- =========================
-- SmartInvest KPI Views
-- =========================

CREATE SCHEMA IF NOT EXISTS smartinvest;

-- 1) Vue prix + jointures dim (pratique Power BI)
CREATE OR REPLACE VIEW smartinvest.v_market_daily AS
SELECT
  f.date_id,
  a.ticker,
  a.asset_type,
  f.open, f.high, f.low, f.close, f.adj_close, f.volume
FROM smartinvest.fact_market_daily f
JOIN smartinvest.dim_asset a ON a.asset_id = f.asset_id;

-- 2) Vue returns (rendement journalier) par ticker
-- return = (close / close_prev) - 1
CREATE OR REPLACE VIEW smartinvest.v_market_returns_daily AS
WITH x AS (
  SELECT
    f.date_id,
    a.ticker,
    f.close,
    LAG(f.close) OVER (PARTITION BY a.ticker ORDER BY f.date_id) AS close_prev
  FROM smartinvest.fact_market_daily f
  JOIN smartinvest.dim_asset a ON a.asset_id = f.asset_id
)
SELECT
  date_id,
  ticker,
  close,
  close_prev,
  CASE
    WHEN close_prev IS NULL OR close_prev = 0 THEN NULL
    ELSE (close / close_prev) - 1
  END AS daily_return
FROM x;

-- 3) KPI basique : rendement cumulé (depuis le début) par ticker
CREATE OR REPLACE VIEW smartinvest.v_market_cum_return AS
WITH r AS (
  SELECT * FROM smartinvest.v_market_returns_daily
),
base AS (
  SELECT
    ticker,
    MIN(date_id) AS start_date
  FROM r
  GROUP BY ticker
),
start_close AS (
  SELECT
    b.ticker,
    b.start_date,
    r.close AS start_close
  FROM base b
  JOIN r ON r.ticker = b.ticker AND r.date_id = b.start_date
),
latest AS (
  SELECT
    ticker,
    MAX(date_id) AS last_date
  FROM r
  GROUP BY ticker
),
last_close AS (
  SELECT
    l.ticker,
    l.last_date,
    r.close AS last_close
  FROM latest l
  JOIN r ON r.ticker = l.ticker AND r.date_id = l.last_date
)
SELECT
  s.ticker,
  s.start_date,
  l.last_date,
  s.start_close,
  l.last_close,
  CASE
    WHEN s.start_close IS NULL OR s.start_close = 0 THEN NULL
    ELSE (l.last_close / s.start_close) - 1
  END AS cum_return
FROM start_close s
JOIN last_close l ON l.ticker = s.ticker;

-- 4) Macro “plate” (pratique BI)
CREATE OR REPLACE VIEW smartinvest.v_macro_daily AS
SELECT
  f.date_id,
  f.series_id,
  s.label,
  f.value
FROM smartinvest.fact_macro_daily f
JOIN smartinvest.dim_macro_series s ON s.series_id = f.series_id;