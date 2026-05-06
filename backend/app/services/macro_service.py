from datetime import date
from decimal import Decimal
from statistics import stdev
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError


MACRO_SCHEMA = "smartinvest"
MACRO_VIEW = "v_macro_daily"
MACRO_COLUMNS = ("date_id", "series_id", "label", "value")


class MacroDatabaseError(RuntimeError):
    """Raised when macro data cannot be read from PostgreSQL."""


class MacroDataError(ValueError):
    """Raised when macro data cannot satisfy the API contract."""


class MacroNoDataError(ValueError):
    """Raised when no macro data exists for the requested filters."""


class MacroViewNotFoundError(ValueError):
    """Raised when the macro daily view is not available."""


def _get_engine() -> Any:
    try:
        from app.core.database import engine
    except Exception as exc:
        raise MacroDatabaseError("Macro database configuration is invalid.") from exc

    return engine


def _json_safe(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _record_from_row(row: Any) -> dict[str, Any]:
    return {key: _json_safe(value) for key, value in row.items()}


def _validate_view() -> None:
    query = text(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = :schema_name
          AND table_name = :view_name
        """
    )

    try:
        with _get_engine().connect() as connection:
            columns = {
                row["column_name"]
                for row in connection.execute(
                    query,
                    {"schema_name": MACRO_SCHEMA, "view_name": MACRO_VIEW},
                ).mappings()
            }
    except SQLAlchemyError as exc:
        raise MacroDatabaseError("Unable to read macro view metadata.") from exc

    if not columns:
        raise MacroViewNotFoundError(
            f"Macro view {MACRO_SCHEMA}.{MACRO_VIEW} was not found."
        )

    missing_columns = [column for column in MACRO_COLUMNS if column not in columns]
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise MacroDataError(f"Macro view is missing required columns: {missing}")


def _date_params(
    start_date: date | None,
    end_date: date | None,
) -> dict[str, str | None]:
    return {
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None,
    }


def get_macro_series() -> list[dict[str, Any]]:
    _validate_view()

    query = text(
        f"""
        SELECT series_id, COALESCE(MAX(label), series_id) AS label
        FROM {MACRO_SCHEMA}.{MACRO_VIEW}
        WHERE series_id IS NOT NULL
        GROUP BY series_id
        ORDER BY series_id
        """
    )

    try:
        with _get_engine().connect() as connection:
            rows = connection.execute(query).mappings().all()
    except SQLAlchemyError as exc:
        raise MacroDatabaseError("Unable to read macro series.") from exc

    return [_record_from_row(row) for row in rows]


def get_macro_daily(
    series_id: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict[str, Any]]:
    _validate_view()

    filters = []
    params: dict[str, Any] = {}

    if series_id:
        filters.append("series_id = :series_id")
        params["series_id"] = series_id
    if start_date:
        filters.append("date_id >= :start_date")
        params["start_date"] = start_date
    if end_date:
        filters.append("date_id <= :end_date")
        params["end_date"] = end_date

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    query = text(
        f"""
        SELECT date_id, series_id, label, value
        FROM {MACRO_SCHEMA}.{MACRO_VIEW}
        {where_clause}
        ORDER BY date_id
        """
    )

    try:
        with _get_engine().connect() as connection:
            rows = connection.execute(query, params).mappings().all()
    except SQLAlchemyError as exc:
        raise MacroDatabaseError("Unable to read macro daily data.") from exc

    return [_record_from_row(row) for row in rows]


def get_macro_summary(
    series_id: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict[str, Any]:
    rows = get_macro_daily(series_id, start_date, end_date)
    if not rows:
        raise MacroNoDataError(f"No macro data found for series_id '{series_id}'.")

    values = [row["value"] for row in rows if row["value"] is not None]
    if not values:
        raise MacroNoDataError(
            f"No numeric macro observations found for series_id '{series_id}'."
        )

    latest_value = values[-1]
    previous_value = values[-2] if len(values) > 1 else None
    first_value = values[0]

    absolute_change = None
    percent_change = None
    if previous_value is not None:
        absolute_change = latest_value - previous_value
        if previous_value != 0:
            percent_change = (absolute_change / previous_value) * 100

    period_change = latest_value - first_value
    period_change_pct = None
    if first_value != 0:
        period_change_pct = (period_change / first_value) * 100

    return {
        "series_id": rows[-1]["series_id"],
        "label": rows[-1]["label"],
        "start_date": rows[0]["date_id"],
        "end_date": rows[-1]["date_id"],
        "observations": len(rows),
        "latest_value": latest_value,
        "previous_value": previous_value,
        "absolute_change": absolute_change,
        "percent_change": percent_change,
        "period_change": period_change,
        "period_change_pct": period_change_pct,
        "period_mean": sum(values) / len(values),
        "period_std": stdev(values) if len(values) > 1 else None,
        "period_min": min(values),
        "period_max": max(values),
    }


def get_macro_yoy(
    series_id: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict[str, Any]]:
    _validate_view()

    params: dict[str, Any] = {"series_id": series_id}
    params.update(_date_params(start_date, end_date))

    query = text(
        f"""
        WITH yoy AS (
            SELECT
                current_row.date_id,
                current_row.series_id,
                current_row.label,
                current_row.value,
                CASE
                    WHEN previous_row.value IS NULL OR previous_row.value = 0 THEN NULL
                    ELSE ((current_row.value - previous_row.value) / previous_row.value) * 100
                END AS yoy_change_pct
            FROM {MACRO_SCHEMA}.{MACRO_VIEW} AS current_row
            LEFT JOIN {MACRO_SCHEMA}.{MACRO_VIEW} AS previous_row
              ON previous_row.series_id = current_row.series_id
             AND previous_row.date_id = current_row.date_id - INTERVAL '1 year'
            WHERE current_row.series_id = :series_id
        )
        SELECT date_id, series_id, label, value, yoy_change_pct
        FROM yoy
        WHERE (:start_date IS NULL OR date_id >= CAST(:start_date AS date))
          AND (:end_date IS NULL OR date_id <= CAST(:end_date AS date))
        ORDER BY date_id
        """
    )

    try:
        with _get_engine().connect() as connection:
            rows = connection.execute(query, params).mappings().all()
    except SQLAlchemyError as exc:
        raise MacroDatabaseError("Unable to read macro year-over-year data.") from exc

    return [_record_from_row(row) for row in rows]
