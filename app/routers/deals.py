# app/routers/deals.py
from typing import List
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_, or_

from app.database import get_async_db
from app.models import Deal, DealItem, Product, User
from app.schemas import DealCreateSchema, DealUpdateSchema, DealResponseSchema
from app.core.dependencies import admin_required

router = APIRouter(prefix="/deals", tags=["Deals"])


# =========================================================
# TIME HELPERS (NAIROBI)
# =========================================================
NAIROBI_TZ = timezone(timedelta(hours=3))


def _naive_nairobi(dt: datetime | None) -> datetime | None:
    """
    Store datetimes as TIMESTAMP WITHOUT TIME ZONE representing Nairobi local time.
    - If aware -> convert to Nairobi time then drop tzinfo.
    - If naive -> assume it is already Nairobi local time.
    """
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(NAIROBI_TZ).replace(tzinfo=None)
    return dt


def _now_naive_nairobi() -> datetime:
    """Naive Nairobi now (matches TIMESTAMP WITHOUT TIME ZONE stored as Nairobi local time)."""
    return datetime.now(NAIROBI_TZ).replace(tzinfo=None)


# =========================================================
# DB HELPERS
# =========================================================
async def _reload_deal(db: AsyncSession, deal_id: int) -> Deal:
    result = await db.execute(
        select(Deal)
        .options(selectinload(Deal.items).selectinload(DealItem.product))
        .where(Deal.id == deal_id)
    )
    return result.scalar_one()


def _deal_to_response(deal: Deal) -> DealResponseSchema:
    products = []
    for it in sorted(deal.items or [], key=lambda x: x.sort_order or 0):
        p = it.product
        if not p:
            continue
        products.append(
            {
                "id": p.id,
                "name": p.name,
                "price": float(p.price),
                "stock": int(p.stock or 0),
                "image_url": p.image_url,
                "deal_price": it.deal_price,
                "discount_percentage": it.discount_percentage,
                "sort_order": it.sort_order or 0,
            }
        )

    return DealResponseSchema(
        id=deal.id,
        title=deal.title,
        description=deal.description,
        starts_at=deal.starts_at,
        ends_at=deal.ends_at,
        is_active=deal.is_active,
        created_at=deal.created_at,
        products=products,
    )


# =========================================================
# ROUTES
# =========================================================

# -----------------------------
# CREATE DEAL (ADMIN ONLY)
# -----------------------------
@router.post("/", response_model=DealResponseSchema)
async def create_deal(
    data: DealCreateSchema,
    db: AsyncSession = Depends(get_async_db),
    admin: User = Depends(admin_required),
):
    starts_at = _naive_nairobi(data.starts_at)
    ends_at = _naive_nairobi(data.ends_at)

    if starts_at and ends_at and ends_at < starts_at:
        raise HTTPException(status_code=400, detail="ends_at must be after starts_at")

    deal = Deal(
        title=data.title,
        description=data.description,
        starts_at=starts_at,
        ends_at=ends_at,
        is_active=data.is_active,
    )

    db.add(deal)
    await db.commit()
    await db.refresh(deal)

    if data.items:
        product_ids = [it.product_id for it in data.items]
        res = await db.execute(select(Product.id).where(Product.id.in_(product_ids)))
        found = set(res.scalars().all())
        missing = [pid for pid in product_ids if pid not in found]
        if missing:
            raise HTTPException(status_code=404, detail=f"Products not found: {missing}")

        for it in data.items:
            db.add(
                DealItem(
                    deal_id=deal.id,
                    product_id=it.product_id,
                    deal_price=it.deal_price,
                    discount_percentage=it.discount_percentage,
                    sort_order=it.sort_order,
                )
            )
        await db.commit()

    deal = await _reload_deal(db, deal.id)
    return _deal_to_response(deal)


# -----------------------------
# LIST DEALS (PUBLIC)
# -----------------------------
@router.get("/", response_model=List[DealResponseSchema])
async def list_deals(db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(
        select(Deal)
        .options(selectinload(Deal.items).selectinload(DealItem.product))
        .order_by(Deal.created_at.desc())
    )
    deals = result.scalars().all()
    return [_deal_to_response(d) for d in deals]


# -----------------------------
# GET LATEST ACTIVE DEAL (PUBLIC)
# -----------------------------
@router.get("/latest", response_model=DealResponseSchema)
async def latest_deal(db: AsyncSession = Depends(get_async_db)):
    # ✅ Nairobi time comparison (naive values represent Nairobi time)
    now = _now_naive_nairobi()

    result = await db.execute(
        select(Deal)
        .options(selectinload(Deal.items).selectinload(DealItem.product))
        .where(
            and_(
                Deal.is_active == True,
                or_(Deal.starts_at == None, Deal.starts_at <= now),
                or_(Deal.ends_at == None, Deal.ends_at >= now),
            )
        )
        .order_by(Deal.created_at.desc())
        .limit(1)
    )
    deal = result.scalar_one_or_none()
    if not deal:
        raise HTTPException(status_code=404, detail="No active deal found")

    return _deal_to_response(deal)


# -----------------------------
# GET SINGLE DEAL (PUBLIC)
# -----------------------------
@router.get("/{deal_id}", response_model=DealResponseSchema)
async def get_deal(deal_id: int, db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(
        select(Deal)
        .options(selectinload(Deal.items).selectinload(DealItem.product))
        .where(Deal.id == deal_id)
    )
    deal = result.scalar_one_or_none()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return _deal_to_response(deal)


# -----------------------------
# UPDATE DEAL (ADMIN ONLY)
# -----------------------------
@router.put("/{deal_id}", response_model=DealResponseSchema)
async def update_deal(
    deal_id: int,
    data: DealUpdateSchema,
    db: AsyncSession = Depends(get_async_db),
    admin: User = Depends(admin_required),
):
    deal = await db.get(Deal, deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    if data.title is not None:
        deal.title = data.title
    if data.description is not None:
        deal.description = data.description
    if data.starts_at is not None:
        deal.starts_at = _naive_nairobi(data.starts_at)
    if data.ends_at is not None:
        deal.ends_at = _naive_nairobi(data.ends_at)
    if data.is_active is not None:
        deal.is_active = data.is_active

    if deal.starts_at and deal.ends_at and deal.ends_at < deal.starts_at:
        raise HTTPException(status_code=400, detail="ends_at must be after starts_at")

    if data.items is not None:
        await db.refresh(deal, attribute_names=["items"])
        deal.items.clear()

        if data.items:
            product_ids = [it.product_id for it in data.items]
            res = await db.execute(select(Product.id).where(Product.id.in_(product_ids)))
            found = set(res.scalars().all())
            missing = [pid for pid in product_ids if pid not in found]
            if missing:
                raise HTTPException(status_code=404, detail=f"Products not found: {missing}")

            for it in data.items:
                deal.items.append(
                    DealItem(
                        product_id=it.product_id,
                        deal_price=it.deal_price,
                        discount_percentage=it.discount_percentage,
                        sort_order=it.sort_order,
                    )
                )

    db.add(deal)
    await db.commit()

    deal = await _reload_deal(db, deal.id)
    return _deal_to_response(deal)


# -----------------------------
# DELETE DEAL (ADMIN ONLY)
# -----------------------------
@router.delete("/{deal_id}", status_code=status.HTTP_200_OK)
async def delete_deal(
    deal_id: int,
    db: AsyncSession = Depends(get_async_db),
    admin: User = Depends(admin_required),
):
    deal = await db.get(Deal, deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    title = deal.title
    await db.delete(deal)
    await db.commit()
    return {"message": f"Deal '{title}' deleted successfully"}