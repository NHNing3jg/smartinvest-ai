from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.services.backtest_service import (
    BacktestDataError,
    BacktestDependencyError,
    BacktestFileNotFoundError,
    get_backtest_metrics,
    get_backtest_summary,
)


router = APIRouter(prefix="/backtest", tags=["backtest"])


@router.get("/summary")
def backtest_summary() -> list[dict[str, Any]]:
    try:
        return get_backtest_summary()
    except BacktestFileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "backtest_summary_not_found",
                "message": str(exc),
            },
        ) from exc
    except BacktestDependencyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "backtest_dependency_unavailable",
                "message": str(exc),
            },
        ) from exc
    except BacktestDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "backtest_summary_invalid",
                "message": str(exc),
            },
        ) from exc


@router.get("/metrics")
def backtest_metrics() -> list[dict[str, Any]]:
    try:
        return get_backtest_metrics()
    except BacktestFileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "backtest_metrics_not_found",
                "message": str(exc),
            },
        ) from exc
    except BacktestDependencyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "backtest_dependency_unavailable",
                "message": str(exc),
            },
        ) from exc
    except BacktestDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "backtest_metrics_invalid",
                "message": str(exc),
            },
        ) from exc
