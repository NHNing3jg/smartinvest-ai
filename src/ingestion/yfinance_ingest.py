from __future__ import annotations

from pathlib import Path
import re
import pandas as pd
import yfinance as yf

RAW_DIR = Path("data/raw/yfinance")

# Tickers (actions + indices)
TICKERS = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "^GSPC", "^IXIC"]

# Période
START_DATE = "2020-01-01"
END_DATE = None  # None = jusqu'à aujourd'hui


def _safe_ticker(ticker: str) -> str:
    """Ex: '^GSPC' -> 'GSPC' (utile pour noms de fichiers et matching)."""
    return ticker.replace("^", "")


def _safe_filename(ticker: str) -> str:
    t = _safe_ticker(ticker)
    return re.sub(r"[^A-Za-z0-9_\-\.]+", "_", t)


def _norm_col(col) -> str:
    """
    Normalise un nom de colonne yfinance.
    - gère MultiIndex (tuple) -> 'open_aapl'
    - lower + spaces -> underscore
    """
    if isinstance(col, tuple):
        parts = [str(x) for x in col if x not in ("", None)]
        col = "_".join(parts) if parts else ""
    return str(col).strip().lower().replace(" ", "_")


def _clean_suffix(s: str) -> str:
    # enlève ^ et tout caractère non alphanum, ex "^IXIC" -> "ixic"
    return re.sub(r"[^a-z0-9]+", "", s.lower())

def _fix_suffixed_ohlcv_columns(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    base = _clean_suffix(_safe_ticker(ticker))

    pattern = re.compile(r"^(open|high|low|close|adj_close|volume|dividends|stock_splits)_(.+)$")
    rename_map = {}

    for c in df.columns:
        m = pattern.match(c)
        if not m:
            continue
        base_name, suffix = m.group(1), m.group(2)
        if _clean_suffix(suffix) == base:
            rename_map[c] = base_name

    if rename_map:
        df = df.rename(columns=rename_map)
    return df


def fetch_ticker(ticker: str) -> pd.DataFrame:
    df = yf.download(
        ticker,
        start=START_DATE,
        end=END_DATE,
        auto_adjust=False,
        actions=True,          # dividends / splits si dispo
        group_by="column",     # limite surprises
        progress=False,
        threads=True,
    )

    if df is None or df.empty:
        raise ValueError(f"Aucune donnée retournée pour {ticker}")

    df = df.reset_index()

    # normaliser colonnes
    df.columns = [_norm_col(c) for c in df.columns]

    # yfinance peut renvoyer datetime au lieu de date
    if "date" not in df.columns and "datetime" in df.columns:
        df = df.rename(columns={"datetime": "date"})

    if "date" not in df.columns:
        raise ValueError(f"Colonne date introuvable pour {ticker}. Colonnes: {list(df.columns)}")

    # si colonnes suffixées (open_aapl...), les corriger
    df = _fix_suffixed_ohlcv_columns(df, ticker)

    # date propre (sans timezone)
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)

    df["ticker"] = ticker

    # Colonnes attendues
    wanted = [
        "ticker", "date",
        "open", "high", "low", "close", "adj_close", "volume",
        "dividends", "stock_splits",
    ]

    existing = [c for c in wanted if c in df.columns]
    out = df[existing].copy()

    # tri stable
    out = out.sort_values(["ticker", "date"]).reset_index(drop=True)

    # petit guardrail: si on n'a que ticker/date, on le signale clairement
    if set(out.columns) <= {"ticker", "date"}:
        raise ValueError(
            f"[{ticker}] CSV ne contiendra que ticker/date. Colonnes disponibles: {list(df.columns)} "
            f"(yfinance a probablement renvoyé des colonnes non mappées)."
        )

    return out


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Start yfinance ingestion | start={START_DATE} end={END_DATE or 'today'}")
    print(f"[INFO] Output dir: {RAW_DIR.resolve()}")

    for t in TICKERS:
        try:
            df = fetch_ticker(t)
            out_path = RAW_DIR / f"{_safe_filename(t)}.csv"
            df.to_csv(out_path, index=False)

            print(f"[OK] {t} -> {out_path} ({len(df)} rows) | cols={list(df.columns)}")
        except Exception as e:
            print(f"[ERR] {t} failed: {e}")

    print("[INFO] Done.")


if __name__ == "__main__":
    main()