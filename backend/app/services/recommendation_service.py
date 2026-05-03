from pathlib import Path
from typing import Any


RECOMMENDATION_COLUMNS = [
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


class RecommendationFileNotFoundError(FileNotFoundError):
    """Raised when the latest recommendation CSV has not been generated yet."""


class RecommendationDataError(ValueError):
    """Raised when the recommendation CSV cannot satisfy the API contract."""


class RecommendationDependencyError(RuntimeError):
    """Raised when a required recommendation service dependency is unavailable."""


def get_project_root() -> Path:
    backend_root = Path(__file__).resolve().parents[2]
    return backend_root.parent


def get_recommendations_path() -> Path:
    return get_project_root() / "outputs" / "latest_recommendations.csv"


def _get_pandas() -> Any:
    try:
        import pandas as pd
    except ModuleNotFoundError as exc:
        raise RecommendationDependencyError(
            "pandas is required to read recommendation CSV files."
        ) from exc

    return pd


def _read_recommendations_csv() -> tuple[Any, Any]:
    recommendations_path = get_recommendations_path()

    if not recommendations_path.exists():
        raise RecommendationFileNotFoundError(
            "Recommendation file not found at outputs/latest_recommendations.csv."
        )

    pd = _get_pandas()

    try:
        dataframe = pd.read_csv(recommendations_path)
    except pd.errors.EmptyDataError as exc:
        raise RecommendationDataError("Recommendation file is empty.") from exc
    except pd.errors.ParserError as exc:
        raise RecommendationDataError("Recommendation file could not be parsed.") from exc

    missing_columns = [
        column for column in RECOMMENDATION_COLUMNS if column not in dataframe.columns
    ]
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise RecommendationDataError(
            f"Recommendation file is missing required columns: {missing}"
        )

    return dataframe[RECOMMENDATION_COLUMNS], pd


def _json_safe(value: Any, pd: Any) -> Any:
    if pd.isna(value):
        return None
    return value


def get_latest_recommendations() -> list[dict[str, Any]]:
    dataframe, pd = _read_recommendations_csv()
    records = dataframe.to_dict(orient="records")

    return [
        {key: _json_safe(value, pd) for key, value in record.items()}
        for record in records
    ]


def get_recommendations_summary() -> dict[str, Any]:
    dataframe, pd = _read_recommendations_csv()
    signal_counts = dataframe["signal"].fillna("").str.upper().value_counts()

    proba_up = pd.to_numeric(dataframe["proba_up"], errors="coerce")
    advisor_score = pd.to_numeric(dataframe["advisor_score"], errors="coerce")

    average_proba_up = proba_up.mean()
    top_advisor_score = advisor_score.max()

    return {
        "total_recommendations": int(len(dataframe)),
        "buy_count": int(signal_counts.get("BUY", 0)),
        "hold_count": int(signal_counts.get("HOLD", 0)),
        "sell_count": int(signal_counts.get("SELL", 0)),
        "average_proba_up": _json_safe(average_proba_up, pd),
        "top_advisor_score": _json_safe(top_advisor_score, pd),
    }
