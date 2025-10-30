from pydantic import BaseModel, EmailStr
from typing import List, Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str
    class Config:
        from_attributes = True

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ProductOut(BaseModel):
    id: int
    sku: str
    name: str
    slug: str
    description: str
    price_cents: int
    currency: str
    is_subscription: bool
    features_json: list | None = None
    media_urls_json: list | None = None
    class Config:
        from_attributes = True

class LineItem(BaseModel):
    price_id: str
    qty: int = 1

class CheckoutSessionCreate(BaseModel):
    items: List[LineItem]

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int

class OrderCreate(BaseModel):
    items: List[OrderItemCreate]

class OrderItemOut(BaseModel):
    product_id: int
    qty: int
    unit_price_cents: int
    class Config:
        from_attributes = True

class OrderOut(BaseModel):
    id: int
    status: str
    currency: str
    total_cents: int
    tax_cents: int
    items: List[OrderItemOut]
    class Config:
        from_attributes = True

class ChatMessageIn(BaseModel):
    thread_id: Optional[int] = None
    body: str

class AIMessage(BaseModel):
    message: str
    user_email: Optional[str] = None
