import random
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.security import hash_password
from app.models import User
from app.database import get_async_db
from app.core.jwt import create_access_token, decode_access_token
from app.core.gmail import send_reset_code
from app.routers.users import validate_password
from app.schemas import ForgotPasswordSchema, ResetPasswordSchema

router = APIRouter(prefix="/settings", tags=["Settings"])

# -----------------------------
# FORGOT PASSWORD
# -----------------------------
@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordSchema, db: AsyncSession = Depends(get_async_db)):

    # Find user by email
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Generate 6-digit numeric code
    code = f"{random.randint(100000, 999999)}"

    # Encode code into JWT valid 15 mins
    token_data = {
        "user_id": user.id,
        "code": code,
        "exp": datetime.utcnow() + timedelta(minutes=15)
    }
    reset_token = create_access_token(token_data)

    # Send code via email
    await send_reset_code(user.email, code)

    return {
        "message": "Password reset code sent to your email.",
        "reset_token": reset_token  # user needs this token to reset password
    }


# -----------------------------
# RESET PASSWORD
# -----------------------------
@router.post("/reset-password")
async def reset_password(data: ResetPasswordSchema, db: AsyncSession = Depends(get_async_db)):

    # Decode the reset token sent by user
    try:
        payload = decode_access_token(data.reset_token)
        user_id = payload.get("user_id")
        code_in_token = payload.get("code")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    # Check if code matches
    if code_in_token != data.code:
        raise HTTPException(status_code=400, detail="Invalid reset code")

    # Get the user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate new password
    validate_password(data.new_password)

    # Update password
    user.password_hash = hash_password(data.new_password)
    db.add(user)
    await db.commit()

    return {"message": "Password has been reset successfully"}
