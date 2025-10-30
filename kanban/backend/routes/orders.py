from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models
from ..schemas import OrderCreate, OrderOut
from ..auth import get_current_user
from ..db import get_db

router = APIRouter()

@router.get("/", response_model=List[OrderOut])
def get_orders(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    orders = db.query(models.Order).filter(models.Order.user_id == current_user.id).all()
    return orders

@router.post("/", response_model=OrderOut)
def create_order(order: OrderCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    total_cents = 0
    new_order = models.Order(user_id=current_user.id, total_cents=0)
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    for item in order.items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        total_cents += product.price_cents * item.quantity
        order_item = models.OrderItem(order_id=new_order.id, product_id=item.product_id, quantity=item.quantity, price_cents=product.price_cents)
        db.add(order_item)

    new_order.total_cents = total_cents
    db.commit()
    return new_order
