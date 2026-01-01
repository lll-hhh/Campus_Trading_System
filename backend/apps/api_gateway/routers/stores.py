from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Any
from apps.api_gateway.dependencies import get_db_session
from apps.core.models.inventory import Store
from pydantic import BaseModel

router = APIRouter(prefix="/stores", tags=["Stores"])

class StoreSchema(BaseModel):
    id: int
    name: str
    address: str
    phone: str | None
    image_url: str | None
    description: str | None
    is_active: bool

    class Config:
        from_attributes = True

@router.get("/", response_model=List[StoreSchema])
def get_stores(db: Session = Depends(get_db_session)):
    """获取所有门店信息"""
    return db.query(Store).filter(Store.is_active == True).all()

@router.get("/{store_id}", response_model=StoreSchema)
def get_store(store_id: int, db: Session = Depends(get_db_session)):
    """获取特定门店详情"""
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    return store
