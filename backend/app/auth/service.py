"""
Authentication service for user management.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import get_password_hash, verify_password
from app.config import get_settings
from app.storage.models import User, UserRole

settings = get_settings()


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    """Find a user by username."""
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User | None:
    """Find a user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_all_users(db: AsyncSession) -> list[User]:
    """Get all users."""
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return list(result.scalars().all())


async def authenticate_user(
    db: AsyncSession, username: str, password: str
) -> User | None:
    """Authenticate a user by username and password."""
    user = await get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def create_user(
    db: AsyncSession,
    username: str,
    password: str,
    role: str = UserRole.USER.value,
    is_active: bool = True,
) -> User:
    """
    Create a new user.
    Raises ValueError if username already exists.
    """
    existing = await get_user_by_username(db, username)
    if existing:
        raise ValueError(f"Username '{username}' already exists")

    user = User(
        username=username,
        hashed_password=get_password_hash(password),
        role=role,
        is_active=is_active,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user_password(db: AsyncSession, user: User, new_password: str) -> User:
    """Update a user's password."""
    user.hashed_password = get_password_hash(new_password)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user(
    db: AsyncSession,
    user: User,
    is_active: Optional[bool] = None,
    role: Optional[str] = None,
) -> User:
    """Update user properties (admin only)."""
    if is_active is not None:
        user.is_active = is_active
    if role is not None:
        user.role = role
    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user: User) -> None:
    """Delete a user."""
    await db.delete(user)
    await db.commit()


async def create_default_user(db: AsyncSession) -> User | None:
    """
    Create the default admin user if it doesn't exist.
    Returns the user if created, None if already exists.
    """
    existing = await get_user_by_username(db, settings.default_username)
    if existing:
        return None

    user = User(
        username=settings.default_username,
        hashed_password=get_password_hash(settings.default_password),
        role=UserRole.ADMIN.value,  # Default user is admin
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
