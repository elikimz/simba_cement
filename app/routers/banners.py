from typing import List
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import or_

from app.database import get_async_db
from app.models import User, HeroBanner, HeroBannerImage
from app.schemas import (
    HeroBannerCreateSchema,
    HeroBannerUpdateSchema,
    HeroBannerResponseSchema,
)
from app.core.dependencies import admin_required

router = APIRouter(prefix="/hero-banners", tags=["Hero Banners"])


# ---------------------------------------------------------
# Helpers: convert aware datetime -> naive UTC (for DB)
# ---------------------------------------------------------
def to_naive_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def now_utc_naive() -> datetime:
    # naive UTC, matches TIMESTAMP WITHOUT TIME ZONE
    return datetime.utcnow()


# =========================================================
# PUBLIC: list active banners for homepage
# =========================================================
@router.get("/", response_model=List[HeroBannerResponseSchema])
async def list_active_banners(
    db: AsyncSession = Depends(get_async_db),
):
    n = now_utc_naive()

    result = await db.execute(
        select(HeroBanner)
        .options(selectinload(HeroBanner.images))
        .where(
            HeroBanner.is_active == True,
            or_(HeroBanner.starts_at == None, HeroBanner.starts_at <= n),
            or_(HeroBanner.ends_at == None, HeroBanner.ends_at >= n),
        )
        .order_by(HeroBanner.sort_order.asc(), HeroBanner.id.desc())
    )
    return result.scalars().all()


# =========================================================
# ADMIN: list all banners (including inactive)
# =========================================================
@router.get("/admin", response_model=List[HeroBannerResponseSchema])
async def admin_list_all_banners(
    db: AsyncSession = Depends(get_async_db),
    _: User = Depends(admin_required),
):
    result = await db.execute(
        select(HeroBanner)
        .options(selectinload(HeroBanner.images))
        .order_by(HeroBanner.sort_order.asc(), HeroBanner.id.desc())
    )
    return result.scalars().all()


# =========================================================
# ADMIN: create banner (+ images)
# =========================================================
@router.post("/admin", response_model=HeroBannerResponseSchema)
async def admin_create_banner(
    payload: HeroBannerCreateSchema,
    db: AsyncSession = Depends(get_async_db),
    _: User = Depends(admin_required),
):
    banner = HeroBanner(
        title=payload.title,
        description=payload.description,
        cta_text=payload.cta_text,
        cta_href=payload.cta_href,
        starts_at=to_naive_utc(payload.starts_at),
        ends_at=to_naive_utc(payload.ends_at),
        is_active=payload.is_active,
        sort_order=payload.sort_order,
    )
    db.add(banner)
    await db.flush()  # get banner.id

    # if payload has a primary image, ensure only one primary
    has_primary = any(img.is_primary for img in payload.images)

    for idx, img in enumerate(payload.images):
        db.add(
            HeroBannerImage(
                banner_id=banner.id,
                url=img.url,
                sort_order=img.sort_order,
                is_primary=(img.is_primary if has_primary else idx == 0),
            )
        )

    await db.commit()

    result = await db.execute(
        select(HeroBanner)
        .options(selectinload(HeroBanner.images))
        .where(HeroBanner.id == banner.id)
    )
    return result.scalar_one()


# =========================================================
# ADMIN: update banner fields
# =========================================================
@router.put("/admin/{banner_id}", response_model=HeroBannerResponseSchema)
async def admin_update_banner(
    banner_id: int,
    payload: HeroBannerUpdateSchema,
    db: AsyncSession = Depends(get_async_db),
    _: User = Depends(admin_required),
):
    banner = await db.get(HeroBanner, banner_id)
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")

    data = payload.model_dump(exclude_unset=True)

    # convert datetime fields if present
    if "starts_at" in data:
        data["starts_at"] = to_naive_utc(data["starts_at"])
    if "ends_at" in data:
        data["ends_at"] = to_naive_utc(data["ends_at"])

    for k, v in data.items():
        setattr(banner, k, v)

    db.add(banner)
    await db.commit()

    result = await db.execute(
        select(HeroBanner)
        .options(selectinload(HeroBanner.images))
        .where(HeroBanner.id == banner_id)
    )
    return result.scalar_one()


# =========================================================
# ADMIN: delete banner (cascades images)
# =========================================================
@router.delete("/admin/{banner_id}")
async def admin_delete_banner(
    banner_id: int,
    db: AsyncSession = Depends(get_async_db),
    _: User = Depends(admin_required),
):
    banner = await db.get(HeroBanner, banner_id)
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")

    await db.delete(banner)
    await db.commit()
    return {"ok": True}


# =========================================================
# ADMIN: add an image to a banner
# =========================================================
@router.post("/admin/{banner_id}/images", response_model=HeroBannerResponseSchema)
async def admin_add_banner_image(
    banner_id: int,
    url: str,
    sort_order: int = 0,
    is_primary: bool = False,
    db: AsyncSession = Depends(get_async_db),
    _: User = Depends(admin_required),
):
    banner = await db.get(HeroBanner, banner_id)
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")

    if is_primary:
        result = await db.execute(
            select(HeroBannerImage).where(HeroBannerImage.banner_id == banner_id)
        )
        for img in result.scalars().all():
            img.is_primary = False
            db.add(img)

    db.add(
        HeroBannerImage(
            banner_id=banner_id,
            url=url,
            sort_order=sort_order,
            is_primary=is_primary,
        )
    )
    await db.commit()

    result = await db.execute(
        select(HeroBanner)
        .options(selectinload(HeroBanner.images))
        .where(HeroBanner.id == banner_id)
    )
    return result.scalar_one()


# =========================================================
# ADMIN: delete a banner image
# =========================================================
@router.delete("/admin/images/{image_id}")
async def admin_delete_banner_image(
    image_id: int,
    db: AsyncSession = Depends(get_async_db),
    _: User = Depends(admin_required),
):
    img = await db.get(HeroBannerImage, image_id)
    if not img:
        raise HTTPException(status_code=404, detail="Image not found")

    banner_id = img.banner_id
    await db.delete(img)
    await db.commit()

    # (optional) if you deleted the primary image, you can set first as primary
    result = await db.execute(
        select(HeroBannerImage)
        .where(HeroBannerImage.banner_id == banner_id)
        .order_by(HeroBannerImage.sort_order.asc(), HeroBannerImage.id.asc())
    )
    imgs = result.scalars().all()
    if imgs and not any(i.is_primary for i in imgs):
        imgs[0].is_primary = True
        db.add(imgs[0])
        await db.commit()

    return {"ok": True}


# =========================================================
# ADMIN: set a banner image as primary
# =========================================================
@router.put("/admin/images/{image_id}/primary")
async def admin_set_primary_image(
    image_id: int,
    db: AsyncSession = Depends(get_async_db),
    _: User = Depends(admin_required),
):
    img = await db.get(HeroBannerImage, image_id)
    if not img:
        raise HTTPException(status_code=404, detail="Image not found")

    result = await db.execute(
        select(HeroBannerImage).where(HeroBannerImage.banner_id == img.banner_id)
    )
    for other in result.scalars().all():
        other.is_primary = (other.id == img.id)
        db.add(other)

    await db.commit()
    return {"ok": True}