"""Market search endpoints with rich filtering and role-aware responses."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from apps.api_gateway.dependencies import get_db_session, require_roles
from apps.core.models import Category, Item, User

router = APIRouter(prefix="/market", tags=["market"])


class SearchFilters(BaseModel):
    """Request payload for complex marketplace searches."""

    keyword: Optional[str] = None
    category_ids: List[int] = Field(default_factory=list)
    status: List[str] = Field(default_factory=list)
    price_min: Optional[float] = Field(default=None, ge=0)
    price_max: Optional[float] = Field(default=None, ge=0)
    sources: List[str] = Field(default_factory=list)
    seller_id: Optional[int] = None
    updated_from: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class SearchResponse(BaseModel):
    """Structured response for filtered results."""

    total: int
    items: List[Dict[str, Any]]


@router.get("/categories")
def list_categories(
    session: Session = Depends(get_db_session),
    _: User = Depends(require_roles("market_admin", "trader")),
) -> List[Dict[str, Any]]:
    """Return categories for building filter UI."""

    categories = session.execute(select(Category).order_by(Category.name)).scalars().all()
    return [{"id": category.id, "name": category.name} for category in categories]


@router.post("/search", response_model=SearchResponse)
def advanced_search(
    payload: SearchFilters,
    session: Session = Depends(get_db_session),
    current_user: User = Depends(require_roles("market_admin", "trader")),
) -> SearchResponse:
    """Execute a multi-criteria search with role-specific scoping."""

    base_query = select(Item, Category).join(Category, Item.category_id == Category.id, isouter=True)
    filters = []

    if payload.keyword:
        like_expr = f"%{payload.keyword.lower()}%"
        filters.append(or_(Item.title.ilike(like_expr), Item.description.ilike(like_expr)))

    if payload.category_ids:
        filters.append(Item.category_id.in_(payload.category_ids))

    if payload.status:
        filters.append(Item.status.in_(payload.status))

    if payload.price_min is not None:
        filters.append(Item.price >= payload.price_min)
    if payload.price_max is not None:
        filters.append(Item.price <= payload.price_max)

    if payload.updated_from is not None:
        filters.append(Item.updated_at >= payload.updated_from)

    user_roles = {role.name for role in current_user.roles}
    is_admin = "market_admin" in user_roles

    if not is_admin:
        permitted_status = set(payload.status or ["published", "active"])
        filters.append(Item.status.in_(permitted_status))
        filters.append(or_(Item.seller_id == current_user.id, Item.status == "active"))
    else:
        if payload.seller_id:
            filters.append(Item.seller_id == payload.seller_id)

    statement = base_query.where(and_(*filters)) if filters else base_query
    statement = statement.order_by(Item.updated_at.desc())

    count_statement = (base_query.where(and_(*filters)) if filters else base_query).with_only_columns(
        Item.id
    ).order_by(None)
    total_subquery = count_statement.subquery()
    total = session.execute(select(func.count()).select_from(total_subquery)).scalar_one()

    offset = (payload.page - 1) * payload.page_size
    paginated = session.execute(statement.offset(offset).limit(payload.page_size)).all()

    items: List[Dict[str, Any]] = []
    for item, category in paginated:
        items.append(
            {
                "id": item.id,
                "title": item.title,
                "price": float(item.price),
                "currency": item.currency,
                "status": item.status,
                "category": category.name if category else None,
                "seller_id": item.seller_id,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None,
            }
        )

    return SearchResponse(total=total, items=items)
