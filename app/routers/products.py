


# app/routers/products.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.database import get_async_db
from app.models import Product, Category, User, ProductImage  # ✅ add ProductImage
from app.schemas import ProductCreateSchema, ProductUpdateSchema, ProductResponseSchema
from app.core.dependencies import admin_required

router = APIRouter(prefix="/products", tags=["Products"])


def _normalize_images(images: list[str] | None) -> list[str]:
    """Remove empties and duplicates (keep order)."""
    if not images:
        return []
    seen = set()
    out: list[str] = []
    for u in images:
        if not u:
            continue
        u = u.strip()
        if not u or u in seen:
            continue
        seen.add(u)
        out.append(u)
    return out


async def _reload_product(db: AsyncSession, product_id: int) -> Product:
    result = await db.execute(
        select(Product)
        .options(
            selectinload(Product.category),
            selectinload(Product.seller),
            selectinload(Product.images),  # ✅ load images
        )
        .where(Product.id == product_id)
    )
    return result.scalar_one()


# -----------------------------
# CREATE PRODUCT (ADMIN ONLY)
# -----------------------------
@router.post("/", response_model=ProductResponseSchema)
async def create_product(
    data: ProductCreateSchema,
    db: AsyncSession = Depends(get_async_db),
    admin: User = Depends(admin_required),
):
    # Validate category exists (if provided)
    if data.category_id is not None:
        category = await db.get(Category, data.category_id)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

    # ✅ create product (keep image_url for backward-compat)
    product = Product(
        name=data.name,
        description=data.description,
        price=data.price,
        original_price=data.original_price,
        discount_percentage=data.discount_percentage or 0.0,
        stock=data.stock,
        image_url=data.image_url,
        category_id=data.category_id,
        seller_id=admin.id,
    )

    db.add(product)
    await db.commit()
    await db.refresh(product)

    # ✅ create images (if provided)
    images = _normalize_images(getattr(data, "images", None))
    if images:
        # if image_url not given, use first image as fallback
        if not product.image_url:
            product.image_url = images[0]

        for idx, url in enumerate(images):
            db.add(
                ProductImage(
                    product_id=product.id,
                    url=url,
                    is_primary=(idx == 0),
                    sort_order=idx,
                )
            )
        await db.commit()

    return await _reload_product(db, product.id)


# -----------------------------
# GET ALL PRODUCTS (PUBLIC)
# -----------------------------
@router.get("/", response_model=List[ProductResponseSchema])
async def list_products(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(
        select(Product).options(
            selectinload(Product.category),
            selectinload(Product.seller),
            selectinload(Product.images),  # ✅ load images
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
        .options(
            selectinload(Product.category),
            selectinload(Product.seller),
            selectinload(Product.images),  # ✅ load images
        )
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
    admin: User = Depends(admin_required),
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

    # ✅ update images ONLY if images field is provided
    if hasattr(data, "images") and data.images is not None:
        new_images = _normalize_images(data.images)

        # delete old images
        # (relationship cascade delete-orphan will delete when list replaced)
        await db.refresh(product, attribute_names=["images"])
        product.images.clear()

        # rebuild images
        for idx, url in enumerate(new_images):
            product.images.append(
                ProductImage(
                    url=url,
                    is_primary=(idx == 0),
                    sort_order=idx,
                )
            )

        # keep image_url aligned (fallback)
        if new_images and (product.image_url is None or product.image_url.strip() == ""):
            product.image_url = new_images[0]

    db.add(product)
    await db.commit()
    await db.refresh(product)

    return await _reload_product(db, product.id)


# -----------------------------
# DELETE PRODUCT (ADMIN ONLY)
# -----------------------------
@router.delete("/{product_id}", status_code=status.HTTP_200_OK)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_async_db),
    admin: User = Depends(admin_required),
):
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    name = product.name
    await db.delete(product)
    await db.commit()
    return {"message": f"Product '{name}' has been deleted successfully"}