from __future__ import annotations

from datetime import date
from decimal import Decimal
from math import isfinite, sqrt
from typing import Any, Iterable

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError


PERFORMANCE_SCHEMA = "smartinvest"
RETURNS_VIEW = "v_market_returns_daily"
CUM_RETURN_VIEW = "v_market_cum_return"
TRADING_DAYS_PER_YEAR = 252


class PerformanceDatabaseError(RuntimeError):
    """Raised when performance data cannot be read from PostgreSQL."""


class PerformanceDataError(ValueError):
    """Raised when performance data cannot satisfy the API contract."""


class PerformanceNoDataError(ValueError):
    """Raised when no performance data exists for the requested filters."""


class PerformanceViewNotFoundError(ValueError):
    """Raised when a required performance view is not available."""


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
    return clean_number(numeric * 100)


def safe_sample_std(values: list[float]) -> float | None:
    if len(values) < 2:
        return None

    mean_value = sum(values) / len(values)
    variance = sum((value - mean_value) ** 2 for value in values) / (len(values) - 1)
    return clean_number(sqrt(variance))


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
        raise PerformanceDatabaseError(
            "Performance database configuration is unavailable."
        ) from exc

    return engine


def _execute_mappings(
    query: str,
    params: dict[str, Any] | None = None,
    error_message: str = "Unable to read performance data.",
) -> list[dict[str, Any]]:
    try:
        with _get_engine().connect() as connection:
            rows = connection.execute(text(query), params or {}).mappings().all()
            return [dict(row) for row in rows]
    except SQLAlchemyError as exc:
        if _is_missing_view_error(exc):
            raise PerformanceViewNotFoundError(
                "A required performance database view was not found."
            ) from exc
        raise PerformanceDatabaseError(error_message) from exc


