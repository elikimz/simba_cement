

# app/models.py
from sqlalchemy import (
    Boolean, Column, Integer, String, Float, ForeignKey, DateTime, Text, Enum
)
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime


# =========================================================
# ENUMS
# =========================================================
class OrderStatus:
    PENDING = "pending"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


# =========================================================
# USERS
# =========================================================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    phone = Column(String(20), unique=True, nullable=True)
    role = Column(String(20), nullable=False, default="user")
    password_hash = Column(String(255), nullable=True)

    # Relationships
    products = relationship("Product", back_populates="seller", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="buyer", cascade="all, delete-orphan")
    cart = relationship("Cart", back_populates="user", uselist=False, cascade="all, delete-orphan")
    addresses = relationship("Address", back_populates="user", cascade="all, delete-orphan")

    


# =========================================================
# ADDRESS
# =========================================================
class Address(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    full_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    county = Column(String(50), nullable=False)
    town = Column(String(100), nullable=False)
    street = Column(String(200), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="addresses")


# =========================================================
# CATEGORY
# =========================================================
class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)

    products = relationship("Product", back_populates="category", cascade="all, delete-orphan")


# =========================================================
# PRODUCT
# =========================================================
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)

    price = Column(Float, nullable=False)
    original_price = Column(Float, nullable=True)
    discount_percentage = Column(Float, default=0.0)

    stock = Column(Integer, nullable=False, default=0)

    # keep for backward-compat (primary/fallback image)
    image_url = Column(String(300), nullable=True)

    seller_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    seller = relationship("User", back_populates="products")
    category = relationship("Category", back_populates="products")
    cart_items = relationship("CartItem", back_populates="product", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="product", cascade="all, delete-orphan")

    # NEW: multiple images per product
    images = relationship(
        "ProductImage",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductImage.sort_order",
    )


# =========================================================
# PRODUCT IMAGES (NEW)
# =========================================================
class ProductImage(Base):
    __tablename__ = "product_images"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)

    url = Column(String(500), nullable=False)
    is_primary = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="images")


# =========================================================
# DEALS (NEW)
# =========================================================
class Deal(Base):
    __tablename__ = "deals"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    starts_at = Column(DateTime, nullable=True)
    ends_at = Column(DateTime, nullable=True)

    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship(
        "DealItem",
        back_populates="deal",
        cascade="all, delete-orphan",
        order_by="DealItem.sort_order",
    )


class DealItem(Base):
    __tablename__ = "deal_items"

    id = Column(Integer, primary_key=True, index=True)
    deal_id = Column(Integer, ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)

    # optional overrides for this deal
    deal_price = Column(Float, nullable=True)            # fixed special price
    discount_percentage = Column(Float, nullable=True)   # percent override
    sort_order = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    deal = relationship("Deal", back_populates="items")
    product = relationship("Product")


# =========================================================
# CART
# =========================================================
class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="cart")
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("carts.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)

    cart = relationship("Cart", back_populates="items")
    product = relationship("Product", back_populates="cart_items")


# =========================================================
# ORDER
# =========================================================
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    address_id = Column(Integer, ForeignKey("addresses.id", ondelete="SET NULL"), nullable=True)

    status = Column(
        Enum(
            OrderStatus.PENDING,
            OrderStatus.SHIPPED,
            OrderStatus.DELIVERED,
            OrderStatus.CANCELLED,
            name="order_status"
        ),
        default=OrderStatus.PENDING, index=True
    )

    subtotal = Column(Float, nullable=False)
    shipping_fee = Column(Float, nullable=False, default=0)
    total_amount = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    buyer = relationship("User", back_populates="orders")
    address = relationship("Address")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


# =========================================================
# ORDER ITEMS
# =========================================================
class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)

    product_name = Column(String(200), nullable=False)
    price_at_purchase = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")


# =========================================================
# CONTACT / MESSAGES
# =========================================================
# app/models.py  (only the Contact part)

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(120), nullable=True)
    email = Column(String(120), nullable=True)
    phone = Column(String(30), nullable=True)

    message = Column(Text, nullable=False)

    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# =========================================================
# HERO BANNERS (NEW)
# =========================================================
class HeroBanner(Base):
    __tablename__ = "hero_banners"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    cta_text = Column(String(100), nullable=False, default="Shop Now")
    cta_href = Column(String(300), nullable=True, default="/products")

    # scheduling / control
    starts_at = Column(DateTime, nullable=True)
    ends_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, index=True)

    # banner ordering in homepage slider
    sort_order = Column(Integer, default=0, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # multiple images per banner
    images = relationship(
        "HeroBannerImage",
        back_populates="banner",
        cascade="all, delete-orphan",
        order_by="HeroBannerImage.sort_order",
    )


# =========================================================
# HERO BANNER IMAGES (NEW)
# =========================================================
class HeroBannerImage(Base):
    __tablename__ = "hero_banner_images"

    id = Column(Integer, primary_key=True, index=True)
    banner_id = Column(Integer, ForeignKey("hero_banners.id", ondelete="CASCADE"), nullable=False, index=True)

    url = Column(String(500), nullable=False)

    # which image shows first for that banner
    sort_order = Column(Integer, default=0)

    # optional: mark the main image
    is_primary = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    banner = relationship("HeroBanner", back_populates="images")    