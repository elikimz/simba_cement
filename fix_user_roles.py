import asyncio
from sqlalchemy import text
from app.database import engine

async def fix_roles():
    async with engine.begin() as conn:
        # Update existing 'ADMIN' string values to match the Enum's expected 'ADMIN' (lowercase)
        # This is specifically for cases where the database might have a case mismatch 
        # or the Enum is being strict about its internal representation.
        # Based on the error, it seems the database has 'ADMIN' but the Enum is expecting something else or vice versa.
        # Let's try to normalize them.
        await conn.execute(text("UPDATE users SET role = 'ADMIN' WHERE role::text ILIKE 'ADMIN'"))
        await conn.execute(text("UPDATE users SET role = 'USER' WHERE role::text ILIKE 'USER'"))
        print("User roles normalized.")

if __name__ == "__main__":
    asyncio.run(fix_roles())
