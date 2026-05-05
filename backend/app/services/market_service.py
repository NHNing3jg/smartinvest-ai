from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError


MARKET_SCHEMA = "smartinvest"
MARKET_VIEW = "v_market_daily"
MARKET_COLUMNS = ["date_id", "ticker", "open", "high", "low", "close", "volume"]
SUMMARY_COLUMNS = ["date_id", "ticker", "close", "volume", "high", "low"]


class MarketDatabaseError(RuntimeError):
    """Raised when market data cannot be read from PostgreSQL."""


class MarketDataError(ValueError):
    """Raised when market data cannot satisfy the API contract."""


class MarketNoDataError(ValueError):
    """Raised when no market data exists for the requested filters."""


class MarketViewNotFoundError(ValueError):
    """Raised when the market daily view is not available."""


def _get_pandas() -> Any:
    try:
        import pandas as pd
    except ImportError as exc:
        raise MarketDataError("pandas is required to process market data.") from exc

    return pd


def _json_safe(value: Any, pd: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    return value


def _records_from_dataframe(dataframe: Any, pd: Any) -> list[dict[str, Any]]:
    records = dataframe.to_dict(orient="records")
    return [
        {key: _json_safe(value, pd) for key, value in record.items()}
        for record in records
    ]


def _get_engine() -> Any:
    try:
        from app.core.database import engine
    except Exception as exc:
        message = str(exc)
        if message:
            raise MarketDatabaseError(message) from exc

        raise MarketDatabaseError("Market database configuration is invalid.") from exc

    return engine


def _available_columns() -> list[str]:
    return list(_available_column_types().keys())


def _available_column_types() -> dict[str, str]:
    query = text(
        """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = :schema_name
          AND table_name = :view_name
        ORDER BY ordinal_position
        """
    )

    try:
        with _get_engine().connect() as connection:
            rows = connection.execute(
                query,
                {"schema_name": MARKET_SCHEMA, "view_name": MARKET_VIEW},
            ).mappings()
            column_types = {row["column_name"]: row["data_type"] for row in rows}
    except SQLAlchemyError as exc:
        raise MarketDatabaseError("Unable to read market view metadata.") from exc

    if not column_types:
        raise MarketViewNotFoundError(
            f"Market view {MARKET_SCHEMA}.{MARKET_VIEW} was not found."
        )

    return column_types


def _selectable_columns(columns: list[str]) -> list[str]:
    available = set(_available_columns())
    selected = [column for column in columns if column in available]

    missing_required = [
        column for column in ("date_id", "ticker") if column not in selected
    ]
    if missing_required:
        missing = ", ".join(missing_required)
        raise MarketDataError(
            f"Market view is missing required columns: {missing}"
        )

    return selected


def _date_filter_value(value: date, date_id_type: str) -> str | int:
    if date_id_type in {"integer", "bigint", "smallint", "numeric"}:
        return int(value.strftime("%Y%m%d"))
    return value.isoformat()


def _market_query(
    columns: list[str],
    ticker: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> tuple[str, dict[str, Any]]:
    selected_columns = _selectable_columns(columns)
    column_types = _available_column_types()
    date_id_type = column_types.get("date_id", "")
    quoted_columns = ", ".join(f'"{column}"' for column in selected_columns)

    filters = []
    params: dict[str, Any] = {}

    if ticker:
        filters.append("ticker = :ticker")
        params["ticker"] = ticker
    if start_date:
        filters.append("date_id >= :start_date")
        params["start_date"] = _date_filter_value(start_date, date_id_type)
    if end_date:
        filters.append("date_id <= :end_date")
        params["end_date"] = _date_filter_value(end_date, date_id_type)

    where_clause = ""
    if filters:
        where_clause = "WHERE " + " AND ".join(filters)

    query = f"""
        SELECT {quoted_columns}
        FROM {MARKET_SCHEMA}.{MARKET_VIEW}
        {where_clause}
        ORDER BY date_id
    """

    return query, params


def _read_market_dataframe(
    columns: list[str],
    ticker: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> tuple[Any, Any]:
    pd = _get_pandas()
    query, params = _market_query(columns, ticker, start_date, end_date)

    try:
        with _get_engine().connect() as connection:
            result = connection.execute(text(query), params)
            rows = result.mappings().all()
    except SQLAlchemyError as exc:
        raise MarketDatabaseError("Unable to read market daily data.") from exc

    return pd.DataFrame(rows), pd


def get_market_tickers() -> list[str]:
    if "ticker" not in _available_columns():
        raise MarketDataError("Market view is missing required column: ticker")

    query = text(
        f"""
        SELECT DISTINCT ticker
        FROM {MARKET_SCHEMA}.{MARKET_VIEW}
        WHERE ticker IS NOT NULL
        ORDER BY ticker
        """
    )

    try:
        with _get_engine().connect() as connection:
            tickers = connection.execute(query).scalars()
            return [ticker for ticker in tickers]
    except SQLAlchemyError as exc:
        raise MarketDatabaseError("Unable to read market tickers.") from exc


def get_market_daily(
    ticker: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict[str, Any]]:
    dataframe, pd = _read_market_dataframe(MARKET_COLUMNS, ticker, start_date, end_date)

    if dataframe.empty:
        return []

    return _records_from_dataframe(dataframe, pd)


def get_market_summary(
    ticker: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict[str, Any]:
    dataframe, pd = _read_market_dataframe(SUMMARY_COLUMNS, ticker, start_date, end_date)

    if dataframe.empty:
        raise MarketNoDataError("No market data found for the requested filters.")

    if "close" not in dataframe.columns:
        raise MarketDataError("Market view is missing required column: close")

    dataframe = dataframe.copy()
    dataframe["close"] = pd.to_numeric(dataframe["close"], errors="coerce")
    dataframe = dataframe.dropna(subset=["close"])

    if dataframe.empty:
        raise MarketNoDataError("No usable close prices found for the requested filters.")

    daily_returns = dataframe["close"].pct_change().dropna()
    observations = int(len(dataframe))
    last_close = dataframe["close"].iloc[-1]
    previous_close = dataframe["close"].iloc[-2] if observations > 1 else None
    first_close = dataframe["close"].iloc[0]

    price_change = None
    price_change_pct = None
    if previous_close is not None and previous_close != 0:
        price_change = last_close - previous_close
        price_change_pct = (price_change / previous_close) * 100

    period_return_pct = None
    if first_close != 0:
        period_return_pct = ((last_close / first_close) - 1) * 100

    average_volume = None
    if "volume" in dataframe.columns:
        average_volume = pd.to_numeric(dataframe["volume"], errors="coerce").mean()

    period_high = None
    if "high" in dataframe.columns:
        period_high = pd.to_numeric(dataframe["high"], errors="coerce").max()

    period_low = None
    if "low" in dataframe.columns:
        period_low = pd.to_numeric(dataframe["low"], errors="coerce").min()

    annualized_volatility_pct = None
    if not daily_returns.empty:
        annualized_volatility_pct = daily_returns.std() * (252**0.5) * 100

    return {
        "ticker": ticker,
        "start_date": _json_safe(dataframe["date_id"].iloc[0], pd),
        "end_date": _json_safe(dataframe["date_id"].iloc[-1], pd),
        "observations": observations,
        "last_close": _json_safe(last_close, pd),
        "previous_close": _json_safe(previous_close, pd),
        "price_change": _json_safe(price_change, pd),
        "price_change_pct": _json_safe(price_change_pct, pd),
        "period_return_pct": _json_safe(period_return_pct, pd),
        "average_volume": _json_safe(average_volume, pd),
        "period_high": _json_safe(period_high, pd),
        "period_low": _json_safe(period_low, pd),
        "annualized_volatility_pct": _json_safe(annualized_volatility_pct, pd),
    }


def get_returns_distribution(
    ticker: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict[str, Any]]:
    dataframe, pd = _read_market_dataframe(
        ["date_id", "ticker", "close"],
        ticker,
        start_date,
        end_date,
    )

    if dataframe.empty:
        return []

    if "close" not in dataframe.columns:
        raise MarketDataError("Market view is missing required column: close")

    dataframe = dataframe.copy()
    dataframe["close"] = pd.to_numeric(dataframe["close"], errors="coerce")
    dataframe["daily_return_pct"] = dataframe["close"].pct_change() * 100
    dataframe = dataframe.dropna(subset=["daily_return_pct"])

    return _records_from_dataframe(
        dataframe[["date_id", "ticker", "daily_return_pct"]],
        pd,
    )
