
# app/routers/order.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.database import get_async_db
from app.models import OrderStatus, User, Cart, CartItem, Product, Order, OrderItem, Address
from app.schemas import OrderCreateSchema, OrderResponseSchema
from app.core.dependencies import admin_required, get_current_user

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/checkout", response_model=OrderResponseSchema)
async def checkout(
    data: OrderCreateSchema,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):
    # 1) Verify address belongs to user
    result = await db.execute(
        select(Address).where(Address.id == data.address_id, Address.user_id == user.id)
    )
    address = result.scalar_one_or_none()
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    # 2) Get user cart
    result = await db.execute(
        select(Cart)
        .options(selectinload(Cart.items))
        .where(Cart.user_id == user.id)
    )
    cart = result.scalar_one_or_none()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    if not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # 3) Load products in cart
    product_ids = [item.product_id for item in cart.items]
    result = await db.execute(select(Product).where(Product.id.in_(product_ids)))
    products = {p.id: p for p in result.scalars().all()}

    # 4) Validate products exist + stock
    subtotal = 0.0
    for item in cart.items:
        product = products.get(item.product_id)
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")

        if item.quantity > product.stock:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough stock for '{product.name}'. Available: {product.stock}"
            )

        subtotal += float(product.price) * item.quantity

    shipping_fee = 0.0
    total_amount = subtotal + shipping_fee

    # 5) Create order
    order = Order(
        buyer_id=user.id,
        address_id=data.address_id,
        subtotal=subtotal,
        shipping_fee=shipping_fee,
        total_amount=total_amount,
        notes=data.notes,
    )
    db.add(order)
    await db.flush()  # gives order.id without commit

    # 6) Create order items + reduce stock
    for item in cart.items:
        product = products[item.product_id]

        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.name,
            price_at_purchase=product.price,
            quantity=item.quantity
        )
        db.add(order_item)

        product.stock -= item.quantity
        db.add(product)

    # 7) Clear cart
    for item in cart.items:
        await db.delete(item)

    # 8) Commit everything
    await db.commit()

    # 9) Reload order with items for response
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order.id)
    )
    order = result.scalar_one()
    return order


@router.get("/", response_model=list[OrderResponseSchema])
async def my_orders(
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.buyer_id == user.id)
        .order_by(Order.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{order_id}", response_model=OrderResponseSchema)
async def get_my_order(
    order_id: int,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order_id, Order.buyer_id == user.id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


# =========================
# ADMIN: update order status
# =========================
@router.put("/{order_id}/status")
async def admin_update_order_status(
    order_id: int,
    new_status: str,
    db: AsyncSession = Depends(get_async_db),
    _: User = Depends(admin_required),
):
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    allowed = {
        OrderStatus.PENDING,
        OrderStatus.SHIPPED,
        OrderStatus.DELIVERED,
        OrderStatus.CANCELLED,
    }
    if new_status not in allowed:
        raise HTTPException(status_code=400, detail="Invalid status")

    order.status = new_status
    await db.commit()
    return {"message": f"Order status updated to '{new_status}'"}




# =========================
# ADMIN: get all orders
# =========================
@router.get("/admin/all", response_model=list[OrderResponseSchema])
async def admin_list_all_orders(
    status: str | None = None,  # optional: ?status=pending
    db: AsyncSession = Depends(get_async_db),
    _: User = Depends(admin_required),
):
    q = (
        select(Order)
        .options(
            selectinload(Order.items),
            selectinload(Order.buyer),
            selectinload(Order.address),
        )
        .order_by(Order.created_at.desc())
    )

    if status:
        status = status.strip().lower()  # ✅ accept PENDING / pending
        allowed = {
            OrderStatus.PENDING,
            OrderStatus.SHIPPED,
            OrderStatus.DELIVERED,
            OrderStatus.CANCELLED,
        }
        if status not in allowed:
            raise HTTPException(status_code=400, detail="Invalid status")
        q = q.where(Order.status == status)

    result = await db.execute(q)
    return result.scalars().all()