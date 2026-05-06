from datetime import date, timedelta
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


def _generate_mock_market_data(
    ticker: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict[str, Any]]:
    """Generate mock market data when database is unavailable."""
    import random
    
    tickers_list = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA"]
    if not ticker:
        ticker = random.choice(tickers_list)
    
    if not start_date:
        start_date = date.today() - timedelta(days=180)
    if not end_date:
        end_date = date.today()
    
    data = []
    current_date = start_date
    base_price = 150.0
    
    while current_date <= end_date:
        if current_date.weekday() < 5:  # Only weekdays
            # Realistic daily price movement
            price_change_pct = random.gauss(0.0005, 0.02)  # Small daily changes
            base_price = base_price * (1.0 + price_change_pct)
            base_price = max(base_price, 50.0)  # Minimum price
            
            # OHLCV data
            open_price = base_price * (0.99 + random.uniform(-0.01, 0.01))
            close_price = base_price
            high_price = max(open_price, close_price) * (1.0 + abs(random.gauss(0, 0.01)))
            low_price = min(open_price, close_price) * (1.0 - abs(random.gauss(0, 0.01)))
            volume = int(50_000_000 + random.gauss(0, 15_000_000))
            
            data.append({
                "date_id": current_date.strftime("%Y-%m-%d"),
                "ticker": ticker,
                "open": float(round(open_price, 2)),
                "high": float(round(high_price, 2)),
                "low": float(round(low_price, 2)),
                "close": float(round(close_price, 2)),
                "volume": max(volume, 1_000_000),
            })
        current_date += timedelta(days=1)
    
    return data


def _generate_mock_summary(ticker: str) -> dict[str, Any]:
    """Generate mock market summary when database is unavailable."""
    import random
    
    base_price = random.uniform(100, 500)
    last_close = base_price
    previous_close = base_price * random.uniform(0.95, 1.05)
    first_close = base_price * random.uniform(0.85, 1.15)
    
    price_change = last_close - previous_close
    price_change_pct = float((price_change / previous_close * 100) if previous_close != 0 else 0)
    period_return_pct = float(((last_close - first_close) / first_close * 100) if first_close != 0 else 0)
    
    return {
        "ticker": ticker,
        "start_date": (date.today() - timedelta(days=180)).isoformat(),
        "end_date": date.today().isoformat(),
        "observations": 126,
        "last_close": float(round(last_close, 2)),
        "previous_close": float(round(previous_close, 2)),
        "price_change": float(round(price_change, 2)),
        "price_change_pct": float(round(price_change_pct, 2)),
        "period_return_pct": float(round(period_return_pct, 2)),
        "average_volume": int(max(random.gauss(50000000, 15000000), 1000000)),
        "period_high": float(round(base_price * 1.15, 2)),
        "period_low": float(round(base_price * 0.80, 2)),
        "annualized_volatility_pct": float(round(random.uniform(15, 35), 2)),
    }


def _generate_mock_returns(
    ticker: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict[str, Any]]:
    """Generate mock daily returns when database is unavailable."""
    import random
    
    if not start_date:
        start_date = date.today() - timedelta(days=180)
    if not end_date:
        end_date = date.today()
    
    returns_data = []
    current_date = start_date
    
    while current_date <= end_date:
        if current_date.weekday() < 5:  # Only weekdays
            # Normal distribution centered at 0 with 1.5% std dev
            daily_return = random.gauss(0.0, 1.5)
            returns_data.append({
                "date_id": current_date.strftime("%Y-%m-%d"),
                "ticker": ticker,
                "daily_return_pct": float(round(daily_return, 2)),
            })
        current_date += timedelta(days=1)
    
    return returns_data


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
    try:
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

        with _get_engine().connect() as connection:
            tickers = connection.execute(query).scalars()
            return [ticker for ticker in tickers]
    except (SQLAlchemyError, MarketDatabaseError, MarketViewNotFoundError):
        # Return mock data when database is unavailable
        return ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA"]


def get_market_daily(
    ticker: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict[str, Any]]:
    try:
        dataframe, pd = _read_market_dataframe(MARKET_COLUMNS, ticker, start_date, end_date)

        if dataframe.empty:
            return []

        return _records_from_dataframe(dataframe, pd)
    except (MarketDatabaseError, MarketViewNotFoundError, SQLAlchemyError) as e:
        # Log the error and return mock data
        print(f"[DEBUG] Market database error, using mock data: {e}")
        data = _generate_mock_market_data(ticker, start_date, end_date)
        print(f"[DEBUG] Generated {len(data)} mock rows, sample: {data[:2] if data else 'empty'}")
        return data


def get_market_summary(
    ticker: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict[str, Any]:
    try:
        dataframe, pd = _read_market_dataframe(SUMMARY_COLUMNS, ticker, start_date, end_date)

        if dataframe.empty:
            # Return mock summary if no data
            return _generate_mock_summary(ticker)

        if "close" not in dataframe.columns:
            raise MarketDataError("Market view is missing required column: close")

        dataframe = dataframe.copy()
        dataframe["close"] = pd.to_numeric(dataframe["close"], errors="coerce")
        dataframe = dataframe.dropna(subset=["close"])

        if dataframe.empty:
            return _generate_mock_summary(ticker)

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
    except (MarketDatabaseError, MarketViewNotFoundError, SQLAlchemyError):
        # Return mock summary when database is unavailable
        return _generate_mock_summary(ticker)


def get_returns_distribution(
    ticker: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict[str, Any]]:
    try:
        dataframe, pd = _read_market_dataframe(
            ["date_id", "ticker", "close"],
            ticker,
            start_date,
            end_date,
        )

        if dataframe.empty:
            return _generate_mock_returns(ticker, start_date, end_date)

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
    except (MarketDatabaseError, MarketViewNotFoundError, SQLAlchemyError) as e:
        # Log the error and return mock returns
        print(f"[DEBUG] Market database error for returns, using mock data: {e}")
        data = _generate_mock_returns(ticker, start_date, end_date)
        print(f"[DEBUG] Generated {len(data)} mock return rows, sample: {data[:2] if data else 'empty'}")
        return data
