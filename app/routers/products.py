# app/routers/products.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.database import get_async_db
from app.models import Product, Category, User
from app.schemas import ProductCreateSchema, ProductUpdateSchema, ProductResponseSchema
from app.core.dependencies import admin_required

router = APIRouter(
    prefix="/products",
    tags=["Products"]
)

# -----------------------------
# CREATE PRODUCT (ADMIN ONLY)
# -----------------------------
@router.post("/", response_model=ProductResponseSchema)
async def create_product(
    data: ProductCreateSchema,
    db: AsyncSession = Depends(get_async_db),
    admin: User = Depends(admin_required)
):
    # Validate category exists (if provided)
    if data.category_id is not None:
        category = await db.get(Category, data.category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

    product = Product(
        name=data.name,
        description=data.description,
        price=data.price,
        original_price=data.original_price,
        discount_percentage=data.discount_percentage or 0.0,
        stock=data.stock,
        image_url=data.image_url,
        category_id=data.category_id,
        seller_id=admin.id
    )

    db.add(product)
    await db.commit()
    await db.refresh(product)

    # Reload with relationships to avoid MissingGreenlet
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.category), selectinload(Product.seller))
        .where(Product.id == product.id)
    )
    return result.scalar_one()

# -----------------------------
# GET ALL PRODUCTS (PUBLIC) - NO ID
# -----------------------------
@router.get("/", response_model=List[ProductResponseSchema])
async def list_products(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(
        select(Product).options(
            selectinload(Product.category),
            selectinload(Product.seller),
        )
    )
    return result.scalars().all()

# -----------------------------
# GET SINGLE PRODUCT (PUBLIC)
# -----------------------------
@router.get("/{product_id}", response_model=ProductResponseSchema)
async def get_product(product_id: int, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.category), selectinload(Product.seller))
        .where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# -----------------------------
# UPDATE PRODUCT (ADMIN ONLY)
# -----------------------------
@router.put("/{product_id}", response_model=ProductResponseSchema)
async def update_product(
    product_id: int,
    data: ProductUpdateSchema,
    db: AsyncSession = Depends(get_async_db),
    admin: User = Depends(admin_required)
):
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if data.name is not None:
        product.name = data.name
    if data.description is not None:
        product.description = data.description
    if data.price is not None:
        product.price = data.price
    if data.original_price is not None:
        product.original_price = data.original_price
    if data.discount_percentage is not None:
        if not (0 <= data.discount_percentage <= 100):
            raise HTTPException(status_code=400, detail="Discount must be between 0 and 100")
        product.discount_percentage = data.discount_percentage
    if data.stock is not None:
        product.stock = data.stock
    if data.image_url is not None:
        product.image_url = data.image_url
    if data.category_id is not None:
        category = await db.get(Category, data.category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        product.category_id = data.category_id

    db.add(product)
    await db.commit()
    await db.refresh(product)

    # Reload with relationships
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.category), selectinload(Product.seller))
        .where(Product.id == product.id)
    )
    return result.scalar_one()

# -----------------------------
# DELETE PRODUCT (ADMIN ONLY)
# -----------------------------
@router.delete("/{product_id}", status_code=status.HTTP_200_OK)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_async_db),
    admin: User = Depends(admin_required)
):
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    name = product.name
    await db.delete(product)
    await db.commit()
    return {"message": f"Product '{name}' has been deleted successfully"}
