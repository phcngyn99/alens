"""
User management routes.
Includes change password, user CRUD (admin only), and current user info.
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    ChangePasswordRequest,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from app.auth.dependencies import CurrentAdminUser, CurrentUser
from app.auth.security import verify_password
from app.auth.service import (
    create_user,
    delete_user,
    get_all_users,
    get_user_by_id,
    update_user,
    update_user_password,
)
from app.storage.database import get_db

router = APIRouter(prefix="/users", tags=["User Management"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: CurrentUser) -> UserResponse:
    """Get current user information."""
    return UserResponse.model_validate(current_user)


@router.post("/me/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    request: ChangePasswordRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """
    Change current user's password.
    Requires current password for verification.
    """
    # Verify current password
    if not verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    
    await update_user_password(db, current_user, request.new_password)
    return {"message": "Password changed successfully"}


# ============ Admin-only endpoints ============


@router.get("", response_model=list[UserResponse])
async def list_users(
    admin_user: CurrentAdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[UserResponse]:
    """List all users (admin only)."""
    users = await get_all_users(db)
    return [UserResponse.model_validate(u) for u in users]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_new_user(
    user_data: UserCreate,
    admin_user: CurrentAdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """Create a new user (admin only)."""
    try:
        user = await create_user(
            db,
            username=user_data.username,
            password=user_data.password,
            role=user_data.role,
            is_active=user_data.is_active,
        )
        return UserResponse.model_validate(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    admin_user: CurrentAdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """Get a specific user by ID (admin only)."""
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user_info(
    user_id: UUID,
    user_data: UserUpdate,
    admin_user: CurrentAdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """Update a user's role or active status (admin only)."""
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Prevent admin from deactivating themselves
    if user.id == admin_user.id and user_data.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account",
        )
    
    updated_user = await update_user(
        db, user, is_active=user_data.is_active, role=user_data.role
    )
    return UserResponse.model_validate(updated_user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_endpoint(
    user_id: UUID,
    admin_user: CurrentAdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a user (admin only)."""
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Prevent admin from deleting themselves
    if user.id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )
    
    await delete_user(db, user)

