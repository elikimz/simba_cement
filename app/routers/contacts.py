# app/routers/contact.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_async_db
from app.models import Contact, User
from app.schemas import (
    ContactCreateSchema,
    ContactResponseSchema,
    ContactMarkReadSchema,
)
from app.core.dependencies import admin_required

router = APIRouter(prefix="/contacts", tags=["Contacts"])


def clean(s: str | None) -> str | None:
    if s is None:
        return None
    s2 = s.strip()
    return s2 if s2 else None


@router.post("/", response_model=ContactResponseSchema)
async def create_contact(
    data: ContactCreateSchema,
    db: AsyncSession = Depends(get_async_db),
):
    msg = clean(data.message)
    if not msg:
        raise HTTPException(status_code=400, detail="Message is required")

    contact = Contact(
        name=clean(data.name),
        email=str(data.email) if data.email else None,
        phone=clean(data.phone),
        message=msg,
        is_read=False,
    )

    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


@router.get("/admin", response_model=list[ContactResponseSchema])
async def admin_list_contacts(
    db: AsyncSession = Depends(get_async_db),
    _: User = Depends(admin_required),
):
    res = await db.execute(select(Contact).order_by(Contact.created_at.desc()))
    return res.scalars().all()


@router.put("/admin/{contact_id}/read", response_model=ContactResponseSchema)
async def admin_mark_read(
    contact_id: int,
    body: ContactMarkReadSchema,
    db: AsyncSession = Depends(get_async_db),
    _: User = Depends(admin_required),
):
    contact = await db.get(Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Message not found")

    contact.is_read = bool(body.is_read)
    await db.commit()
    await db.refresh(contact)
    return contact


@router.delete("/admin/{contact_id}")
async def admin_delete_contact(
    contact_id: int,
    db: AsyncSession = Depends(get_async_db),
    _: User = Depends(admin_required),
):
    contact = await db.get(Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Message not found")

    await db.delete(contact)
    await db.commit()
    return {"ok": True}