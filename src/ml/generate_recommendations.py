from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd

from src.ml.train_direction_model import get_engine, build_dataset

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = Path("models/direction_model_xgb.pkl")
FEATURES_PATH = Path("models/direction_model_features.pkl")
THRESHOLD_PATH = Path("models/direction_model_threshold.pkl")


def get_confidence(prob: float) -> str:
    """
    Niveau de confiance basé sur la distance à 0.5.
    """
    distance = abs(prob - 0.5)

    if distance >= 0.20:
        return "High"
    elif distance >= 0.10:
        return "Medium"
    return "Low"


def get_asset_name(row: pd.Series, asset_cols: list[str]) -> str:
    """
    Retrouve le nom de l'actif à partir des colonnes one-hot asset_*.
    """
    for col in asset_cols:
        if row.get(col, 0) == 1:
            return col.replace("asset_", "")
    return "UNKNOWN"


def compute_advisor_score(row: pd.Series) -> float:
    """
    Score composite pour classer les actifs.
    Plus le score est élevé, plus l'actif est attractif.
    """
    proba_component = row.get("proba_up", 0) * 0.55
    momentum_5_component = row.get("momentum_5", 0) * 0.20
    momentum_10_component = row.get("momentum_10", 0) * 0.15
    market_component = row.get("market_trend", 0) * 0.10
    volatility_penalty = row.get("rolling_vol_10", 0) * 0.15

    score = (
        proba_component
        + momentum_5_component
        + momentum_10_component
        + market_component
        - volatility_penalty
    )
    return round(score, 6)


def assign_signals_by_ranking(df: pd.DataFrame) -> pd.DataFrame:
    """
    Attribue les signaux de manière relative :
    - top 2 = BUY
    - milieu = HOLD
    - bottom 2 = SELL

    Si les scores sont trop proches :
    - 1 BUY
    - 3 HOLD
    - 1 SELL
    """
    df = df.sort_values("advisor_score", ascending=False).reset_index(drop=True).copy()

    n = len(df)
    if n == 0:
        return df

    df["signal"] = "HOLD"

    spread = df["advisor_score"].max() - df["advisor_score"].min()

    if n >= 5:
        if spread < 0.03:
            df.loc[df.index[0], "signal"] = "BUY"
            df.loc[df.index[-1], "signal"] = "SELL"
        else:
            df.loc[df.index[:2], "signal"] = "BUY"
            df.loc[df.index[-2:], "signal"] = "SELL"
    elif n == 4:
        df.loc[df.index[0], "signal"] = "BUY"
        df.loc[df.index[-1], "signal"] = "SELL"
    elif n == 3:
        df.loc[df.index[0], "signal"] = "BUY"
        df.loc[df.index[-1], "signal"] = "SELL"
    elif n == 2:
        if spread >= 0.03:
            df.loc[df.index[0], "signal"] = "BUY"
            df.loc[df.index[1], "signal"] = "SELL"

    return df


