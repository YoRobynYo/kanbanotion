import stripe
from sqlalchemy.orm import Session
from fastapi import HTTPException
from ..config import settings
from .. import models
from .license_svc import issue_licenses
from .email_svc import send_order_confirmation

stripe.api_key = settings.STRIPE_SECRET_KEY

def create_checkout_session(items: list[dict], success_url: str, cancel_url: str, customer_email: str | None = None) -> str:
    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=items,
            success_url=success_url,
            cancel_url=cancel_url,
            automatic_tax={"enabled": True},
            allow_promotion_codes=True,
            customer_email=customer_email
        )
        return session.url
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def fulfill_checkout_session(db: Session, session_obj: dict):
    sess_id = session_obj.get("id")
    exists = db.query(models.Order).filter(models.Order.stripe_session_id == sess_id).first()
    if exists:
        return exists

    email = (session_obj.get("customer_details") or {}).get("email") or session_obj.get("customer_email")

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        user = models.User(email=email, password_hash="!stripe_customer", role="customer")
        db.add(user)
        db.flush()

    line_items = stripe.checkout.Session.list_line_items(sess_id)
    currency = (session_obj.get("currency") or "usd").lower()
    total_cents = int(session_obj.get("amount_total") or 0)
    tax_cents = int((session_obj.get("total_details") or {}).get("amount_tax") or 0)
    payment_intent = session_obj.get("payment_intent")

    order = models.Order(
        user_id=user.id,
        stripe_session_id=sess_id,
        stripe_payment_intent=payment_intent,
        total_cents=total_cents,
        tax_cents=tax_cents,
        currency=currency,
        status="paid"
    )
    db.add(order)
    db.flush()

    price_ids = []
    for li in line_items.auto_paging_iter():
        price_id = li.price.id if hasattr(li, "price") and li.price else li.get("price", {}).get("id")
        qty = li.quantity or 1
        price_ids.append((price_id, qty))

    for price_id, qty in price_ids:
        product = db.query(models.Product).filter(models.Product.stripe_price_id == price_id).first()
        if not product:
            continue
        db.add(models.OrderItem(
            order_id=order.id,
            product_id=product.id,
            unit_price_cents=product.price_cents,
            qty=qty
        ))

    db.commit()
    db.refresh(order)

    issue_licenses(db, order)
    send_order_confirmation(user.email, order.id, total_cents, currency)
    return order
