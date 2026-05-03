from pathlib import Path
from typing import Any


BACKTEST_SUMMARY_COLUMNS = [
    "signal",
    "nb_obs",
    "avg_next_return",
    "median_next_return",
    "win_rate",
    "avg_proba_up",
    "avg_advisor_score",
]

BACKTEST_METRICS_COLUMNS = ["metric", "value"]


class BacktestFileNotFoundError(FileNotFoundError):
    """Raised when a backtest CSV has not been generated yet."""


class BacktestDataError(ValueError):
    """Raised when a backtest CSV cannot satisfy the API contract."""


class BacktestDependencyError(RuntimeError):
    """Raised when a required backtest service dependency is unavailable."""


def get_project_root() -> Path:
    backend_root = Path(__file__).resolve().parents[2]
    return backend_root.parent


def get_backtest_summary_path() -> Path:
    return get_project_root() / "outputs" / "backtest_summary.csv"


def get_backtest_metrics_path() -> Path:
    return get_project_root() / "outputs" / "backtest_metrics.csv"


def _get_pandas() -> Any:
    try:
        import pandas as pd
    except ImportError as exc:
        raise BacktestDependencyError(
            "pandas is required to read backtest CSV files."
        ) from exc

    return pd


def _read_backtest_csv(
    csv_path: Path,
    required_columns: list[str],
    display_path: str,
) -> tuple[Any, Any]:
    if not csv_path.exists():
        raise BacktestFileNotFoundError(f"Backtest file not found at {display_path}.")

    pd = _get_pandas()

    try:
        dataframe = pd.read_csv(csv_path)
    except pd.errors.EmptyDataError as exc:
        raise BacktestDataError(f"Backtest file is empty: {display_path}.") from exc
    except pd.errors.ParserError as exc:
        raise BacktestDataError(
            f"Backtest file could not be parsed: {display_path}."
        ) from exc

    missing_columns = [
        column for column in required_columns if column not in dataframe.columns
    ]
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise BacktestDataError(
            f"Backtest file {display_path} is missing required columns: {missing}"
        )

    return dataframe[required_columns], pd


def _json_safe(value: Any, pd: Any) -> Any:
    if pd.isna(value):
        return None
    return value


def _records_from_dataframe(dataframe: Any, pd: Any) -> list[dict[str, Any]]:
    records = dataframe.to_dict(orient="records")

    return [
        {key: _json_safe(value, pd) for key, value in record.items()}
        for record in records
    ]


def get_backtest_summary() -> list[dict[str, Any]]:
    dataframe, pd = _read_backtest_csv(
        get_backtest_summary_path(),
        BACKTEST_SUMMARY_COLUMNS,
        "outputs/backtest_summary.csv",
    )

    return _records_from_dataframe(dataframe, pd)


def get_backtest_metrics() -> list[dict[str, Any]]:
    dataframe, pd = _read_backtest_csv(
        get_backtest_metrics_path(),
        BACKTEST_METRICS_COLUMNS,
        "outputs/backtest_metrics.csv",
    )

    return _records_from_dataframe(dataframe, pd)
