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


def get_asset_name(row: pd.Series, asset_cols: list[str]) -> str:
    for col in asset_cols:
        if row.get(col, 0) == 1:
            return col.replace("asset_", "")
    return "UNKNOWN"


def compute_advisor_score(row: pd.Series) -> float:
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
    return score


def assign_signals_by_ranking(group: pd.DataFrame) -> pd.DataFrame:
    group = group.sort_values("advisor_score", ascending=False).reset_index(drop=True).copy()
    n = len(group)

    group["signal"] = "HOLD"

    if n == 0:
        return group

    spread = group["advisor_score"].max() - group["advisor_score"].min()

    if n >= 5:
        if spread < 0.03:
            group.loc[group.index[0], "signal"] = "BUY"
            group.loc[group.index[-1], "signal"] = "SELL"
        else:
            group.loc[group.index[:2], "signal"] = "BUY"
            group.loc[group.index[-2:], "signal"] = "SELL"
    elif n == 4:
        group.loc[group.index[0], "signal"] = "BUY"
        group.loc[group.index[-1], "signal"] = "SELL"
    elif n == 3:
        group.loc[group.index[0], "signal"] = "BUY"
        group.loc[group.index[-1], "signal"] = "SELL"
    elif n == 2:
        if spread >= 0.03:
            group.loc[group.index[0], "signal"] = "BUY"
            group.loc[group.index[1], "signal"] = "SELL"

    return group


def backtest():
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

    # dataset complet historique
    df, X, y, _ = build_dataset(engine)

    asset_cols = [c for c in df.columns if c.startswith("asset_")]

    # prédictions historiques
    proba_up = model.predict_proba(X[feature_cols])[:, 1]
    proba_up = pd.Series(proba_up, index=df.index)

    df = df.copy()
    df["proba_up"] = proba_up
    df["predicted_direction"] = (df["proba_up"] >= threshold).astype(int).map({1: "UP", 0: "DOWN"})
    df["ticker"] = df.apply(lambda row: get_asset_name(row, asset_cols), axis=1)

    df["market_trend"] = (
        df["sp500_return"].fillna(0) +
        df["nasdaq_return"].fillna(0)
    ) / 2

    df["advisor_score"] = df.apply(compute_advisor_score, axis=1)

    # rendement réel du lendemain
    df["next_day_return"] = df.groupby("ticker")["daily_return"].shift(-1)

    # appliquer les signaux par date (ranking relatif entre actifs)
    signal_frames = []
    for date_id, group in df.groupby("date_id"):
        signal_frames.append(assign_signals_by_ranking(group))

    signal_df = pd.concat(signal_frames, ignore_index=True)

    # garder les lignes valides
    signal_df = signal_df.dropna(subset=["next_day_return"]).copy()

    # succès du signal
    def is_success(row: pd.Series) -> int:
        if row["signal"] == "BUY":
            return int(row["next_day_return"] > 0)
        if row["signal"] == "SELL":
            return int(row["next_day_return"] < 0)
        # HOLD = zone neutre ; succès si mouvement faible
        return int(abs(row["next_day_return"]) < 0.01)

    signal_df["success"] = signal_df.apply(is_success, axis=1)

    # résumé global
    summary = (
        signal_df.groupby("signal")
        .agg(
            nb_obs=("signal", "count"),
            avg_next_return=("next_day_return", "mean"),
            median_next_return=("next_day_return", "median"),
            win_rate=("success", "mean"),
            avg_proba_up=("proba_up", "mean"),
            avg_advisor_score=("advisor_score", "mean"),
        )
        .reset_index()
    )

    summary["avg_next_return"] = summary["avg_next_return"].round(4)
    summary["median_next_return"] = summary["median_next_return"].round(4)
    summary["win_rate"] = (summary["win_rate"] * 100).round(2)
    summary["avg_proba_up"] = summary["avg_proba_up"].round(4)
    summary["avg_advisor_score"] = summary["avg_advisor_score"].round(4)

    # backtest long-only simple : suivre uniquement BUY
    buy_df = signal_df[signal_df["signal"] == "BUY"].copy()
    sell_df = signal_df[signal_df["signal"] == "SELL"].copy()
    hold_df = signal_df[signal_df["signal"] == "HOLD"].copy()

    buy_mean_return = buy_df["next_day_return"].mean() if not buy_df.empty else 0
    sell_mean_return = sell_df["next_day_return"].mean() if not sell_df.empty else 0
    hold_mean_return = hold_df["next_day_return"].mean() if not hold_df.empty else 0

    overall_metrics = pd.DataFrame(
        {
            "metric": [
                "BUY mean next-day return",
                "SELL mean next-day return",
                "HOLD mean next-day return",
                "BUY win rate",
                "SELL win rate",
                "HOLD win rate",
            ],
            "value": [
                round(buy_mean_return, 4),
                round(sell_mean_return, 4),
                round(hold_mean_return, 4),
                round(buy_df["success"].mean() * 100, 2) if not buy_df.empty else 0,
                round(sell_df["success"].mean() * 100, 2) if not sell_df.empty else 0,
                round(hold_df["success"].mean() * 100, 2) if not hold_df.empty else 0,
            ],
        }
    )

    # sauvegarde
    detailed_path = OUTPUT_DIR / "backtest_detailed.csv"
    summary_path = OUTPUT_DIR / "backtest_summary.csv"
    metrics_path = OUTPUT_DIR / "backtest_metrics.csv"

    signal_df.to_csv(detailed_path, index=False)
    summary.to_csv(summary_path, index=False)
    overall_metrics.to_csv(metrics_path, index=False)

    print("\n=== BACKTEST SUMMARY ===")
    print(summary)

    print("\n=== OVERALL METRICS ===")
    print(overall_metrics)

    print(f"\n[OK] Detailed backtest saved to: {detailed_path}")
    print(f"[OK] Summary backtest saved to: {summary_path}")
    print(f"[OK] Metrics backtest saved to: {metrics_path}")


if __name__ == "__main__":
    backtest()