"""AI service router definitions."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from apps.services.ai_pricing import PriceRecommendationService, get_default_price_service

router = APIRouter(prefix="/ai", tags=["ai"])


class PricingRequest(BaseModel):
    """Payload for requesting price suggestion."""

    category_id: int
    condition_score: float
    original_price: float
    usage_months: int


class PricingResponse(BaseModel):
    """AI pricing result."""

    suggested_price: float


@router.post("/pricing", response_model=PricingResponse)
def pricing(request: PricingRequest) -> PricingResponse:
    """Return KNN-based price suggestion."""

    service: PriceRecommendationService = get_default_price_service()
    if not service._is_fitted:  # pylint: disable=protected-access
        raise HTTPException(status_code=503, detail="Model not ready")

    features = [
        float(request.category_id),
        request.condition_score,
        request.original_price,
        float(request.usage_months),
    ]
    return PricingResponse(suggested_price=service.suggest_price(features))
