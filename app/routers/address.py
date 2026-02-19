from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.database import get_async_db
from app.models import Address, User
from app.schemas import AddressCreateSchema, AddressUpdateSchema, AddressResponseSchema
from app.core.dependencies import get_current_user

router = APIRouter(
    prefix="/addresses",
    tags=["Addresses"]
)

# -----------------------------
# CREATE ADDRESS (USER)
# -----------------------------
@router.post("/", response_model=AddressResponseSchema)
async def create_address(
    data: AddressCreateSchema,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user)
):
    address = Address(
        user_id=user.id,
        full_name=data.full_name,
        phone=data.phone,
        county=data.county,
        town=data.town,
        street=data.street,
    )

    db.add(address)
    await db.commit()
    await db.refresh(address)
    return address


# -----------------------------
# GET MY ADDRESSES
# -----------------------------
@router.get("/", response_model=List[AddressResponseSchema])
async def list_my_addresses(
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Address).where(Address.user_id == user.id)
    )
    return result.scalars().all()


# -----------------------------
# UPDATE ADDRESS
# -----------------------------
@router.put("/{address_id}", response_model=AddressResponseSchema)
async def update_address(
    address_id: int,
    data: AddressUpdateSchema,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user)
):
    address = await db.get(Address, address_id)

    if not address or address.user_id != user.id:
        raise HTTPException(status_code=404, detail="Address not found")

    if data.full_name:
        address.full_name = data.full_name
    if data.phone:
        address.phone = data.phone
    if data.county:
        address.county = data.county
    if data.town:
        address.town = data.town
    if data.street:
        address.street = data.street

    await db.commit()
    await db.refresh(address)
    return address


# -----------------------------
# DELETE ADDRESS
# -----------------------------
@router.delete("/{address_id}")
async def delete_address(
    address_id: int,
    db: AsyncSession = Depends(get_async_db),
    user: User = Depends(get_current_user)
):
    address = await db.get(Address, address_id)

    if not address or address.user_id != user.id:
        raise HTTPException(status_code=404, detail="Address not found")

    await db.delete(address)
    await db.commit()
    return {"message": "Address deleted successfully"}
