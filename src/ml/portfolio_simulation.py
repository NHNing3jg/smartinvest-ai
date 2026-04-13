from __future__ import annotations

from pathlib import Path

import pandas as pd

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

RECO_PATH = OUTPUT_DIR / "latest_recommendations.csv"


def normalize_weights(scores: pd.Series) -> pd.Series:
    """
    Convertit des scores positifs en poids qui somment à 1.
    """
    scores = scores.clip(lower=0)

    if scores.sum() == 0:
        return pd.Series([1 / len(scores)] * len(scores), index=scores.index)

    return scores / scores.sum()


def simulate_portfolio():
    if not RECO_PATH.exists():
        raise FileNotFoundError(
            f"Recommendation file not found: {RECO_PATH}. "
            "Run `python -m src.ml.generate_recommendations` first."
        )

    df = pd.read_csv(RECO_PATH)

    if df.empty:
        raise ValueError("Recommendation file is empty.")

    # garder uniquement les BUY
    buy_df = df[df["signal"] == "BUY"].copy()

    if buy_df.empty:
        # fallback : prendre le meilleur actif si aucun BUY
        buy_df = df.sort_values("advisor_score", ascending=False).head(1).copy()

    # score de pondération
    # plus advisor_score et proba_up sont élevés, plus le poids est grand
    buy_df["weight_score"] = (
        buy_df["advisor_score"].clip(lower=0) * 0.7
        + buy_df["proba_up"].clip(lower=0) * 0.3
    )

    buy_df["weight"] = normalize_weights(buy_df["weight_score"])

    # rendement attendu simple
    # ici on utilise un estimateur simple basé sur proba_up + momentum
    buy_df["expected_return"] = (
        buy_df["proba_up"] * 0.02
        + buy_df["momentum_5"] * 0.30
        + buy_df["momentum_10"] * 0.20
    )

    # proxy de risque
    buy_df["risk_score"] = buy_df["rolling_vol_10"].fillna(0).clip(lower=0)

    # contribution pondérée
    buy_df["weighted_expected_return"] = buy_df["weight"] * buy_df["expected_return"]
    buy_df["weighted_risk"] = buy_df["weight"] * buy_df["risk_score"]

    portfolio_expected_return = buy_df["weighted_expected_return"].sum()
    portfolio_risk = buy_df["weighted_risk"].sum()
    portfolio_assets = len(buy_df)

    # niveau de risque qualitatif
    if portfolio_risk < 0.015:
        risk_level = "Low"
    elif portfolio_risk < 0.03:
        risk_level = "Medium"
    else:
        risk_level = "High"

    # résumé portefeuille
    portfolio_summary = pd.DataFrame(
        {
            "metric": [
                "Number of selected assets",
                "Portfolio expected return",
                "Portfolio risk score",
                "Portfolio risk level",
            ],
            "value": [
                portfolio_assets,
                round(float(portfolio_expected_return), 4),
                round(float(portfolio_risk), 4),
                risk_level,
            ],
        }
    )

    allocation_df = buy_df[
        [
            "ticker",
            "signal",
            "confidence",
            "proba_up",
            "advisor_score",
            "expected_return",
            "risk_score",
            "weight",
            "explanation",
        ]
    ].copy()

    allocation_df["proba_up"] = allocation_df["proba_up"].round(4)
    allocation_df["advisor_score"] = allocation_df["advisor_score"].round(4)
    allocation_df["expected_return"] = allocation_df["expected_return"].round(4)
    allocation_df["risk_score"] = allocation_df["risk_score"].round(4)
    allocation_df["weight"] = allocation_df["weight"].round(4)

    allocation_df = allocation_df.sort_values("weight", ascending=False).reset_index(drop=True)

    allocation_path = OUTPUT_DIR / "portfolio_allocation.csv"
    summary_path = OUTPUT_DIR / "portfolio_summary.csv"

    allocation_df.to_csv(allocation_path, index=False)
    portfolio_summary.to_csv(summary_path, index=False)

    print("\n=== PORTFOLIO ALLOCATION ===")
    print(allocation_df)

    print("\n=== PORTFOLIO SUMMARY ===")
    print(portfolio_summary)

    print(f"\n[OK] Allocation saved to: {allocation_path}")
    print(f"[OK] Summary saved to: {summary_path}")


if __name__ == "__main__":
    simulate_portfolio()