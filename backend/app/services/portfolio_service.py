from pathlib import Path
from typing import Any


PORTFOLIO_ALLOCATION_COLUMNS = [
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

PORTFOLIO_SUMMARY_COLUMNS = ["metric", "value"]

PORTFOLIO_SUMMARY_METRICS = {
    "Number of selected assets": "total_assets",
    "Portfolio expected return": "expected_return",
    "Portfolio risk score": "risk_score",
    "Portfolio risk level": "risk_level",
}


class PortfolioFileNotFoundError(FileNotFoundError):
    """Raised when a portfolio CSV has not been generated yet."""


class PortfolioDataError(ValueError):
    """Raised when a portfolio CSV cannot satisfy the API contract."""


class PortfolioDependencyError(RuntimeError):
    """Raised when a required portfolio service dependency is unavailable."""


def get_project_root() -> Path:
    backend_root = Path(__file__).resolve().parents[2]
    return backend_root.parent


def get_portfolio_allocation_path() -> Path:
    return get_project_root() / "outputs" / "portfolio_allocation.csv"


def get_portfolio_summary_path() -> Path:
    return get_project_root() / "outputs" / "portfolio_summary.csv"


def _get_pandas() -> Any:
    try:
        import pandas as pd
    except ImportError as exc:
        raise PortfolioDependencyError(
            "pandas is required to read portfolio CSV files."
        ) from exc

    return pd


def _read_portfolio_csv(
    csv_path: Path,
    required_columns: list[str],
    display_path: str,
) -> tuple[Any, Any]:
    if not csv_path.exists():
        raise PortfolioFileNotFoundError(f"Portfolio file not found at {display_path}.")

    pd = _get_pandas()

    try:
        dataframe = pd.read_csv(csv_path)
    except pd.errors.EmptyDataError as exc:
        raise PortfolioDataError(f"Portfolio file is empty: {display_path}.") from exc
    except pd.errors.ParserError as exc:
        raise PortfolioDataError(
            f"Portfolio file could not be parsed: {display_path}."
        ) from exc

    missing_columns = [
        column for column in required_columns if column not in dataframe.columns
    ]
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise PortfolioDataError(
            f"Portfolio file {display_path} is missing required columns: {missing}"
        )

    return dataframe[required_columns], pd


def _json_safe(value: Any, pd: Any) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def _records_from_dataframe(dataframe: Any, pd: Any) -> list[dict[str, Any]]:
    records = dataframe.to_dict(orient="records")

    return [
        {key: _json_safe(value, pd) for key, value in record.items()}
        for record in records
    ]


def _coerce_summary_value(key: str, value: Any, pd: Any) -> Any:
    value = _json_safe(value, pd)

    if value is None or key == "risk_level":
        return value

    numeric_value = pd.to_numeric(value, errors="coerce")
    if pd.isna(numeric_value):
        return value

    if key == "total_assets":
        return int(numeric_value)

    return float(numeric_value)


def get_portfolio_allocation() -> list[dict[str, Any]]:
    dataframe, pd = _read_portfolio_csv(
        get_portfolio_allocation_path(),
        PORTFOLIO_ALLOCATION_COLUMNS,
        "outputs/portfolio_allocation.csv",
    )

    return _records_from_dataframe(dataframe, pd)


def get_portfolio_summary() -> dict[str, Any]:
    dataframe, pd = _read_portfolio_csv(
        get_portfolio_summary_path(),
        PORTFOLIO_SUMMARY_COLUMNS,
        "outputs/portfolio_summary.csv",
    )

    summary_rows = dataframe.set_index("metric")["value"].to_dict()
    missing_metrics = [
        metric for metric in PORTFOLIO_SUMMARY_METRICS if metric not in summary_rows
    ]
    if missing_metrics:
        missing = ", ".join(missing_metrics)
        raise PortfolioDataError(
            f"Portfolio file outputs/portfolio_summary.csv is missing required metrics: {missing}"
        )

    return {
        api_key: _coerce_summary_value(api_key, summary_rows[csv_metric], pd)
        for csv_metric, api_key in PORTFOLIO_SUMMARY_METRICS.items()
    }
