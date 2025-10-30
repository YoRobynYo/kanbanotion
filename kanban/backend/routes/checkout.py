from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models
from ..auth import get_current_user
from ..db import get_db

router = APIRouter()

@router.post("/create-session")
def create_checkout_session(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Placeholder: Integrate with Stripe to create session
    raise HTTPException(status_code=501, detail="Not implemented yet")
