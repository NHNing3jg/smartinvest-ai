from __future__ import annotations

from datetime import date
from decimal import Decimal
from math import isfinite, sqrt
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError


ENERGY_SCHEMA = "smartinvest"
OIL_DAILY_VIEW = "v_oil_daily"
MARKET_RETURNS_VIEW = "v_market_returns_daily"
TRADING_DAYS_PER_YEAR = 252


class EnergyDatabaseError(RuntimeError):
    """Raised when energy data cannot be read from PostgreSQL."""


class EnergyDataError(ValueError):
    """Raised when energy data cannot satisfy the API contract."""


class EnergyNoDataError(ValueError):
    """Raised when no energy data exists for the requested filters."""


class EnergyViewNotFoundError(ValueError):
    """Raised when a required energy database view is not available."""


def to_float_or_none(value: Any) -> float | None:
    if value is None:
        return None

    try:
        if isinstance(value, Decimal):
            numeric = float(value)
        elif hasattr(value, "item"):
            numeric = float(value.item())
        else:
            numeric = float(value)
    except (TypeError, ValueError, OverflowError):
        return None

    if not isfinite(numeric):
        return None

    return numeric


def to_int_or_none(value: Any) -> int | None:
    if value is None:
        return None

    try:
        numeric = int(value)
    except (TypeError, ValueError, OverflowError):
        return None

    return numeric


