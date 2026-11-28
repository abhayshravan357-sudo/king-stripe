from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class VariantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    sku: str
    colour: str
    size: str
    price_minor: int
    currency: str


class ProductOut(BaseModel):
    id: int
    slug: str
    name: str
    type: str
    collection: str
    variants: list[VariantOut]


class CollectionOut(BaseModel):
    id: int
    slug: str
    title: str
    animal: str
    colour: str
    tagline: str
    description: str
    status: str
    artwork: str
    accent: str
    featured: bool


class CartLine(BaseModel):
    variant_id: int
    quantity: int = Field(ge=1, le=10)


class CheckoutIn(BaseModel):
    items: list[CartLine] = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    address: str = Field(min_length=8, max_length=1000)


class CheckoutOut(BaseModel):
    reference: str
    access_token: str
    status: str
    subtotal_minor: int
    currency: str
    payment_ready: bool
    message: str
    provider_order_id: str | None = None
    razorpay_key_id: str | None = None


class PaymentVerifyIn(BaseModel):
    order_reference: str = Field(min_length=16, max_length=40)
    razorpay_order_id: str = Field(min_length=8, max_length=80)
    razorpay_payment_id: str = Field(min_length=8, max_length=80)
    razorpay_signature: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-fA-F]{64}$")


class AdminLoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=1, max_length=256)


class FulfillmentUpdate(BaseModel):
    status: Literal["unfulfilled", "processing", "fulfilled"]


class VariantUpdate(BaseModel):
    price_minor: int | None = Field(default=None, ge=100)
    active: bool | None = None


class InventoryUpdate(BaseModel):
    mode: Literal["limited", "preorder", "made_to_order", "unlimited"]
    quantity_on_hand: int | None = Field(default=None, ge=0)
