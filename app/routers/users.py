import re
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.phone_validation import normalize_phone
from app.database import get_async_db
from app.models import User, Cart
from app.core.security import hash_password, verify_password
from app.core.jwt import create_access_token
from app.schemas import RegisterSchema, LoginSchema, TokenResponse

router = APIRouter(prefix="/auth", tags=["Auth"])

# Password validation function
def validate_password(password: str):
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    if not re.search(r"[A-Z]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one uppercase letter"
        )
    if not re.search(r"[a-z]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one lowercase letter"
        )
    if not re.search(r"[0-9]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least one number"
        )
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password should contain at least one special character"
        )


@router.post("/register", response_model=TokenResponse)
async def register(data: RegisterSchema, db: AsyncSession = Depends(get_async_db)):

    # Normalize phone
    try:
        normalized_phone = normalize_phone(data.phone)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phone number"
        )

    # Validate password strength
    validate_password(data.password)

    # Check if email exists
    result = await db.execute(select(User).where(User.email == data.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create user
    new_user = User(
        name=data.name,
        email=data.email,
        phone=normalized_phone,
        password_hash=hash_password(data.password)
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Create cart automatically
    new_cart = Cart(user_id=new_user.id)
    db.add(new_cart)
    await db.commit()
    await db.refresh(new_cart)

    token = create_access_token({"user_id": new_user.id})
    return TokenResponse(access_token=token)






# -----------------------------
# LOGIN (OAuth2 form)
# -----------------------------
@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Swagger will now show a proper login form for email/phone + password
    """

    # Determine if username is email or phone
    if "@" in form_data.username:
        user_query = select(User).where(User.email == form_data.username)
    else:
        # assume phone
        user_query = select(User).where(User.phone == form_data.username)

    result = await db.execute(user_query)
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email/phone or password"
        )

    token = create_access_token({"user_id": user.id, "user_role": user.role})
    return TokenResponse(access_token=token)
