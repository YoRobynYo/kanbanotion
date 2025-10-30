import secrets
from sqlalchemy.orm import Session
from .. import models

def generate_key() -> str:
    return "-".join(secrets.token_hex(4) for _ in range(3)).upper()

def issue_licenses(db: Session, order: models.Order):
    for item in order.items:
        product = item.product
        if product.is_subscription:
            continue
        for _ in range(item.qty):
            lic = models.License(
                order_id=order.id,
                user_id=order.user_id,
                product_id=product.id,
                key=generate_key(),
                status="active"
            )
            db.add(lic)
    db.commit()
