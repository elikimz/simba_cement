from sqlalchemy import (
    Boolean, Column, Integer, String, Float, ForeignKey, DateTime, Text
)
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

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
    google_id = Column(String(255), unique=True, nullable=True)  # Google's unique ID
    auth_provider = Column(String(20), nullable=False, default="email")  # "email" or "google"

    # Relationships
    products = relationship("Product", back_populates="seller")
    orders = relationship("Order", back_populates="buyer")
    cart = relationship("Cart", back_populates="user", uselist=False)
    sent_messages = relationship("Contact", foreign_keys="Contact.sender_id", back_populates="sender")
    received_messages = relationship("Contact", foreign_keys="Contact.recipient_id", back_populates="recipient")

class Product(Base):
    """Product model for hardware items, including discount fields."""
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)  # Current selling price
    original_price = Column(Float, nullable=True)  # Original price before discount
    discount_percentage = Column(Float, nullable=True, default=0.0)  # Discount percentage (e.g., 10.0 for 10%)
    stock = Column(Integer, nullable=False, default=0)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    seller = relationship("User", back_populates="products")
    cart_items = relationship("CartItem", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")

class Cart(Base):
    """Cart model for buyers."""
    __tablename__ = "carts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    # Relationships
    user = relationship("User", back_populates="cart")
    items = relationship("CartItem", back_populates="cart")

class CartItem(Base):
    """CartItem model for items in a cart."""
    __tablename__ = "cart_items"
    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("carts.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)

    # Relationships
    cart = relationship("Cart", back_populates="items")
    product = relationship("Product", back_populates="cart_items")

class Order(Base):
    """Order model for buyer orders."""
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    buyer = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    """OrderItem model for items in an order."""
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

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

    # Relationships
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    recipient = relationship("User", foreign_keys=[recipient_id], back_populates="received_messages")
