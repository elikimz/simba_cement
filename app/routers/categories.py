from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.models import Category, User
from app.database import get_async_db
from app.schemas import CategoryCreateSchema, CategoryUpdateSchema, CategoryResponseSchema
from app.core.dependencies import admin_required  # OAuth2 + admin check

router = APIRouter(
    prefix="/categories",
    tags=["Categories"]
)

# -----------------------------
# CREATE CATEGORY (ADMIN ONLY)
# -----------------------------
@router.post("/", response_model=CategoryResponseSchema)
async def create_category(
    data: CategoryCreateSchema,
    db: AsyncSession = Depends(get_async_db),
    _: User = Depends(admin_required)  # only admin
):
    result = await db.execute(select(Category).where(Category.name == data.name))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")

    category = Category(name=data.name, description=data.description)
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category

# -----------------------------
# GET ALL CATEGORIES (PUBLIC)
# -----------------------------
@router.get("/", response_model=List[CategoryResponseSchema])
async def list_categories(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(select(Category))
    categories = result.scalars().all()
    return categories

# -----------------------------
# GET SINGLE CATEGORY (PUBLIC)
# -----------------------------
@router.get("/{category_id}", response_model=CategoryResponseSchema)
async def get_category(category_id: int, db: AsyncSession = Depends(get_async_db)):
    category = await db.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

# -----------------------------
# UPDATE CATEGORY (ADMIN ONLY)
# -----------------------------
@router.put("/{category_id}", response_model=CategoryResponseSchema)
async def update_category(
    category_id: int,
    data: CategoryUpdateSchema,
    db: AsyncSession = Depends(get_async_db),
    _: User = Depends(admin_required)  # only admin
):
    category = await db.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    if data.name:
        category.name = data.name
    if data.description:
        category.description = data.description

    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category

# -----------------------------
# DELETE CATEGORY (ADMIN ONLY)
# -----------------------------
@router.delete("/{category_id}")
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_async_db),
    _: User = Depends(admin_required)  # only admin
):
    category = await db.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    await db.delete(category)
    await db.commit()
    return {"message": f"Category '{category.name}' has been deleted successfully"}
