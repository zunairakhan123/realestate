from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.auth.models import User, UserRole
from app.core.auth import get_password_hash

async def seed_initial_admin(db: AsyncSession):
    admin_email = "admin@realtycrm.com"
    result = await db.execute(select(User).filter(User.email == admin_email))
    existing_admin = result.scalars().first()
    
    if not existing_admin:
        admin_user = User(
            email=admin_email,
            hashed_password=get_password_hash("Admin123"),
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(admin_user)
        await db.commit()
        print("✅ Initial Admin account successfully seeded.")