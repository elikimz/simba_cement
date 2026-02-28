from fastapi_mail import ConnectionConfig, FastMail, MessageSchema
from pydantic import EmailStr

# -----------------------------
# SMTP Configuration (Pydantic v2 / FastAPI-Mail v2)
# -----------------------------
conf = ConnectionConfig(
    MAIL_USERNAME="elijahkimani1293@gmail.com",
    MAIL_PASSWORD="msuo okfc qujw rzt",
    MAIL_FROM="elijahkimani1293@gmail.com",
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",  # e.g., smtp.gmail.com
    MAIL_STARTTLS=True,              # Use STARTTLS
    MAIL_SSL_TLS=False,              # Do not use SSL directly
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)

# -----------------------------
# Send Password Reset Code
# -----------------------------
async def send_reset_code(email_to: EmailStr, code: str):
    subject = "Password Reset Code"
    body = f"""
Hi,

You requested a password reset. Use the code below to reset your password.
This code is valid for 15 minutes.

Reset Code: {code}

If you did not request this, please ignore this email.

Thanks.
"""
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=body,
        subtype="plain"
    )

    fm = FastMail(conf)
    await fm.send_message(message)
