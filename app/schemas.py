# app/schemas.py

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, constr


# =========================================================
# AUTH SCHEMAS
# =========================================================

class RegisterSchema(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None


class LoginSchema(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ForgotPasswordSchema(BaseModel):
    email: EmailStr


class ResetPasswordSchema(BaseModel):
    email: EmailStr
    code: constr(min_length=6, max_length=6)  # type: ignore
    new_password: str
    reset_token: str


# =========================================================
# CATEGORY SCHEMAS
# =========================================================

class CategoryCreateSchema(BaseModel):
    name: str
    description: Optional[str] = None


class CategoryUpdateSchema(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class CategoryResponseSchema(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    model_config = {"from_attributes": True}


class CategoryNestedSchema(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


# =========================================================
# USER / SELLER NESTED SCHEMAS
# =========================================================

class SellerNestedSchema(BaseModel):
    id: int
    name: str
    email: str

    model_config = {"from_attributes": True}


# # =========================================================
# # PRODUCT SCHEMAS
# # =========================================================

# class ProductCreateSchema(BaseModel):
#     name: str = Field(..., examples=["Cement 50kg"])
#     description: Optional[str] = Field(None, examples=["High quality cement"])
#     price: float = Field(..., examples=[450.0])
#     original_price: Optional[float] = Field(None, examples=[500.0])
#     discount_percentage: Optional[float] = Field(0.0, examples=[10.0])
#     stock: int = Field(..., examples=[100])
#     image_url: Optional[str] = Field(None, examples=["http://example.com/image.png"])
#     category_id: Optional[int] = Field(None, examples=[1])


# class ProductUpdateSchema(BaseModel):
#     name: Optional[str] = Field(None, examples=["Cement 50kg"])
#     description: Optional[str] = Field(None, examples=["High quality cement"])
#     price: Optional[float] = Field(None, examples=[450.0])
#     original_price: Optional[float] = Field(None, examples=[500.0])
#     discount_percentage: Optional[float] = Field(None, examples=[10.0])
#     stock: Optional[int] = Field(None, examples=[100])
#     image_url: Optional[str] = Field(None, examples=["http://example.com/image.png"])
#     category_id: Optional[int] = Field(None, examples=[1])


# class ProductResponseSchema(BaseModel):
#     id: int
#     name: str
#     description: Optional[str] = None
#     price: float
#     original_price: Optional[float] = None
#     discount_percentage: float
#     stock: int
#     image_url: Optional[str] = None

#     seller: SellerNestedSchema
#     category: Optional[CategoryNestedSchema] = None

#     created_at: datetime
#     updated_at: datetime

#     model_config = {"from_attributes": True}



# ✅ NEW
class ProductImageSchema(BaseModel):
    id: int
    url: str

    # allow NULLs coming from DB
    is_primary: Optional[bool] = False
    sort_order: Optional[int] = 0
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ProductCreateSchema(BaseModel):
    name: str = Field(..., examples=["Cement 50kg"])
    description: Optional[str] = Field(None, examples=["High quality cement"])
    price: float = Field(..., examples=[450.0])
    original_price: Optional[float] = Field(None, examples=[500.0])
    discount_percentage: Optional[float] = Field(0.0, examples=[10.0])
    stock: int = Field(..., examples=[100])

    # ✅ keep old one (optional)
    image_url: Optional[str] = Field(None, examples=["http://example.com/image.png"])

    # ✅ NEW: multiple images
    images: Optional[List[str]] = Field(
        default=None,
        examples=[["http://example.com/1.png", "http://example.com/2.png"]],
    )

    category_id: Optional[int] = Field(None, examples=[1])


class ProductUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, examples=["Cement 50kg"])
    description: Optional[str] = Field(None, examples=["High quality cement"])
    price: Optional[float] = Field(None, examples=[450.0])
    original_price: Optional[float] = Field(None, examples=[500.0])
    discount_percentage: Optional[float] = Field(None, examples=[10.0])
    stock: Optional[int] = Field(None, examples=[100])

    image_url: Optional[str] = Field(None, examples=["http://example.com/image.png"])

    # ✅ NEW: if provided, replaces product images list
    images: Optional[List[str]] = Field(
        default=None,
        examples=[["http://example.com/1.png", "http://example.com/2.png"]],
        description="If provided, replaces all product images.",
    )

    category_id: Optional[int] = Field(None, examples=[1])


class ProductResponseSchema(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    original_price: Optional[float] = None
    discount_percentage: float
    stock: int

    # ✅ keep old for compatibility
    image_url: Optional[str] = None

    # ✅ NEW: list of images
    images: List[ProductImageSchema] = []

    seller: "SellerNestedSchema"
    category: Optional["CategoryNestedSchema"] = None

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}




# =========================================================
# CART SCHEMAS
# =========================================================

class CartItemCreateSchema(BaseModel):
    product_id: int
    quantity: int = Field(1, ge=1)


class CartItemUpdateSchema(BaseModel):
    quantity: int = Field(..., ge=1)


class CartItemResponseSchema(BaseModel):
    id: int
    product_id: int
    quantity: int

    # Optional product info (nice for frontend)
    product_name: Optional[str] = None
    product_price: Optional[float] = None
    product_image_url: Optional[str] = None

    model_config = {"from_attributes": True}


class CartResponseSchema(BaseModel):
    id: int
    user_id: int
    items: List[CartItemResponseSchema] = Field(default_factory=list)

    model_config = {"from_attributes": True}


# =========================================================
# ORDER SCHEMAS
# =========================================================

class OrderCreateSchema(BaseModel):
    address_id: int
    notes: Optional[str] = None


class OrderItemResponseSchema(BaseModel):
    id: int
    product_id: int
    product_name: str
    price_at_purchase: float
    quantity: int

    model_config = {"from_attributes": True}


class OrderResponseSchema(BaseModel):
    id: int
    buyer_id: int
    address_id: Optional[int] = None
    status: str

    subtotal: float
    shipping_fee: float
    total_amount: float

    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    items: List[OrderItemResponseSchema] = Field(default_factory=list)

    model_config = {"from_attributes": True}



# =========================
# ADDRESS SCHEMAS
# =========================

class AddressCreateSchema(BaseModel):
    full_name: str
    phone: str
    county: str
    town: str
    street: str


class AddressUpdateSchema(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    county: Optional[str] = None
    town: Optional[str] = None
    street: Optional[str] = None


class AddressResponseSchema(BaseModel):
    id: int
    user_id: int
    full_name: str
    phone: str
    county: str
    town: str
    street: str
    created_at: datetime

    model_config = {"from_attributes": True}
