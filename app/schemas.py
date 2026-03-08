from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict

# =========================================================
# AUTH SCHEMAS
# =========================================================

class RegisterSchema(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(char.isupper() for char in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.islower() for char in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one number")
        if not any(char in "!@#$%^&*(),.?\":{}|<>" for char in v):
            raise ValueError("Password should contain at least one special character")
        return v


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
    code: str = Field(..., min_length=6, max_length=6)
    new_password: str
    reset_token: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("New password must be at least 8 characters long")
        if not any(char.isupper() for char in v):
            raise ValueError("New password must contain at least one uppercase letter")
        if not any(char.islower() for char in v):
            raise ValueError("New password must contain at least one lowercase letter")
        if not any(char.isdigit() for char in v):
            raise ValueError("New password must contain at least one number")
        if not any(char in "!@#$%^&*(),.?\":{}|<>" for char in v):
            raise ValueError("New password should contain at least one special character")
        return v


class ChangePasswordSchema(BaseModel):
    old_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("New password must be at least 8 characters long")
        if not any(char.isupper() for char in v):
            raise ValueError("New password must contain at least one uppercase letter")
        if not any(char.islower() for char in v):
            raise ValueError("New password must contain at least one lowercase letter")
        if not any(char.isdigit() for char in v):
            raise ValueError("New password must contain at least one number")
        if not any(char in "!@#$%^&*(),.?\":{}|<>" for char in v):
            raise ValueError("New password should contain at least one special character")
        return v


# =========================================================
# USER / SELLER SCHEMAS
# =========================================================

class UserPublicSchema(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    role: str

    model_config = ConfigDict(from_attributes=True)


class SellerNestedSchema(BaseModel):
    id: int
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


class CategoryNestedSchema(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


# =========================================================
# PRODUCT SCHEMAS
# =========================================================

class ProductImageSchema(BaseModel):
    id: int
    url: str
    is_primary: bool = False
    sort_order: int = 0
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ProductCreateSchema(BaseModel):
    name: str = Field(..., examples=["Cement 50kg"])
    description: Optional[str] = Field(None, examples=["High quality cement"])
    price: float = Field(..., examples=[450.0])
    max_price: Optional[float] = None 
    original_price: Optional[float] = Field(None, examples=[500.0])
    discount_percentage: float = 0.0
    stock: int = Field(..., examples=[100])
    image_url: Optional[str] = None
    images: Optional[List[str]] = None
    category_id: Optional[int] = None


class ProductUpdateSchema(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    max_price: Optional[float] = None 
    original_price: Optional[float] = None
    discount_percentage: Optional[float] = None
    stock: Optional[int] = None
    image_url: Optional[str] = None
    images: Optional[List[str]] = None
    category_id: Optional[int] = None


class ProductResponseSchema(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    max_price: Optional[float] = None 
    original_price: Optional[float] = None
    discount_percentage: float
    stock: int
    image_url: Optional[str] = None
    images: List[ProductImageSchema] = []
    seller: SellerNestedSchema
    category: Optional[CategoryNestedSchema] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


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
    product_name: Optional[str] = None
    product_price: Optional[float] = None
    product_image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CartResponseSchema(BaseModel):
    id: int
    user_id: int
    items: List[CartItemResponseSchema] = []

    model_config = ConfigDict(from_attributes=True)


# =========================================================
# ADDRESS SCHEMAS
# =========================================================

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

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


class OrderResponseSchema(BaseModel):
    id: int
    buyer_id: int
    status: str
    subtotal: float
    shipping_fee: float
    total_amount: float
    notes: Optional[str] = None
    address_id: Optional[int] = None
    address: Optional[AddressResponseSchema] = None
    buyer: Optional[UserPublicSchema] = None
    items: List[OrderItemResponseSchema] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =========================================================
# DEAL SCHEMAS
# =========================================================

class DealItemCreateSchema(BaseModel):
    product_id: int
    deal_price: Optional[float] = None
    discount_percentage: Optional[float] = None
    sort_order: int = 0

    @field_validator("discount_percentage")
    @classmethod
    def validate_discount(cls, v):
        if v is not None and not (0 <= v <= 100):
            raise ValueError("discount_percentage must be between 0 and 100")
        return v

    @field_validator("deal_price")
    @classmethod
    def validate_price(cls, v):
        if v is not None and v < 0:
            raise ValueError("deal_price must be >= 0")
        return v


class DealCreateSchema(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    is_active: bool = True
    items: List[DealItemCreateSchema] = []


class DealUpdateSchema(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    is_active: Optional[bool] = None
    items: Optional[List[DealItemCreateSchema]] = None


class DealProductOutSchema(BaseModel):
    id: int
    name: str
    price: float
    stock: int
    image_url: Optional[str] = None
    deal_price: Optional[float] = None
    discount_percentage: Optional[float] = None
    sort_order: int = 0

    model_config = ConfigDict(from_attributes=True)


class DealResponseSchema(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    products: List[DealProductOutSchema]

    model_config = ConfigDict(from_attributes=True)


# =========================================================
# HERO BANNER SCHEMAS
# =========================================================

class HeroBannerImageBase(BaseModel):
    url: str
    sort_order: int = 0
    is_primary: bool = False


class HeroBannerImageCreateSchema(HeroBannerImageBase):
    pass


class HeroBannerImageResponseSchema(HeroBannerImageBase):
    id: int
    banner_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HeroBannerBase(BaseModel):
    title: str
    description: Optional[str] = None
    cta_text: str = "Shop Now"
    cta_href: Optional[str] = "/products"
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    is_active: bool = True
    sort_order: int = 0


class HeroBannerCreateSchema(HeroBannerBase):
    images: List[HeroBannerImageCreateSchema] = []


class HeroBannerUpdateSchema(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    cta_text: Optional[str] = None
    cta_href: Optional[str] = None
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class HeroBannerResponseSchema(HeroBannerBase):
    id: int
    created_at: datetime
    updated_at: datetime
    images: List[HeroBannerImageResponseSchema] = []

    model_config = ConfigDict(from_attributes=True)


# =========================================================
# CONTACT SCHEMAS
# =========================================================

class ContactCreateSchema(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    message: str


class ContactResponseSchema(BaseModel):
    id: int
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    message: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ContactMarkReadSchema(BaseModel):
    is_read: bool
