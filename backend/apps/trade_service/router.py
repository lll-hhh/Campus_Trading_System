"""Trade service router definitions."""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/trade", tags=["trade"])


class OfferPayload(BaseModel):
    """Offer creation payload."""

    item_id: int
    buyer_id: int
    price: float


@router.get("/offers")
def list_offers() -> list[dict[str, str]]:
    """Return mock offers."""

    return [{"status": "open", "item_id": 1}]


@router.post("/offers")
def create_offer(payload: OfferPayload) -> dict[str, str | float]:
    """Create an offer placeholder."""

    return {"status": "created", "price": payload.price}
