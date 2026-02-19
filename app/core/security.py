from passlib.context import CryptContext

# bcrypt configuration
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

# ---------------------------------------------------
# HASH PASSWORD (truncate to 72 characters)
# ---------------------------------------------------
def hash_password(password: str) -> str:
    """
    Convert plain password into secure hash.
    Truncate to 72 characters for bcrypt compatibility.
    Stored in DB.
    """
    truncated = password[:72]  # truncate to 72 chars
    return pwd_context.hash(truncated)


# ---------------------------------------------------
# VERIFY PASSWORD (truncate to 72 characters)
# ---------------------------------------------------
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Compare login password with DB hash.
    """
    truncated = plain_password[:72]  # truncate to 72 chars
    return pwd_context.verify(truncated, hashed_password)
