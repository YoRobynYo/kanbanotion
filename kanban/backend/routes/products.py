from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models
from ..schemas import ProductOut
from ..db import get_db

router = APIRouter()

@router.get("/", response_model=List[ProductOut])
def get_products(db: Session = Depends(get_db)):
    products = db.query(models.Product).filter(models.Product.active == True).all()
    return products
