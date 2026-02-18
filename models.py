from sqlalchemy import (
    Boolean, Column, Integer, String, Float, ForeignKey, DateTime, Text, Enum
)
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

# --- Enums ---
class OrderStatus:
    PENDING = "pending"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

# --- Models ---
class User(Base):
    """User model for buyers and sellers, with Google OAuth2 support."""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    phone = Column(String(20), unique=True, nullable=True)  # Optional for Google users
    role = Column(String(20), nullable=False, default="buyer")  # Default to "buyer"
    password_hash = Column(String(255), nullable=True)  # Nullable for Google users

class Category(Base):
    """Category model for product categories (e.g., Tools, Building Materials)."""
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)

class Product(Base):
    """Product model for hardware items, including discount and category fields."""
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)  # Current selling price
    original_price = Column(Float, nullable=True)  # Original price before discount
    discount_percentage = Column(Float, nullable=True, default=0.0)  # Discount percentage (e.g., 10.0 for 10%)
    stock = Column(Integer, nullable=False, default=0)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)  # Link to category
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

class Cart(Base):
    """Cart model for buyers."""
    __tablename__ = "carts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

class CartItem(Base):
    """CartItem model for items in a cart."""
    __tablename__ = "cart_items"
    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("carts.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)

class Order(Base):
    """Order model for buyer orders."""
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(
        OrderStatus.PENDING,
        OrderStatus.SHIPPED,
        OrderStatus.DELIVERED,
        OrderStatus.CANCELLED,
        name="order_status"
    ), nullable=False, default=OrderStatus.PENDING, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

class OrderItem(Base):
    """OrderItem model for items in an order."""
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)

class Contact(Base):
    """Contact model for messages between users (buyers, sellers, admins)."""
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    reply_to = Column(Integer, ForeignKey("contacts.id"), nullable=True)  # For message threads

# --- Relationships ---
User.products = relationship("Product", back_populates="seller", cascade="all, delete-orphan")
User.orders = relationship("Order", back_populates="buyer", cascade="all, delete-orphan")
User.cart = relationship("Cart", back_populates="user", uselist=False)
User.sent_messages = relationship("Contact", foreign_keys="Contact.sender_id", back_populates="sender", cascade="all, delete-orphan")
User.received_messages = relationship("Contact", foreign_keys="Contact.recipient_id", back_populates="recipient", cascade="all, delete-orphan")

Category.products = relationship("Product", back_populates="category", cascade="all, delete-orphan")

Product.seller = relationship("User", back_populates="products")
Product.category = relationship("Category", back_populates="products")
Product.cart_items = relationship("CartItem", back_populates="product", cascade="all, delete")
Product.order_items = relationship("OrderItem", back_populates="product", cascade="all, delete")

Cart.user = relationship("User", back_populates="cart")
Cart.items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")

CartItem.cart = relationship("Cart", back_populates="items")
CartItem.product = relationship("Product", back_populates="cart_items")

Order.buyer = relationship("User", back_populates="orders")
Order.items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

OrderItem.order = relationship("Order", back_populates="items")
OrderItem.product = relationship("Product", back_populates="order_items")

Contact.sender = relationship("User", foreign_keys=[Contact.sender_id], back_populates="sent_messages")
Contact.recipient = relationship("User", foreign_keys=[Contact.recipient_id], back_populates="received_messages")