def _where_clause(
    ticker: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> tuple[str, dict[str, Any]]:
    filters = []
    params: dict[str, Any] = {}

    if ticker:
        filters.append("ticker = :ticker")
        params["ticker"] = ticker
    if start_date:
        filters.append("date_id >= :start_date")
        params["start_date"] = start_date
    if end_date:
        filters.append("date_id <= :end_date")
        params["end_date"] = end_date

    if not filters:
        return "", params

    return "WHERE " + " AND ".join(filters), params


def _validate_ticker_exists(ticker: str) -> None:
    query = f"""
        SELECT 1
        FROM {PERFORMANCE_SCHEMA}.{RETURNS_VIEW}
        WHERE ticker = :ticker
        LIMIT 1
    """
    rows = _execute_mappings(
        query,
        {"ticker": ticker},
        "Unable to validate performance ticker.",
    )
    if not rows:
        raise PerformanceNoDataError(f"Ticker '{ticker}' was not found.")


def _row_date_key(row: dict[str, Any]) -> Any:
    return row.get("date_id")


def _clean_daily_row(row: dict[str, Any]) -> dict[str, Any]:
    daily_return = to_float_or_none(row.get("daily_return"))
    return {
        "date_id": to_iso_date(row.get("date_id")),
        "ticker": row.get("ticker"),
        "close": clean_number(row.get("close")),
        "close_prev": clean_number(row.get("close_prev")),
        "daily_return": daily_return,
        "daily_return_pct": safe_pct(daily_return),
    }


def _read_daily_rows(
    ticker: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    where_clause, params = _where_clause(ticker, start_date, end_date)
    limit_clause = ""
    if limit is not None:
        limit_clause = "LIMIT :limit"
        params["limit"] = limit

    query = f"""
        SELECT date_id, ticker, close, close_prev, daily_return
        FROM {PERFORMANCE_SCHEMA}.{RETURNS_VIEW}
        {where_clause}
        ORDER BY date_id
        {limit_clause}
    """

    return _execute_mappings(query, params, "Unable to read daily performance data.")


def compute_cumulative_series(
    rows: Iterable[dict[str, Any]],
    include_daily_return: bool = True,
) -> list[dict[str, Any]]:
    wealth_by_ticker: dict[str, float] = {}
    output: list[dict[str, Any]] = []

    for row in rows:
        ticker = row.get("ticker")
        daily_return = to_float_or_none(row.get("daily_return"))
        if not ticker or daily_return is None:
            continue

        wealth = wealth_by_ticker.get(ticker, 1.0) * (1.0 + daily_return)
        wealth_by_ticker[ticker] = wealth

        item: dict[str, Any] = {
            "date_id": to_iso_date(row.get("date_id")),
            "ticker": ticker,
        }
        if include_daily_return:
            item["daily_return"] = daily_return
        item["cumulative_return_pct"] = safe_pct(wealth - 1.0)
        output.append(item)

    return output


def compute_summary_metrics(
    ticker: str,
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    if not rows:
        raise PerformanceNoDataError(
            f"No performance data found for ticker '{ticker}' in the selected period."
        )

    ordered_rows = sorted(rows, key=_row_date_key)
    returns = [
        daily_return
        for daily_return in (
            to_float_or_none(row.get("daily_return")) for row in ordered_rows
        )
        if daily_return is not None
    ]
    closes = [
        close
        for close in (to_float_or_none(row.get("close")) for row in ordered_rows)
        if close is not None
    ]

    observations = len(ordered_rows)
    start_close = closes[0] if closes else None
    last_close = closes[-1] if closes else None

    average_daily_return_pct = None
    annualized_return_pct = None
    annualized_volatility_pct = None
    sharpe_ratio = None
    cumulative_return_pct = None
    max_drawdown_pct = None
    win_rate_pct = None
    best_daily_return_pct = None
    worst_daily_return_pct = None

    if returns:
        mean_return = sum(returns) / len(returns)
        average_daily_return_pct = safe_pct(mean_return)
        annualized_return_pct = safe_pct(mean_return * TRADING_DAYS_PER_YEAR)

        sample_std = safe_sample_std(returns)
        if sample_std is not None:
            annualized_volatility_pct = safe_pct(sample_std * sqrt(TRADING_DAYS_PER_YEAR))

        if annualized_return_pct is not None and annualized_volatility_pct:
            sharpe_ratio = clean_number(annualized_return_pct / annualized_volatility_pct)

        wealth = 1.0
        peak = 1.0
        drawdowns: list[float] = []
        for daily_return in returns:
            wealth *= 1.0 + daily_return
            peak = max(peak, wealth)
            if peak != 0:
                drawdowns.append(((wealth / peak) - 1.0) * 100)

        cumulative_return_pct = safe_pct(wealth - 1.0)
        max_drawdown_pct = clean_number(min(drawdowns)) if drawdowns else None
        win_rate_pct = clean_number(
            (sum(1 for daily_return in returns if daily_return > 0) / len(returns)) * 100
        )
        best_daily_return_pct = safe_pct(max(returns))
        worst_daily_return_pct = safe_pct(min(returns))

    return {
        "ticker": ticker,
        "start_date": to_iso_date(ordered_rows[0].get("date_id")),
        "end_date": to_iso_date(ordered_rows[-1].get("date_id")),
        "observations": observations,
        "start_close": clean_number(start_close),
        "last_close": clean_number(last_close),
        "cumulative_return_pct": clean_number(cumulative_return_pct),
        "annualized_return_pct": clean_number(annualized_return_pct),
        "annualized_volatility_pct": clean_number(annualized_volatility_pct),
        "sharpe_ratio": clean_number(sharpe_ratio),
        "max_drawdown_pct": clean_number(max_drawdown_pct),
        "win_rate_pct": clean_number(win_rate_pct),
        "best_daily_return_pct": clean_number(best_daily_return_pct),
        "worst_daily_return_pct": clean_number(worst_daily_return_pct),
        "average_daily_return_pct": clean_number(average_daily_return_pct),
    }


def get_performance_tickers() -> list[str]:
    query = f"""
        SELECT DISTINCT ticker
        FROM {PERFORMANCE_SCHEMA}.{RETURNS_VIEW}
        WHERE ticker IS NOT NULL
        ORDER BY ticker
    """
    rows = _execute_mappings(query, error_message="Unable to read performance tickers.")
    return [row["ticker"] for row in rows]


def get_performance_daily(
    ticker: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = 1000,
) -> list[dict[str, Any]]:
    rows = _read_daily_rows(ticker, start_date, end_date, limit)
    if ticker and not rows:
        _validate_ticker_exists(ticker)
        raise PerformanceNoDataError(
            f"No performance data found for ticker '{ticker}' in the selected period."
        )
    return [_clean_daily_row(row) for row in rows]


def get_performance_cumulative(
    ticker: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict[str, Any]]:
    rows = _read_daily_rows(ticker, start_date, end_date)
    if not rows:
        _validate_ticker_exists(ticker)
        raise PerformanceNoDataError(
            f"No performance data found for ticker '{ticker}' in the selected period."
        )
    return compute_cumulative_series(rows)


def get_performance_summary(
    ticker: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict[str, Any]:
    rows = _read_daily_rows(ticker, start_date, end_date)
    if not rows:
        _validate_ticker_exists(ticker)
    return compute_summary_metrics(ticker, rows)


def _ranking_from_cum_return(limit: int) -> dict[str, list[dict[str, Any]]]:
    query = f"""
        SELECT ticker, start_date, last_date, cum_return
        FROM {PERFORMANCE_SCHEMA}.{CUM_RETURN_VIEW}
        WHERE ticker IS NOT NULL
          AND cum_return IS NOT NULL
        ORDER BY cum_return DESC
    """
    rows = _execute_mappings(
        query,
        error_message="Unable to read cumulative performance ranking.",
    )

    cleaned = [
        {
            "ticker": row.get("ticker"),
            "start_date": to_iso_date(row.get("start_date")),
            "end_date": to_iso_date(row.get("last_date")),
            "cumulative_return_pct": safe_pct(row.get("cum_return")),
        }
        for row in rows
    ]
    cleaned = [
        row for row in cleaned if row["ticker"] and row["cumulative_return_pct"] is not None
    ]

    return {
        "top": cleaned[:limit],
        "worst": sorted(cleaned, key=lambda row: row["cumulative_return_pct"])[:limit],
    }


def _ranking_from_daily(
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = 5,
) -> dict[str, list[dict[str, Any]]]:
    where_clause, params = _where_clause(start_date=start_date, end_date=end_date)
    query = f"""
        SELECT date_id, ticker, daily_return
        FROM {PERFORMANCE_SCHEMA}.{RETURNS_VIEW}
        {where_clause}
        ORDER BY ticker, date_id
    """
    rows = _execute_mappings(
        query,
        params,
        "Unable to compute filtered performance ranking.",
    )

    by_ticker: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if row.get("ticker"):
            by_ticker.setdefault(row["ticker"], []).append(row)

    ranking_rows: list[dict[str, Any]] = []
    for ticker, ticker_rows in by_ticker.items():
        series = compute_cumulative_series(ticker_rows)
        if not series:
            continue
        ranking_rows.append(
            {
                "ticker": ticker,
                "start_date": series[0]["date_id"],
                "end_date": series[-1]["date_id"],
                "cumulative_return_pct": series[-1]["cumulative_return_pct"],
            }
        )

    ranking_rows = [
        row
        for row in ranking_rows
        if row["ticker"] and row["cumulative_return_pct"] is not None
    ]

    top = sorted(
        ranking_rows,
        key=lambda row: row["cumulative_return_pct"],
        reverse=True,
    )[:limit]
    worst = sorted(ranking_rows, key=lambda row: row["cumulative_return_pct"])[:limit]
    return {"top": top, "worst": worst}


def get_performance_ranking(
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = 5,
) -> dict[str, list[dict[str, Any]]]:
    if start_date is None and end_date is None:
        return _ranking_from_cum_return(limit)
    return _ranking_from_daily(start_date, end_date, limit)


def get_performance_compare(
    tickers: list[str],
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict[str, Any]]:
    if not tickers:
        raise PerformanceDataError("At least one ticker is required.")

    where_clause, params = _where_clause(start_date=start_date, end_date=end_date)
    params["tickers"] = tickers

    filter_prefix = "WHERE" if not where_clause else f"{where_clause} AND"
    query = f"""
        SELECT date_id, ticker, daily_return
        FROM {PERFORMANCE_SCHEMA}.{RETURNS_VIEW}
        {filter_prefix} ticker = ANY(:tickers)
        ORDER BY ticker, date_id
    """

    rows = _execute_mappings(
        query,
        params,
        "Unable to compute performance comparison.",
    )

    found_tickers = {row["ticker"] for row in rows if row.get("ticker")}
    missing_tickers = [ticker for ticker in tickers if ticker not in found_tickers]
    if missing_tickers:
        missing = ", ".join(missing_tickers)
        raise PerformanceNoDataError(f"No performance data found for ticker(s): {missing}.")

    return compute_cumulative_series(rows, include_daily_return=False)


def get_performance_cum_return(limit: int = 50) -> list[dict[str, Any]]:
    query = f"""
        SELECT ticker, start_date, last_date, start_close, last_close, cum_return
        FROM {PERFORMANCE_SCHEMA}.{CUM_RETURN_VIEW}
        ORDER BY cum_return DESC
        LIMIT :limit
    """
    rows = _execute_mappings(
        query,
        {"limit": limit},
        "Unable to read cumulative return data.",
    )

    return [
        {
            "ticker": row.get("ticker"),
            "start_date": to_iso_date(row.get("start_date")),
            "last_date": to_iso_date(row.get("last_date")),
            "start_close": clean_number(row.get("start_close")),
            "last_close": clean_number(row.get("last_close")),
            "cum_return": clean_number(row.get("cum_return")),
            "cum_return_pct": safe_pct(row.get("cum_return")),
        }
        for row in rows
    ]
