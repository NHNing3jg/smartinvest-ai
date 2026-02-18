from pathlib import Path
import os

import pandas as pd
from dotenv import load_dotenv
from fredapi import Fred

RAW_DIR = Path("data/raw/fred")
SERIES = ["FEDFUNDS", "CPIAUCSL", "UNRATE", "GDP"]  # vous pouvez ajuster

def main():
    load_dotenv()
    api_key = os.getenv("FRED_API_KEY")
    print("API KEY:", api_key)
    if not api_key:
        raise ValueError("FRED_API_KEY manquante. Vérifiez votre fichier .env à la racine du projet.")

    fred = Fred(api_key=api_key)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    for s in SERIES:
        ts = fred.get_series(s)  # pandas Series index=date
        df = ts.reset_index()
        df.columns = ["date", "value"]
        df["series_id"] = s
        df = df[["series_id", "date", "value"]]

        out = RAW_DIR / f"{s}.csv"
        df.to_csv(out, index=False)
        print(f"[OK] Saved {s} -> {out}")

if __name__ == "__main__":
    main()
