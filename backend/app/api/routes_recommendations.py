from fastapi import APIRouter, HTTPException, status

from app.services.recommendation_service import (
    RecommendationDataError,
    RecommendationDependencyError,
    RecommendationFileNotFoundError,
    get_latest_recommendations,
    get_recommendations_summary,
)


router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/latest")
def latest_recommendations() -> list[dict]:
    try:
        return get_latest_recommendations()
    except RecommendationFileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "recommendations_not_found",
                "message": str(exc),
            },
        ) from exc
    except RecommendationDependencyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "recommendations_dependency_unavailable",
                "message": str(exc),
            },
        ) from exc
    except RecommendationDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "recommendations_invalid",
                "message": str(exc),
            },
        ) from exc


@router.get("/summary")
def recommendations_summary() -> dict:
    try:
        return get_recommendations_summary()
    except RecommendationFileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "recommendations_not_found",
                "message": str(exc),
            },
        ) from exc
    except RecommendationDependencyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "recommendations_dependency_unavailable",
                "message": str(exc),
            },
        ) from exc
    except RecommendationDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "recommendations_invalid",
                "message": str(exc),
            },
        ) from exc
