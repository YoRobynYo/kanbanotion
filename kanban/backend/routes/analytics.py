from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..db import get_db

router = APIRouter()

@router.get("/analytics/summary")
def summary(db: Session = Depends(get_db)):
    row = db.execute(text("""
        SELECT
          COUNT(*) FILTER (WHERE status='paid') as orders,
          COALESCE(SUM(total_cents) FILTER (WHERE status='paid'),0) as revenue_cents,
          COALESCE(SUM(tax_cents) FILTER (WHERE status='paid'),0) as tax_cents
        FROM orders
    """)).mappings().first()
    return row or {}
