from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

RAW_YF = Path("data/raw/yfinance")
RAW_FRED = Path("data/raw/fred")

def get_engine():
    load_dotenv()
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    db   = os.getenv("DB_NAME", "smartinvest_dw")
    user = os.getenv("DB_USER", "postgres")
    pwd  = os.getenv("DB_PASSWORD", "")

    if not pwd:
        raise ValueError("DB_PASSWORD manquant dans .env")

    url = f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db}"
    return create_engine(url)

def upsert_dim_time(engine, dates):
    # dates = liste de date (python date)
    unique_dates = sorted(set(dates))
    if not unique_dates:
        return

    df = pd.DataFrame({"date_id": pd.to_datetime(unique_dates).date})
    dt = pd.to_datetime(df["date_id"])
    df["year"] = dt.dt.year
    df["month"] = dt.dt.month
    df["day"] = dt.dt.day
    df["week"] = dt.dt.isocalendar().week.astype(int)
    df["quarter"] = dt.dt.quarter

    with engine.begin() as con:
        for _, r in df.iterrows():
            con.execute(text("""
                INSERT INTO smartinvest.dim_time(date_id, year, month, day, week, quarter)
                VALUES (:date_id, :year, :month, :day, :week, :quarter)
                ON CONFLICT (date_id) DO NOTHING
            """), r.to_dict())

def get_or_create_asset(engine, ticker: str):
    asset_type = "index" if ticker.startswith("^") else "stock"
    with engine.begin() as con:
        con.execute(text("""
            INSERT INTO smartinvest.dim_asset(ticker, asset_type)
            VALUES (:ticker, :asset_type)
            ON CONFLICT (ticker) DO NOTHING
        """), {"ticker": ticker, "asset_type": asset_type})

        asset_id = con.execute(text("""
            SELECT asset_id FROM smartinvest.dim_asset WHERE ticker=:ticker
        """), {"ticker": ticker}).scalar()

    return asset_id

def load_market(engine):
    if not RAW_YF.exists():
        raise FileNotFoundError("data/raw/yfinance introuvable. Lancez d’abord l’ingestion yfinance.")

    for csv_path in RAW_YF.glob("*.csv"):
        df = pd.read_csv(csv_path)

        # colonnes attendues : ticker,date,open,high,low,close,(adj_close),volume,(dividends),(stock_splits)
        if "date" not in df.columns or "ticker" not in df.columns:
            raise ValueError(f"Colonnes manquantes dans {csv_path.name}")

        df["date"] = pd.to_datetime(df["date"]).dt.date
        ticker = str(df["ticker"].iloc[0])

        asset_id = get_or_create_asset(engine, ticker)
        upsert_dim_time(engine, df["date"].tolist())

        with engine.begin() as con:
            for _, r in df.iterrows():
                con.execute(text("""
                    INSERT INTO smartinvest.fact_market_daily
                    (date_id, asset_id, open, high, low, close, adj_close, volume, dividends, stock_splits)
                    VALUES (:date_id, :asset_id, :open, :high, :low, :close, :adj_close, :volume, :dividends, :stock_splits)
                    ON CONFLICT (date_id, asset_id) DO UPDATE SET
                      open=EXCLUDED.open,
                      high=EXCLUDED.high,
                      low=EXCLUDED.low,
                      close=EXCLUDED.close,
                      adj_close=EXCLUDED.adj_close,
                      volume=EXCLUDED.volume,
                      dividends=EXCLUDED.dividends,
                      stock_splits=EXCLUDED.stock_splits
                """), {
                    "date_id": r["date"],
                    "asset_id": asset_id,
                    "open": r.get("open"),
                    "high": r.get("high"),
                    "low": r.get("low"),
                    "close": r.get("close"),
                    "adj_close": r.get("adj_close"),
                    "volume": r.get("volume"),
                    "dividends": r.get("dividends"),
                    "stock_splits": r.get("stock_splits"),
                })

        print(f"[OK] Market loaded: {csv_path.name}")

def load_macro(engine):
    if not RAW_FRED.exists():
        raise FileNotFoundError("data/raw/fred introuvable. Lancez d’abord l’ingestion FRED.")

    for csv_path in RAW_FRED.glob("*.csv"):
        df = pd.read_csv(csv_path)

        # colonnes attendues : series_id,date,value
        if not {"series_id", "date", "value"}.issubset(df.columns):
            raise ValueError(f"Colonnes manquantes dans {csv_path.name}")

        df["date"] = pd.to_datetime(df["date"]).dt.date
        series_id = str(df["series_id"].iloc[0])

        upsert_dim_time(engine, df["date"].tolist())

        with engine.begin() as con:
            con.execute(text("""
                INSERT INTO smartinvest.dim_macro_series(series_id, label)
                VALUES (:series_id, :label)
                ON CONFLICT (series_id) DO NOTHING
            """), {"series_id": series_id, "label": series_id})

            for _, r in df.iterrows():
                con.execute(text("""
                    INSERT INTO smartinvest.fact_macro_daily(date_id, series_id, value)
                    VALUES (:date_id, :series_id, :value)
                    ON CONFLICT (date_id, series_id) DO UPDATE SET
                      value=EXCLUDED.value
                """), {"date_id": r["date"], "series_id": series_id, "value": r["value"]})

        print(f"[OK] Macro loaded: {csv_path.name}")

def main():
    engine = get_engine()

    # Test connexion rapide
    with engine.connect() as con:
        con.execute(text("SELECT 1"))

    load_market(engine)
    load_macro(engine)
    print("[INFO] Load complete ✅")

if __name__ == "__main__":
    main()