from fastapi import APIRouter, Request, HTTPException, Depends
import stripe
from ..config import settings
from ..db import get_db
from sqlalchemy.orm import Session
from ..services.stripe_svc import fulfill_checkout_session

router = APIRouter()

@router.post("/stripe/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(payload, sig, settings.STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        fulfill_checkout_session(db, session)
    return {"received": True}
