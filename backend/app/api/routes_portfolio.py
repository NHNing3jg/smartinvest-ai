from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.services.portfolio_service import (
    PortfolioDataError,
    PortfolioDependencyError,
    PortfolioFileNotFoundError,
    get_portfolio_allocation,
    get_portfolio_summary,
)


router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/allocation")
def portfolio_allocation() -> list[dict[str, Any]]:
    try:
        return get_portfolio_allocation()
    except PortfolioFileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "portfolio_allocation_not_found",
                "message": str(exc),
            },
        ) from exc
    except PortfolioDependencyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "portfolio_dependency_unavailable",
                "message": str(exc),
            },
        ) from exc
    except PortfolioDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "portfolio_allocation_invalid",
                "message": str(exc),
            },
        ) from exc


@router.get("/summary")
def portfolio_summary() -> dict[str, Any]:
    try:
        return get_portfolio_summary()
    except PortfolioFileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "portfolio_summary_not_found",
                "message": str(exc),
            },
        ) from exc
    except PortfolioDependencyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "portfolio_dependency_unavailable",
                "message": str(exc),
            },
        ) from exc
    except PortfolioDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "portfolio_summary_invalid",
                "message": str(exc),
            },
        ) from exc
