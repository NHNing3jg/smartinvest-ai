from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from app.services.performance_service import (
    PerformanceDatabaseError,
    PerformanceDataError,
    PerformanceNoDataError,
    PerformanceViewNotFoundError,
    get_performance_compare,
    get_performance_cum_return,
    get_performance_cumulative,
    get_performance_daily,
    get_performance_ranking,
    get_performance_summary,
    get_performance_tickers,
)


router = APIRouter(tags=["performance"])


def _handle_performance_error(exc: Exception) -> HTTPException:
    if isinstance(exc, PerformanceNoDataError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "performance_data_not_found",
                "message": str(exc),
            },
        )

    if isinstance(exc, PerformanceViewNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "performance_view_not_found",
                "message": str(exc),
            },
        )

    if isinstance(exc, PerformanceDatabaseError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "performance_database_unavailable",
                "message": str(exc),
            },
        )

    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "error": "performance_data_invalid",
            "message": str(exc),
        },
    )


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = value.strip()
    return cleaned or None


def _parse_tickers(value: str) -> list[str]:
    tickers = []
    seen = set()
    for item in value.split(","):
        ticker = item.strip()
        if ticker and ticker not in seen:
            tickers.append(ticker)
            seen.add(ticker)
    return tickers


@router.get("/tickers")
def performance_tickers() -> list[str]:
    try:
        return get_performance_tickers()
    except (
        PerformanceDatabaseError,
        PerformanceDataError,
        PerformanceViewNotFoundError,
    ) as exc:
        raise _handle_performance_error(exc) from exc


@router.get("/daily")
def performance_daily(
    ticker: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = Query(1000, ge=1, le=10000),
) -> list[dict[str, Any]]:
    try:
        return get_performance_daily(
            ticker=_normalize_optional_text(ticker),
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
    except (
        PerformanceDatabaseError,
        PerformanceDataError,
        PerformanceNoDataError,
        PerformanceViewNotFoundError,
    ) as exc:
        raise _handle_performance_error(exc) from exc


@router.get("/cumulative")
def performance_cumulative(
    ticker: str = Query(..., min_length=1),
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict[str, Any]]:
    try:
        return get_performance_cumulative(
            ticker=ticker.strip(),
            start_date=start_date,
            end_date=end_date,
        )
    except (
        PerformanceDatabaseError,
        PerformanceDataError,
        PerformanceNoDataError,
        PerformanceViewNotFoundError,
    ) as exc:
        raise _handle_performance_error(exc) from exc


@router.get("/summary")
def performance_summary(
    ticker: str = Query(..., min_length=1),
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict[str, Any]:
    try:
        return get_performance_summary(
            ticker=ticker.strip(),
            start_date=start_date,
            end_date=end_date,
        )
    except (
        PerformanceDatabaseError,
        PerformanceDataError,
        PerformanceNoDataError,
        PerformanceViewNotFoundError,
    ) as exc:
        raise _handle_performance_error(exc) from exc


@router.get("/ranking")
def performance_ranking(
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = Query(5, ge=1, le=100),
) -> dict[str, list[dict[str, Any]]]:
    try:
        return get_performance_ranking(
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
    except (
        PerformanceDatabaseError,
        PerformanceDataError,
        PerformanceViewNotFoundError,
    ) as exc:
        raise _handle_performance_error(exc) from exc


@router.get("/compare")
def performance_compare(
    tickers: str = Query(..., min_length=1),
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict[str, Any]]:
    try:
        parsed_tickers = _parse_tickers(tickers)
        if not parsed_tickers:
            raise PerformanceDataError("At least one ticker is required.")
        return get_performance_compare(
            tickers=parsed_tickers,
            start_date=start_date,
            end_date=end_date,
        )
    except (
        PerformanceDatabaseError,
        PerformanceDataError,
        PerformanceNoDataError,
        PerformanceViewNotFoundError,
    ) as exc:
        raise _handle_performance_error(exc) from exc


@router.get("/cum-return")
def performance_cum_return(
    limit: int = Query(50, ge=1, le=1000),
) -> list[dict[str, Any]]:
    try:
        return get_performance_cum_return(limit=limit)
    except (
        PerformanceDatabaseError,
        PerformanceDataError,
        PerformanceViewNotFoundError,
    ) as exc:
        raise _handle_performance_error(exc) from exc
