from __future__ import annotations

from pathlib import Path
from datetime import datetime
import re
import pandas as pd
import yfinance as yf

RAW_DIR = Path("data/raw/yfinance")

# Tickers (actions + indices)
TICKERS = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "^GSPC", "^IXIC"]

# Période
START_DATE = "2020-01-01"
END_DATE = None  # None = jusqu'à aujourd'hui


def _safe_filename(ticker: str) -> str:
    # ex: "^GSPC" -> "GSPC"
    ticker = ticker.replace("^", "")
    return re.sub(r"[^A-Za-z0-9_\-\.]+", "_", ticker)


def _norm_col(col) -> str:
    """
    Normalise un nom de colonne yfinance.
    Gère les colonnes MultiIndex (tuples) en les convertissant en string.
    """
    if isinstance(col, tuple):
        # ex: ('Open', '') ou ('Close', 'AAPL') -> 'open' / 'close_aapl'
        parts = [str(x) for x in col if x not in ("", None)]
        col = "_".join(parts) if parts else ""
    return str(col).strip().lower().replace(" ", "_")


def fetch_ticker(ticker: str) -> pd.DataFrame:
    # group_by="column" réduit les surprises côté colonnes
    df = yf.download(
        ticker,
        start=START_DATE,
        end=END_DATE,
        auto_adjust=False,
        actions=True,          # inclut dividends/splits si dispo
        group_by="column",
        progress=False,
        threads=True,
    )

    if df is None or df.empty:
        raise ValueError(f"Aucune donnée retournée pour {ticker}")

    # Date index -> colonne
    df = df.reset_index()

    # Normaliser colonnes (robuste tuples)
    df.columns = [_norm_col(c) for c in df.columns]

    # yfinance peut renvoyer "datetime" au lieu de "date"
    if "date" not in df.columns and "datetime" in df.columns:
        df = df.rename(columns={"datetime": "date"})

    if "date" not in df.columns:
        raise ValueError(f"Colonne date introuvable pour {ticker}. Colonnes: {list(df.columns)}")

    # Assurer type datetime
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None, ambiguous="NaT", nonexistent="NaT")

    df["ticker"] = ticker

    # Colonnes principales (certaines peuvent manquer selon l'actif)
    base_cols = ["ticker", "date", "open", "high", "low", "close", "adj_close", "volume"]
    action_cols = ["dividends", "stock_splits"]  # peut exister ou non
    cols = [c for c in base_cols + action_cols if c in df.columns]

    out = df[cols].copy()

    # Tri stable
    out = out.sort_values(["ticker", "date"]).reset_index(drop=True)

    return out


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    # petit log d’exécution
    print(f"[INFO] Start yfinance ingestion | start={START_DATE} end={END_DATE or 'today'}")
    print(f"[INFO] Output dir: {RAW_DIR.resolve()}")

    for t in TICKERS:
        try:
            df = fetch_ticker(t)
            out_path = RAW_DIR / f"{_safe_filename(t)}.csv"
            df.to_csv(out_path, index=False)
            print(f"[OK] {t} -> {out_path} ({len(df)} rows)")
        except Exception as e:
            print(f"[ERR] {t} failed: {e}")

    print("[INFO] Done.")


if __name__ == "__main__":
    main()