def build_explanation(row: pd.Series) -> str:
    """
    Génère une explication personnalisée selon la situation spécifique de l'actif.
    """
    signal = row["signal"]
    prob = row.get("proba_up", 0)
    momentum_5 = row.get("momentum_5", 0)
    momentum_10 = row.get("momentum_10", 0)
    vol_10 = row.get("rolling_vol_10", 0)
    score = row.get("advisor_score", 0)
    market_trend = row.get("market_trend", 0)
    oil_return = row.get("oil_return", 0)

    reasons: list[str] = []

    if signal == "BUY":
        if prob >= 0.90:
            reasons.append("the model predicts a very strong upside probability")
        elif prob >= 0.75:
            reasons.append("the model predicts a strong upside probability")
        elif prob >= 0.60:
            reasons.append("the probability of upward movement is favorable")
        else:
            reasons.append("the asset remains among the strongest bullish candidates in the ranking")

        if momentum_5 > 0.05:
            reasons.append("short-term momentum is very strong")
        elif momentum_5 > 0:
            reasons.append("short-term momentum is positive")

        if momentum_10 > 0.03:
            reasons.append("medium-term momentum confirms the upward trend")
        elif momentum_10 > 0:
            reasons.append("medium-term trend remains supportive")

        if vol_10 < 0.02:
            reasons.append("volatility remains relatively controlled")
        elif vol_10 > 0.04:
            reasons.append("despite higher volatility, the overall ranking remains favorable")

        if market_trend > 0.01:
            reasons.append("the broader market trend is supportive")
        elif market_trend > 0:
            reasons.append("the market environment is mildly positive")

        if oil_return > 0.02:
            reasons.append("energy market dynamics may reinforce the current trend")
        elif oil_return < -0.02:
            reasons.append("the asset remains resilient despite weaker energy market movement")

        if score > 0.45:
            reasons.append("its advisor score places it among the best opportunities")

        return "BUY because " + ", ".join(reasons) + "."

    if signal == "HOLD":
        if 0.45 <= prob <= 0.60:
            reasons.append("the model conviction is moderate")
        elif prob > 0.60:
            reasons.append("the upside probability is positive but not strong enough for a buy recommendation")
        else:
            reasons.append("the downside signal is not strong enough for a sell recommendation")

        if momentum_5 > 0 and momentum_10 < 0:
            reasons.append("short-term and medium-term momentum are conflicting")
        elif momentum_5 < 0 and momentum_10 > 0:
            reasons.append("trend signals are mixed across time horizons")
        elif abs(momentum_5) < 0.01 and abs(momentum_10) < 0.01:
            reasons.append("momentum remains relatively neutral")
        elif momentum_5 > 0 and momentum_10 > 0:
            reasons.append("momentum is improving, but not enough to dominate the ranking")
        elif momentum_5 < 0 and momentum_10 < 0:
            reasons.append("weak momentum is visible, but not severe enough for an immediate sell signal")

        if 0.02 <= vol_10 <= 0.04:
            reasons.append("volatility suggests caution")
        elif vol_10 > 0.04:
            reasons.append("higher volatility reduces confidence in the signal")

        if abs(score) < 0.03:
            reasons.append("the advisor score is close to the middle of the ranking")
        elif score > 0:
            reasons.append("the asset has a balanced risk/reward profile")
        else:
            reasons.append("the asset remains neither clearly attractive nor clearly weak")

        return "HOLD because " + ", ".join(reasons) + "."

    # SELL
    if prob < 0.35:
        reasons.append("the model indicates weak upside potential")
    elif prob < 0.45:
        reasons.append("the probability of price increase is lower than for the other assets")
    else:
        reasons.append("the asset is weakly ranked despite a non-extreme model probability")

    if momentum_5 < -0.02:
        reasons.append("short-term momentum is clearly negative")
    elif momentum_5 < 0:
        reasons.append("short-term momentum is deteriorating")

    if momentum_10 < -0.02:
        reasons.append("medium-term momentum also remains negative")
    elif momentum_10 < 0:
        reasons.append("medium-term trend is losing strength")

    if vol_10 > 0.04:
        reasons.append("volatility is elevated and increases downside risk")
    elif vol_10 > 0.03:
        reasons.append("volatility is relatively elevated")
    else:
        reasons.append("the asset is still ranked in the lower part of the opportunity set")

    if market_trend < -0.01:
        reasons.append("the broader market environment is unfavorable")
    elif market_trend < 0:
        reasons.append("the broader market environment is not supportive")

    if oil_return < -0.02:
        reasons.append("energy market weakness may reinforce pressure on the asset")

    if score < 0:
        reasons.append("its advisor score is among the weakest in the selection")

    return "SELL because " + ", ".join(reasons) + "."


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

    print(f"[INFO] Loaded threshold from training: {threshold}")

    engine = get_engine()

    # Reconstruit exactement le dataset de features
    df, X, y, _ = build_dataset(engine)

    asset_cols = [c for c in df.columns if c.startswith("asset_")]

    # Garde seulement la dernière observation de chaque actif
    latest_rows = (
        df.sort_values("date_id")
        .groupby(asset_cols, dropna=False, as_index=False)
        .tail(1)
        .copy()
    )

    X_latest = latest_rows[feature_cols].copy()

    # Prédictions
    pred_proba = model.predict_proba(X_latest)[:, 1]
    pred_proba = pd.Series(pred_proba, index=latest_rows.index)

    pred_class = (pred_proba >= threshold).astype(int)

    latest_rows["proba_up"] = pred_proba
    latest_rows["predicted_direction"] = pred_class.map({1: "UP", 0: "DOWN"})

    # Nom actif
    latest_rows["ticker"] = latest_rows.apply(
        lambda row: get_asset_name(row, asset_cols),
        axis=1
    )

    # Confiance
    latest_rows["confidence"] = latest_rows["proba_up"].apply(get_confidence)

    # Tendance marché globale
    latest_rows["market_trend"] = (
        latest_rows["sp500_return"].fillna(0) +
        latest_rows["nasdaq_return"].fillna(0)
    ) / 2

    # Score advisor
    latest_rows["advisor_score"] = latest_rows.apply(compute_advisor_score, axis=1)

    # Signaux relatifs
    result = assign_signals_by_ranking(latest_rows)

    # Explications personnalisées
    result["explanation"] = result.apply(build_explanation, axis=1)

    # Arrondis
    result["proba_up"] = result["proba_up"].round(4)
    result["advisor_score"] = result["advisor_score"].round(4)

    # Colonnes finales
    result = result[
        [
            "date_id",
            "ticker",
            "proba_up",
            "predicted_direction",
            "signal",
            "confidence",
            "advisor_score",
            "momentum_5",
            "momentum_10",
            "rolling_vol_10",
            "oil_return",
            "sp500_return",
            "nasdaq_return",
            "explanation",
        ]
    ].copy()

    # Tri final
    signal_order = {"BUY": 0, "HOLD": 1, "SELL": 2}
    result["signal_rank"] = result["signal"].map(signal_order)

    result = (
        result.sort_values(
            by=["signal_rank", "advisor_score"],
            ascending=[True, False]
        )
        .drop(columns=["signal_rank"])
        .reset_index(drop=True)
    )

    output_path = OUTPUT_DIR / "latest_recommendations.csv"
    result.to_csv(output_path, index=False)

    print("\n=== AI RECOMMENDATIONS ===")
    print(result)

    print(f"\n[OK] Recommendations saved to: {output_path}")


if __name__ == "__main__":
    generate_recommendations()