from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd

from train_direction_model import (
    get_engine,
    build_dataset,
)

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = Path("models/direction_model_xgb.pkl")
FEATURES_PATH = Path("models/direction_model_features.pkl")
THRESHOLD_PATH = Path("models/direction_model_threshold.pkl")


def confidence_label(proba_up: float) -> str:
    """
    Donne un niveau de confiance lisible.
    """
    distance = abs(proba_up - 0.5)

    if distance >= 0.25:
        return "High"
    if distance >= 0.12:
        return "Medium"
    return "Low"


def generate_signal(proba_up: float, threshold: float, row: pd.Series) -> str:
    """
    Transforme la probabilité en recommandation BUY / HOLD / SELL.

    Logique :
    - BUY si la probabilité de hausse est forte et le momentum est positif
    - SELL si la probabilité de hausse est faible et le momentum est négatif
    - sinon HOLD
    """

    buy_threshold = max(0.60, threshold)
    sell_threshold = min(0.40, 1 - threshold)

    momentum_5 = row.get("momentum_5", 0)
    rolling_vol_10 = row.get("rolling_vol_10", 0)

    # vous pouvez ajuster ce seuil plus tard selon vos résultats
    low_volatility = rolling_vol_10 < 0.03 if pd.notna(rolling_vol_10) else False

    if proba_up >= buy_threshold and momentum_5 > 0:
        if low_volatility:
            return "BUY"
        return "BUY"

    if proba_up <= sell_threshold and momentum_5 < 0:
        return "SELL"

    return "HOLD"


def generate_recommendations():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")

    if not FEATURES_PATH.exists():
        raise FileNotFoundError(f"Features file not found: {FEATURES_PATH}")

    if not THRESHOLD_PATH.exists():
        raise FileNotFoundError(f"Threshold file not found: {THRESHOLD_PATH}")

    model = joblib.load(MODEL_PATH)
    feature_cols = joblib.load(FEATURES_PATH)
    threshold = joblib.load(THRESHOLD_PATH)

    engine = get_engine()

    # on reconstruit le dataset complet avec les mêmes features
    df, X, y, _ = build_dataset(engine)

    # garder seulement la dernière ligne de chaque actif
    asset_cols = [c for c in df.columns if c.startswith("asset_")]

    latest_rows = (
        df.sort_values("date_id")
        .groupby(asset_cols, dropna=False, as_index=False)
        .tail(1)
        .copy()
    )

    X_latest = latest_rows[feature_cols].copy()

    proba_up = model.predict_proba(X_latest)[:, 1]
    pred_class = (proba_up >= threshold).astype(int)

    latest_rows["proba_up"] = proba_up
    latest_rows["predicted_direction"] = pred_class

    # retrouver le nom de l’actif
    def get_asset_name(row):
        for col in asset_cols:
            if row.get(col, 0) == 1:
                return col.replace("asset_", "")
        return "UNKNOWN"

    latest_rows["asset_name"] = latest_rows.apply(get_asset_name, axis=1)

    latest_rows["signal"] = latest_rows.apply(
        lambda row: generate_signal(row["proba_up"], threshold, row),
        axis=1
    )

    latest_rows["confidence"] = latest_rows["proba_up"].apply(confidence_label)

    result = latest_rows[
        [
            "date_id",
            "asset_name",
            "proba_up",
            "predicted_direction",
            "signal",
            "confidence",
            "momentum_5",
            "momentum_10",
            "rolling_vol_10",
            "oil_return",
            "sp500_return",
            "nasdaq_return",
        ]
    ].copy()

    result = result.rename(columns={"asset_name": "ticker"})
    result["proba_up"] = result["proba_up"].round(4)
    result["predicted_direction"] = result["predicted_direction"].map({1: "UP", 0: "DOWN"})
    result = result.sort_values(["signal", "proba_up"], ascending=[True, False]).reset_index(drop=True)

    output_path = OUTPUT_DIR / "latest_recommendations.csv"
    result.to_csv(output_path, index=False)

    print("\n=== AI RECOMMENDATIONS ===")
    print(result)

    print(f"\n[OK] Recommendations saved to: {output_path}")


if __name__ == "__main__":
    generate_recommendations()