"""Inventory service router definitions."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from apps.core.database import db_manager
from apps.core.models import Category, Item

router = APIRouter(prefix="/inventory", tags=["inventory"])


class ItemPayload(BaseModel):
    """Payload describing item creation or update."""

    seller_id: int = Field(..., gt=0)
    title: str
    category_id: int
    price: float
    description: str | None = None
    currency: str = "CNY"


@router.get("/items")
def list_items(limit: int = 20) -> list[dict[str, str | float | int | None]]:
    """Return latest listings from the primary database."""

    with db_manager.session_scope("mysql") as session:
        items = (
            session.execute(
                select(Item).order_by(Item.created_at.desc()).limit(limit)
            )
            .scalars()
            .all()
        )

    return [
        {
            "id": item.id,
            "title": item.title,
            "price": float(item.price),
            "currency": item.currency,
            "status": item.status,
            "category_id": item.category_id,
        }
        for item in items
    ]


@router.post("/items", status_code=201)
def create_item(payload: ItemPayload) -> dict[str, str | int | float]:
    """Persist a new listing."""

    with db_manager.session_scope("mysql") as session:
        category = session.get(Category, payload.category_id)
        if category is None:
            raise HTTPException(status_code=400, detail="Category not found")
        item = Item(
            seller_id=payload.seller_id,
            category_id=payload.category_id,
            title=payload.title,
            description=payload.description or "",
            price=payload.price,
            currency=payload.currency,
            status="draft",
        )
        session.add(item)
        session.flush()

        return {
            "id": item.id,
            "title": item.title,
            "status": item.status,
            "price": float(item.price),
        }
