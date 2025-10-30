from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON, func, UniqueConstraint
from sqlalchemy.orm import relationship
from .db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="customer")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    orders = relationship("Order", back_populates="user")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    sku = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, default="")
    price_cents = Column(Integer, nullable=False)
    currency = Column(String(10), default="usd")
    stripe_price_id = Column(String(128), nullable=True)
    active = Column(Boolean, default=True)
    is_subscription = Column(Boolean, default=False)
    interval = Column(String(20), nullable=True)
    features_json = Column(JSON, default=[])
    media_urls_json = Column(JSON, default=[])

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    stripe_session_id = Column(String(128), unique=True, index=True)
    stripe_payment_intent = Column(String(128), index=True)
    total_cents = Column(Integer, default=0)
    tax_cents = Column(Integer, default=0)
    currency = Column(String(10), default="usd")
    status = Column(String(20), default="paid")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")
    licenses = relationship("License", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), index=True, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), index=True, nullable=False)
    unit_price_cents = Column(Integer, nullable=False)
    qty = Column(Integer, default=1)
    order = relationship("Order", back_populates="items")
    product = relationship("Product")

class License(Base):
    __tablename__ = "licenses"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), index=True, nullable=False)
    key = Column(String(64), unique=True, index=True, nullable=False)
    status = Column(String(20), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    order = relationship("Order", back_populates="licenses")
    user = relationship("User")
    product = relationship("Product")

class Thread(Base):
    __tablename__ = "threads"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (UniqueConstraint("user_id", name="uix_user_thread"),)

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    thread_id = Column(Integer, ForeignKey("threads.id"), index=True, nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    session_id = Column(String(64), nullable=True)
    event_name = Column(String(64), nullable=False)
    meta_json = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), index=True, nullable=False)
    stripe_subscription_id = Column(String(128), unique=True)
    status = Column(String(32), default="active")
    current_period_end = Column(DateTime(timezone=True), nullable=True)

# Additional models for cart abandonment and automation
class Cart(Base):
    __tablename__ = "carts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    status = Column(String(20), default="active")  # active, abandoned, completed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    items = relationship("CartItem", back_populates="cart")
    user = relationship("User")

class CartItem(Base):
    __tablename__ = "cart_items"
    id = Column(Integer, primary_key=True)
    cart_id = Column(Integer, ForeignKey("carts.id"), index=True, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), index=True, nullable=False)
    quantity = Column(Integer, default=1)
    price_cents = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    cart = relationship("Cart", back_populates="items")
    product = relationship("Product")

class ProductView(Base):
    __tablename__ = "product_views"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"), index=True, nullable=False)
    session_id = Column(String(64), nullable=True)
    viewed_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User")
    product = relationship("Product")
