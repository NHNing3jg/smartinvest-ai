from datetime import date
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from app.services.macro_service import (
    MacroDatabaseError,
    MacroDataError,
    MacroNoDataError,
    MacroViewNotFoundError,
    get_macro_daily,
    get_macro_series,
    get_macro_summary,
    get_macro_yoy,
)


router = APIRouter(tags=["macro"])


def _handle_macro_error(exc: Exception) -> HTTPException:
    if isinstance(exc, MacroNoDataError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "macro_data_not_found",
                "message": str(exc),
            },
        )

    if isinstance(exc, MacroViewNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "macro_view_not_found",
                "message": str(exc),
            },
        )

    if isinstance(exc, MacroDatabaseError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "macro_database_unavailable",
                "message": str(exc),
            },
        )

    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "error": "macro_data_invalid",
            "message": str(exc),
        },
    )


@router.get("/series")
def macro_series() -> list[dict[str, Any]]:
    try:
        return get_macro_series()
    except (
        MacroDatabaseError,
        MacroDataError,
        MacroViewNotFoundError,
    ) as exc:
        raise _handle_macro_error(exc) from exc


@router.get("/daily")
def macro_daily(
    series_id: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict[str, Any]]:
    try:
        return get_macro_daily(series_id, start_date, end_date)
    except (
        MacroDatabaseError,
        MacroDataError,
        MacroViewNotFoundError,
    ) as exc:
        raise _handle_macro_error(exc) from exc


@router.get("/summary")
def macro_summary(
    series_id: str = Query(..., min_length=1),
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict[str, Any]:
    try:
        return get_macro_summary(series_id, start_date, end_date)
    except (
        MacroDatabaseError,
        MacroDataError,
        MacroNoDataError,
        MacroViewNotFoundError,
    ) as exc:
        raise _handle_macro_error(exc) from exc


@router.get("/yoy")
def macro_yoy(
    series_id: str = Query(..., min_length=1),
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict[str, Any]]:
    try:
        return get_macro_yoy(series_id, start_date, end_date)
    except (
        MacroDatabaseError,
        MacroDataError,
        MacroViewNotFoundError,
    ) as exc:
        raise _handle_macro_error(exc) from exc