def to_iso_date(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def clean_number(value: Any) -> float | int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value

    numeric = to_float_or_none(value)
    if numeric is None:
        return None

    return numeric


def safe_pct(value: Any) -> float | None:
    numeric = to_float_or_none(value)
    if numeric is None:
        return None
    return to_float_or_none(numeric * 100)


def safe_sample_std(values: list[float]) -> float | None:
    if len(values) < 2:
        return None

    mean_value = sum(values) / len(values)
    variance = sum((value - mean_value) ** 2 for value in values) / (len(values) - 1)
    return clean_number(sqrt(variance))


def safe_correlation(pairs: list[tuple[float | None, float | None]]) -> float | None:
    valid_pairs = [
        (left, right)
        for left, right in pairs
        if left is not None and right is not None
    ]
    if len(valid_pairs) < 2:
        return None

    left_values = [pair[0] for pair in valid_pairs]
    right_values = [pair[1] for pair in valid_pairs]
    left_mean = sum(left_values) / len(left_values)
    right_mean = sum(right_values) / len(right_values)

    numerator = sum(
        (left - left_mean) * (right - right_mean)
        for left, right in valid_pairs
    )
    left_sum_sq = sum((value - left_mean) ** 2 for value in left_values)
    right_sum_sq = sum((value - right_mean) ** 2 for value in right_values)
    denominator = sqrt(left_sum_sq * right_sum_sq)

    if denominator == 0:
        return None

    return clean_number(numerator / denominator)


def safe_regression(pairs: list[tuple[float | None, float | None]]) -> dict[str, float | None]:
    valid_pairs = [
        (oil_return, asset_return)
        for oil_return, asset_return in pairs
        if oil_return is not None and asset_return is not None
    ]
    if len(valid_pairs) < 2:
        return {"beta": None, "alpha": None, "r_squared": None, "correlation": None}

    oil_values = [pair[0] for pair in valid_pairs]
    asset_values = [pair[1] for pair in valid_pairs]
    oil_mean = sum(oil_values) / len(oil_values)
    asset_mean = sum(asset_values) / len(asset_values)
    oil_sum_sq = sum((value - oil_mean) ** 2 for value in oil_values)

    if oil_sum_sq == 0:
        correlation = safe_correlation(valid_pairs)
        return {
            "beta": None,
            "alpha": None,
            "r_squared": clean_number(correlation * correlation) if correlation is not None else None,
            "correlation": correlation,
        }

    covariance_sum = sum(
        (oil_return - oil_mean) * (asset_return - asset_mean)
        for oil_return, asset_return in valid_pairs
    )
    beta = covariance_sum / oil_sum_sq
    alpha = asset_mean - beta * oil_mean
    correlation = safe_correlation(valid_pairs)

    return {
        "beta": clean_number(beta),
        "alpha": clean_number(alpha),
        "r_squared": clean_number(correlation * correlation) if correlation is not None else None,
        "correlation": correlation,
    }


def correlation_label(value: float | None) -> str:
    if value is None:
        return "N/A"
    if value > 0.7:
        return "Strong Positive"
    if value > 0.3:
        return "Moderate Positive"
    if value < -0.7:
        return "Strong Negative"
    if value < -0.3:
        return "Moderate Negative"
    return "Weak / Uncorrelated"


def clamp_corr_window(value: int | None) -> int:
    if value is None:
        return 30
    return max(5, min(120, value))


def _is_missing_view_error(exc: SQLAlchemyError) -> bool:
    orig = getattr(exc, "orig", None)
    pgcode = getattr(orig, "pgcode", None) or getattr(orig, "sqlstate", None)
    if pgcode == "42P01":
        return True

    message = str(orig or exc).lower()
    return "does not exist" in message or "undefinedtable" in message


def _get_engine() -> Any:
    try:
        from app.core.database import engine
    except Exception as exc:
        raise EnergyDatabaseError("Energy database configuration is unavailable.") from exc

    return engine


def _execute_mappings(
    query: str,
    params: dict[str, Any] | None = None,
    error_message: str = "Unable to read energy data.",
) -> list[dict[str, Any]]:
    try:
        with _get_engine().connect() as connection:
            rows = connection.execute(text(query), params or {}).mappings().all()
            return [dict(row) for row in rows]
    except SQLAlchemyError as exc:
        if _is_missing_view_error(exc):
            raise EnergyViewNotFoundError("A required energy database view was not found.") from exc
        raise EnergyDatabaseError(error_message) from exc


def build_date_filters(
    start_date: date | None = None,
    end_date: date | None = None,
    column_name: str = "date_id",
) -> tuple[list[str], dict[str, Any]]:
    filters: list[str] = []
    params: dict[str, Any] = {}

    if start_date:
        filters.append(f"{column_name} >= :start_date")
        params["start_date"] = start_date
    if end_date:
        filters.append(f"{column_name} <= :end_date")
        params["end_date"] = end_date

    return filters, params


def _where_clause(filters: list[str]) -> str:
    if not filters:
        return ""
    return "WHERE " + " AND ".join(filters)


def _validate_oil_ticker_exists(oil_ticker: str) -> None:
    query = f"""
        SELECT 1
        FROM {ENERGY_SCHEMA}.{OIL_DAILY_VIEW}
        WHERE ticker = :ticker
        LIMIT 1
    """
    rows = _execute_mappings(query, {"ticker": oil_ticker}, "Unable to validate oil ticker.")
    if not rows:
        raise EnergyNoDataError(f"Oil ticker '{oil_ticker}' was not found.")


def _validate_asset_ticker_exists(asset_ticker: str) -> None:
    query = f"""
        SELECT 1
        FROM {ENERGY_SCHEMA}.{MARKET_RETURNS_VIEW}
        WHERE ticker = :ticker
        LIMIT 1
    """
    rows = _execute_mappings(query, {"ticker": asset_ticker}, "Unable to validate asset ticker.")
    if not rows:
        raise EnergyNoDataError(f"Asset ticker '{asset_ticker}' was not found.")


def _clean_oil_row(row: dict[str, Any]) -> dict[str, Any]:
    daily_return = to_float_or_none(row.get("daily_return"))
    return {
        "date_id": to_iso_date(row.get("date_id")),
        "ticker": row.get("ticker"),
        "open": clean_number(row.get("open")),
        "high": clean_number(row.get("high")),
        "low": clean_number(row.get("low")),
        "close": clean_number(row.get("close")),
        "adj_close": clean_number(row.get("adj_close")),
        "volume": to_int_or_none(row.get("volume")),
        "daily_return": daily_return,
        "daily_return_pct": safe_pct(daily_return),
    }


def get_oil_rows(
    oil_ticker: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    filters, params = build_date_filters(start_date, end_date)
    if oil_ticker:
        filters.insert(0, "ticker = :oil_ticker")
        params["oil_ticker"] = oil_ticker

    limit_clause = ""
    if limit is not None:
        limit_clause = "LIMIT :limit"
        params["limit"] = limit

    query = f"""
        SELECT date_id, ticker, open, high, low, close, adj_close, volume, daily_return
        FROM {ENERGY_SCHEMA}.{OIL_DAILY_VIEW}
        {_where_clause(filters)}
        ORDER BY date_id ASC
        {limit_clause}
    """

    rows = _execute_mappings(query, params, "Unable to read oil daily data.")
    if oil_ticker and not rows:
        _validate_oil_ticker_exists(oil_ticker)
        raise EnergyNoDataError(
            f"No oil data found for ticker '{oil_ticker}' in the selected period."
        )

    return rows


def get_asset_return_rows(
    asset_ticker: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict[str, Any]]:
    filters, params = build_date_filters(start_date, end_date)
    filters.insert(0, "ticker = :asset_ticker")
    params["asset_ticker"] = asset_ticker

    query = f"""
        SELECT date_id, ticker, daily_return
        FROM {ENERGY_SCHEMA}.{MARKET_RETURNS_VIEW}
        {_where_clause(filters)}
        ORDER BY date_id ASC
    """

    rows = _execute_mappings(query, params, "Unable to read asset return data.")
    if not rows:
        _validate_asset_ticker_exists(asset_ticker)
        raise EnergyNoDataError(
            f"No asset return data found for ticker '{asset_ticker}' in the selected period."
        )

    return rows


def get_oil_series() -> list[str]:
    query = f"""
        SELECT DISTINCT ticker
        FROM {ENERGY_SCHEMA}.{OIL_DAILY_VIEW}
        WHERE ticker IS NOT NULL
        ORDER BY ticker ASC
    """
    rows = _execute_mappings(query, error_message="Unable to read oil tickers.")
    return [row["ticker"] for row in rows if row.get("ticker")]


def get_energy_assets() -> list[str]:
    query = f"""
        SELECT DISTINCT ticker
        FROM {ENERGY_SCHEMA}.{MARKET_RETURNS_VIEW}
        WHERE ticker IS NOT NULL
        ORDER BY ticker ASC
    """
    rows = _execute_mappings(query, error_message="Unable to read asset tickers.")
    return [row["ticker"] for row in rows if row.get("ticker")]


def get_oil_daily(
    oil_ticker: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = 1000,
) -> list[dict[str, Any]]:
    rows = get_oil_rows(oil_ticker, start_date, end_date, limit)
    return [_clean_oil_row(row) for row in rows]


def get_merged_energy_rows(
    oil_ticker: str,
    asset_ticker: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict[str, Any]]:
    oil_rows = get_oil_rows(oil_ticker, start_date, end_date)
    asset_rows = get_asset_return_rows(asset_ticker, start_date, end_date)
    asset_by_date = {row.get("date_id"): row for row in asset_rows}

    merged_rows: list[dict[str, Any]] = []
    for oil_row in oil_rows:
        date_key = oil_row.get("date_id")
        asset_row = asset_by_date.get(date_key)
        if asset_row is None:
            continue

        oil_return = to_float_or_none(oil_row.get("daily_return"))
        asset_return = to_float_or_none(asset_row.get("daily_return"))
        merged_rows.append(
            {
                "date_id": date_key,
                "oil_ticker": oil_ticker,
                "asset_ticker": asset_ticker,
                "oil_close": clean_number(oil_row.get("close")),
                "oil_high": clean_number(oil_row.get("high")),
                "oil_low": clean_number(oil_row.get("low")),
                "oil_volume": to_int_or_none(oil_row.get("volume")),
                "oil_daily_return": oil_return,
                "oil_daily_return_pct": safe_pct(oil_return),
                "asset_daily_return": asset_return,
                "asset_daily_return_pct": safe_pct(asset_return),
            }
        )

    merged_rows.sort(key=lambda row: row["date_id"])
    if not merged_rows:
        _validate_oil_ticker_exists(oil_ticker)
        _validate_asset_ticker_exists(asset_ticker)
        raise EnergyNoDataError(
            f"No common energy/asset sessions found for oil ticker '{oil_ticker}' and asset ticker '{asset_ticker}'."
        )

    return merged_rows


def compute_rolling_correlation(
    merged_rows: list[dict[str, Any]],
    corr_window: int,
) -> list[dict[str, Any]]:
    window = clamp_corr_window(corr_window)
    output: list[dict[str, Any]] = []

    for index, row in enumerate(merged_rows):
        rolling_value = None
        if index + 1 >= window:
            window_rows = merged_rows[index + 1 - window : index + 1]
            pairs = [
                (
                    to_float_or_none(window_row.get("oil_daily_return")),
                    to_float_or_none(window_row.get("asset_daily_return")),
                )
                for window_row in window_rows
            ]
            rolling_value = safe_correlation(pairs)

        output.append(
            {
                "date_id": to_iso_date(row.get("date_id")),
                "rolling_correlation": rolling_value,
            }
        )

    return output


def _with_rolling_correlation(
    merged_rows: list[dict[str, Any]],
    corr_window: int,
) -> list[dict[str, Any]]:
    rolling_by_date = {
        row["date_id"]: row["rolling_correlation"]
        for row in compute_rolling_correlation(merged_rows, corr_window)
    }

    return [
        {
            "date_id": to_iso_date(row.get("date_id")),
            "oil_ticker": row.get("oil_ticker"),
            "asset_ticker": row.get("asset_ticker"),
            "oil_close": clean_number(row.get("oil_close")),
            "oil_daily_return": clean_number(row.get("oil_daily_return")),
            "oil_daily_return_pct": clean_number(row.get("oil_daily_return_pct")),
            "asset_daily_return": clean_number(row.get("asset_daily_return")),
            "asset_daily_return_pct": clean_number(row.get("asset_daily_return_pct")),
            "rolling_correlation": clean_number(rolling_by_date.get(to_iso_date(row.get("date_id")))),
        }
        for row in merged_rows
    ]


def get_energy_summary(
    oil_ticker: str,
    asset_ticker: str,
    start_date: date | None = None,
    end_date: date | None = None,
    corr_window: int = 30,
) -> dict[str, Any]:
    window = clamp_corr_window(corr_window)
    merged_rows = get_merged_energy_rows(oil_ticker, asset_ticker, start_date, end_date)

    closes = [
        to_float_or_none(row.get("oil_close"))
        for row in merged_rows
        if to_float_or_none(row.get("oil_close")) is not None
    ]
    oil_returns = [
        to_float_or_none(row.get("oil_daily_return"))
        for row in merged_rows
        if to_float_or_none(row.get("oil_daily_return")) is not None
    ]
    volumes = [
        volume
        for volume in (to_int_or_none(row.get("oil_volume")) for row in merged_rows)
        if volume is not None
    ]
    highs = [
        high
        for high in (to_float_or_none(row.get("oil_high")) for row in merged_rows)
        if high is not None
    ]
    lows = [
        low
        for low in (to_float_or_none(row.get("oil_low")) for row in merged_rows)
        if low is not None
    ]
    pairs = [
        (
            to_float_or_none(row.get("oil_daily_return")),
            to_float_or_none(row.get("asset_daily_return")),
        )
        for row in merged_rows
    ]

    oil_last_close = closes[-1] if closes else None
    oil_previous_close = closes[-2] if len(closes) >= 2 else None
    oil_change_pct = None
    if oil_last_close is not None and oil_previous_close not in (None, 0):
        oil_change_pct = ((oil_last_close - oil_previous_close) / abs(oil_previous_close)) * 100

    oil_period_return_pct = None
    if len(closes) >= 2 and closes[0] != 0:
        oil_period_return_pct = (closes[-1] / closes[0] - 1) * 100

    oil_annualized_volatility_pct = None
    oil_std = safe_sample_std(oil_returns)
    if oil_std is not None:
        oil_annualized_volatility_pct = oil_std * sqrt(TRADING_DAYS_PER_YEAR) * 100

    global_correlation = safe_correlation(pairs)
    rolling_rows = compute_rolling_correlation(merged_rows, window)
    latest_rolling_correlation = next(
        (
            row["rolling_correlation"]
            for row in reversed(rolling_rows)
            if row["rolling_correlation"] is not None
        ),
        None,
    )
    regression = safe_regression(pairs)

    return {
        "oil_ticker": oil_ticker,
        "asset_ticker": asset_ticker,
        "start_date": to_iso_date(merged_rows[0].get("date_id")),
        "end_date": to_iso_date(merged_rows[-1].get("date_id")),
        "common_sessions": len(merged_rows),
        "oil_last_close": clean_number(oil_last_close),
        "oil_previous_close": clean_number(oil_previous_close),
        "oil_change_pct": clean_number(oil_change_pct),
        "oil_period_return_pct": clean_number(oil_period_return_pct),
        "oil_average_volume": clean_number(sum(volumes) / len(volumes)) if volumes else None,
        "oil_period_high": clean_number(max(highs)) if highs else None,
        "oil_period_low": clean_number(min(lows)) if lows else None,
        "oil_annualized_volatility_pct": clean_number(oil_annualized_volatility_pct),
        "global_correlation": clean_number(global_correlation),
        "global_correlation_label": correlation_label(global_correlation),
        "latest_rolling_correlation": clean_number(latest_rolling_correlation),
        "latest_rolling_correlation_label": correlation_label(latest_rolling_correlation),
        "corr_window": window,
        "beta": clean_number(regression["beta"]),
        "alpha": clean_number(regression["alpha"]),
        "r_squared": clean_number(regression["r_squared"]),
    }


def get_energy_merged(
    oil_ticker: str,
    asset_ticker: str,
    start_date: date | None = None,
    end_date: date | None = None,
    corr_window: int = 30,
    limit: int = 1000,
) -> list[dict[str, Any]]:
    window = clamp_corr_window(corr_window)
    merged_rows = get_merged_energy_rows(oil_ticker, asset_ticker, start_date, end_date)
    return _with_rolling_correlation(merged_rows, window)[:limit]


def get_energy_rolling_correlation(
    oil_ticker: str,
    asset_ticker: str,
    start_date: date | None = None,
    end_date: date | None = None,
    corr_window: int = 30,
) -> list[dict[str, Any]]:
    window = clamp_corr_window(corr_window)
    merged_rows = get_merged_energy_rows(oil_ticker, asset_ticker, start_date, end_date)
    rolling_rows = compute_rolling_correlation(merged_rows, window)
    return [
        {
            "date_id": row["date_id"],
            "rolling_correlation": clean_number(row["rolling_correlation"]),
        }
        for row in rolling_rows
        if row["rolling_correlation"] is not None
    ]


def get_energy_scatter(
    oil_ticker: str,
    asset_ticker: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict[str, Any]:
    merged_rows = get_merged_energy_rows(oil_ticker, asset_ticker, start_date, end_date)
    pairs = [
        (
            to_float_or_none(row.get("oil_daily_return")),
            to_float_or_none(row.get("asset_daily_return")),
        )
        for row in merged_rows
    ]
    regression = safe_regression(pairs)

    points = []
    for row in merged_rows:
        oil_return_pct = safe_pct(row.get("oil_daily_return"))
        asset_return_pct = safe_pct(row.get("asset_daily_return"))
        if oil_return_pct is None or asset_return_pct is None:
            continue

        points.append(
            {
                "date_id": to_iso_date(row.get("date_id")),
                "oil_daily_return_pct": clean_number(oil_return_pct),
                "asset_daily_return_pct": clean_number(asset_return_pct),
            }
        )

    return {
        "points": points,
        "regression": {
            "beta": clean_number(regression["beta"]),
            "alpha": clean_number(regression["alpha"]),
            "r_squared": clean_number(regression["r_squared"]),
            "correlation": clean_number(regression["correlation"]),
        },
    }
