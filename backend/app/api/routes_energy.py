from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from app.services.energy_service import (
    EnergyDatabaseError,
    EnergyDataError,
    EnergyNoDataError,
    EnergyViewNotFoundError,
    get_energy_assets,
    get_energy_merged,
    get_energy_rolling_correlation,
    get_energy_scatter,
    get_energy_summary,
    get_oil_daily,
    get_oil_series,
)


router = APIRouter(tags=["energy"])


def _handle_energy_error(exc: Exception) -> HTTPException:
    if isinstance(exc, EnergyNoDataError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "energy_data_not_found",
                "message": str(exc),
            },
        )

    if isinstance(exc, EnergyViewNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "energy_view_not_found",
                "message": str(exc),
            },
        )

    if isinstance(exc, EnergyDatabaseError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "energy_database_unavailable",
                "message": str(exc),
            },
        )

    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "error": "energy_data_invalid",
            "message": str(exc),
        },
    )


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = value.strip()
    return cleaned or None


def _normalize_required_text(value: str, label: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise EnergyDataError(f"{label} is required.")
    return cleaned


@router.get("/oil-series")
def energy_oil_series() -> list[str]:
    try:
        return get_oil_series()
    except (EnergyDatabaseError, EnergyDataError, EnergyViewNotFoundError) as exc:
        raise _handle_energy_error(exc) from exc


@router.get("/assets")
def energy_assets() -> list[str]:
    try:
        return get_energy_assets()
    except (EnergyDatabaseError, EnergyDataError, EnergyViewNotFoundError) as exc:
        raise _handle_energy_error(exc) from exc


@router.get("/oil-daily")
def energy_oil_daily(
    oil_ticker: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = Query(1000, ge=1, le=10000),
) -> list[dict[str, Any]]:
    try:
        return get_oil_daily(
            oil_ticker=_normalize_optional_text(oil_ticker),
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
    except (
        EnergyDatabaseError,
        EnergyDataError,
        EnergyNoDataError,
        EnergyViewNotFoundError,
    ) as exc:
        raise _handle_energy_error(exc) from exc


@router.get("/summary")
def energy_summary(
    oil_ticker: str = Query(..., min_length=1),
    asset_ticker: str = Query(..., min_length=1),
    start_date: date | None = None,
    end_date: date | None = None,
    corr_window: int = Query(30, ge=1, le=1000),
) -> dict[str, Any]:
    try:
        return get_energy_summary(
            oil_ticker=_normalize_required_text(oil_ticker, "oil_ticker"),
            asset_ticker=_normalize_required_text(asset_ticker, "asset_ticker"),
            start_date=start_date,
            end_date=end_date,
            corr_window=corr_window,
        )
    except (
        EnergyDatabaseError,
        EnergyDataError,
        EnergyNoDataError,
        EnergyViewNotFoundError,
    ) as exc:
        raise _handle_energy_error(exc) from exc


@router.get("/merged")
def energy_merged(
    oil_ticker: str = Query(..., min_length=1),
    asset_ticker: str = Query(..., min_length=1),
    start_date: date | None = None,
    end_date: date | None = None,
    corr_window: int = Query(30, ge=1, le=1000),
    limit: int = Query(1000, ge=1, le=10000),
) -> list[dict[str, Any]]:
    try:
        return get_energy_merged(
            oil_ticker=_normalize_required_text(oil_ticker, "oil_ticker"),
            asset_ticker=_normalize_required_text(asset_ticker, "asset_ticker"),
            start_date=start_date,
            end_date=end_date,
            corr_window=corr_window,
            limit=limit,
        )
    except (
        EnergyDatabaseError,
        EnergyDataError,
        EnergyNoDataError,
        EnergyViewNotFoundError,
    ) as exc:
        raise _handle_energy_error(exc) from exc


@router.get("/rolling-correlation")
def energy_rolling_correlation(
    oil_ticker: str = Query(..., min_length=1),
    asset_ticker: str = Query(..., min_length=1),
    start_date: date | None = None,
    end_date: date | None = None,
    corr_window: int = Query(30, ge=1, le=1000),
) -> list[dict[str, Any]]:
    try:
        return get_energy_rolling_correlation(
            oil_ticker=_normalize_required_text(oil_ticker, "oil_ticker"),
            asset_ticker=_normalize_required_text(asset_ticker, "asset_ticker"),
            start_date=start_date,
            end_date=end_date,
            corr_window=corr_window,
        )
    except (
        EnergyDatabaseError,
        EnergyDataError,
        EnergyNoDataError,
        EnergyViewNotFoundError,
    ) as exc:
        raise _handle_energy_error(exc) from exc


@router.get("/scatter")
def energy_scatter(
    oil_ticker: str = Query(..., min_length=1),
    asset_ticker: str = Query(..., min_length=1),
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict[str, Any]:
    try:
        return get_energy_scatter(
            oil_ticker=_normalize_required_text(oil_ticker, "oil_ticker"),
            asset_ticker=_normalize_required_text(asset_ticker, "asset_ticker"),
            start_date=start_date,
            end_date=end_date,
        )
    except (
        EnergyDatabaseError,
        EnergyDataError,
        EnergyNoDataError,
        EnergyViewNotFoundError,
    ) as exc:
        raise _handle_energy_error(exc) from exc
