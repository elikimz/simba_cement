from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_async_db
from app.models import Cart, CartItem, Product, User
from app.core.dependencies import get_current_user
from app.schemas import (
    CartResponseSchema,
    CartItemCreateSchema,
    CartItemUpdateSchema,
)

router = APIRouter(prefix="/cart", tags=["Cart"])


async def get_or_create_cart(db: AsyncSession, user_id: int) -> Cart:
    result = await db.execute(select(Cart).where(Cart.user_id == user_id))
    cart = result.scalar_one_or_none()
    if cart:
        return cart

    cart = Cart(user_id=user_id)
    db.add(cart)
    await db.flush()  # get cart.id without commit
    return cart


@router.get("/", response_model=CartResponseSchema)
async def get_my_cart(
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):
    # load cart + items + product (to build nicer response)
    result = await db.execute(
        select(Cart)
        .options(selectinload(Cart.items).selectinload(CartItem.product))
        .where(Cart.user_id == user.id)
    )
    cart = result.scalar_one_or_none()
    if not cart:
        cart = await get_or_create_cart(db, user.id)
        await db.commit()
        await db.refresh(cart)

    # attach product details into response shape
    for item in cart.items:
        if item.product:
            item.product_name = item.product.name
            item.product_price = item.product.price
            item.product_image_url = item.product.image_url

    return cart


@router.post("/items", status_code=status.HTTP_201_CREATED)
async def add_to_cart(
    data: CartItemCreateSchema,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):
    # ensure product exists
    product = await db.get(Product, data.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.stock <= 0:
        raise HTTPException(status_code=400, detail="Product out of stock")

    cart = await get_or_create_cart(db, user.id)

    # if item exists -> increment
    result = await db.execute(
        select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.product_id == data.product_id
        )
    )
    item = result.scalar_one_or_none()

    if item:
        new_qty = item.quantity + data.quantity
        if new_qty > product.stock:
            raise HTTPException(status_code=400, detail="Requested quantity exceeds stock")
        item.quantity = new_qty
        msg = "Cart item quantity updated"
    else:
        if data.quantity > product.stock:
            raise HTTPException(status_code=400, detail="Requested quantity exceeds stock")
        item = CartItem(cart_id=cart.id, product_id=data.product_id, quantity=data.quantity)
        db.add(item)
        msg = "Item added to cart"

    await db.commit()
    return {"message": msg}


@router.put("/items/{item_id}")
async def update_cart_item(
    item_id: int,
    data: CartItemUpdateSchema,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):
    # load item and ensure it belongs to user's cart
    result = await db.execute(
        select(CartItem)
        .join(Cart, Cart.id == CartItem.cart_id)
        .where(Cart.user_id == user.id, CartItem.id == item_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    product = await db.get(Product, item.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if data.quantity > product.stock:
        raise HTTPException(status_code=400, detail="Requested quantity exceeds stock")

    item.quantity = data.quantity
    await db.commit()
    return {"message": "Cart item updated"}


@router.delete("/items/{item_id}")
async def remove_cart_item(
    item_id: int,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(CartItem)
        .join(Cart, Cart.id == CartItem.cart_id)
        .where(Cart.user_id == user.id, CartItem.id == item_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")

    await db.delete(item)
    await db.commit()
    return {"message": "Item removed from cart"}
