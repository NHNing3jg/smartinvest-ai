from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from app.services.market_service import (
    MarketDatabaseError,
    MarketDataError,
    MarketNoDataError,
    MarketViewNotFoundError,
    get_market_daily,
    get_market_summary,
    get_market_tickers,
    get_returns_distribution,
)


router = APIRouter(tags=["market"])


def _handle_market_error(exc: Exception) -> HTTPException:
    if isinstance(exc, MarketNoDataError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "market_data_not_found",
                "message": str(exc),
            },
        )

    if isinstance(exc, MarketViewNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "market_view_not_found",
                "message": str(exc),
            },
        )

    if isinstance(exc, MarketDatabaseError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "market_database_unavailable",
                "message": str(exc),
            },
        )

    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "error": "market_data_invalid",
            "message": str(exc),
        },
    )


@router.get("/tickers")
def market_tickers() -> list[str]:
    try:
        return get_market_tickers()
    except (MarketDatabaseError, MarketDataError, MarketViewNotFoundError) as exc:
        raise _handle_market_error(exc) from exc


@router.get("/daily")
def market_daily(
    ticker: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict[str, Any]:
    try:
        data = get_market_daily(ticker, start_date, end_date)
        return {"data": data}
    except (MarketDatabaseError, MarketDataError, MarketViewNotFoundError) as exc:
        raise _handle_market_error(exc) from exc


@router.get("/summary")
def market_summary(
    ticker: str = Query(..., min_length=1),
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict[str, Any]:
    try:
        return get_market_summary(ticker, start_date, end_date)
    except (
        MarketDatabaseError,
        MarketDataError,
        MarketNoDataError,
        MarketViewNotFoundError,
    ) as exc:
        raise _handle_market_error(exc) from exc


@router.get("/returns-distribution")
def market_returns_distribution(
    ticker: str = Query(..., min_length=1),
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict[str, Any]:
    try:
        data = get_returns_distribution(ticker, start_date, end_date)
        return {"data": data}
    except (MarketDatabaseError, MarketDataError, MarketViewNotFoundError) as exc:
        raise _handle_market_error(exc) from exc
