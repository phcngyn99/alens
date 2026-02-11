"""
Database connection management routes.
Includes cache invalidation when connections are modified.
"""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    ConnectionCreate,
    ConnectionResponse,
    ConnectionTestResult,
    ConnectionUpdate,
    DriverStatusResponse,
)
from app.auth.dependencies import CurrentUser
from app.auth.encryption import decrypt_value, encrypt_value
from app.core.cache import CacheKeys, get_cache
from app.core.introspect.base import ConnectionConfig
from app.core.introspect.factory import (
    check_all_drivers,
    check_driver,
    get_introspector,
)
from app.storage.database import get_db
from app.storage.models import DatabaseConnection

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/connections", tags=["Database Connections"])


@router.get("/drivers", response_model=dict[str, DriverStatusResponse])
async def get_driver_status() -> dict[str, DriverStatusResponse]:
    """Get status of all database drivers."""
    drivers = check_all_drivers()
    return {
        db_type: DriverStatusResponse(
            driver_name=status.driver_name,
            is_installed=status.is_installed,
            version=status.version,
            install_instructions=status.install_instructions,
        )
        for db_type, status in drivers.items()
    }


@router.get("", response_model=list[ConnectionResponse])
async def list_connections(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ConnectionResponse]:
    """List all database connections for the current user."""
    result = await db.execute(
        select(DatabaseConnection).where(DatabaseConnection.owner_id == current_user.id)
    )
    connections = result.scalars().all()
    return [ConnectionResponse.model_validate(c) for c in connections]


@router.post("", response_model=ConnectionResponse, status_code=status.HTTP_201_CREATED)
async def create_connection(
    connection: ConnectionCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConnectionResponse:
    """Create a new database connection."""
    # Check driver availability
    driver_status = check_driver(connection.db_type)
    if not driver_status.is_installed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Driver not installed: {driver_status.install_instructions}",
        )

    db_connection = DatabaseConnection(
        owner_id=current_user.id,
        name=connection.name,
        db_type=connection.db_type,
        host=connection.host,
        port=connection.port,
        database_name=connection.database_name,
        username=connection.username,
        encrypted_password=encrypt_value(connection.password),
        schema_whitelist=connection.schema_whitelist,
    )

    db.add(db_connection)
    await db.commit()
    await db.refresh(db_connection)

    return ConnectionResponse.model_validate(db_connection)


@router.get("/{connection_id}", response_model=ConnectionResponse)
async def get_connection(
    connection_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConnectionResponse:
    """Get a specific database connection."""
    result = await db.execute(
        select(DatabaseConnection).where(
            DatabaseConnection.id == connection_id,
            DatabaseConnection.owner_id == current_user.id,
        )
    )
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found"
        )

    return ConnectionResponse.model_validate(connection)


@router.post("/{connection_id}/test", response_model=ConnectionTestResult)
async def test_connection(
    connection_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConnectionTestResult:
    """Test a database connection."""
    result = await db.execute(
        select(DatabaseConnection).where(
            DatabaseConnection.id == connection_id,
            DatabaseConnection.owner_id == current_user.id,
        )
    )
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found"
        )

    config = ConnectionConfig(
        host=connection.host,
        port=connection.port,
        database=connection.database_name,
        username=connection.username,
        password=decrypt_value(connection.encrypted_password),
        schema_whitelist=connection.schema_whitelist,
    )

    introspector = get_introspector(connection.db_type, config)

    try:
        async with introspector:
            success, message = await introspector.test_connection()
            return ConnectionTestResult(success=success, message=message)
    except Exception as e:
        return ConnectionTestResult(success=False, message=str(e))


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    connection_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a database connection and invalidate related cache entries."""
    result = await db.execute(
        select(DatabaseConnection).where(
            DatabaseConnection.id == connection_id,
            DatabaseConnection.owner_id == current_user.id,
        )
    )
    connection = result.scalar_one_or_none()

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found"
        )

    # Invalidate all cache entries for this connection
    cache = get_cache()
    cache_prefix = CacheKeys.for_connection(connection_id)
    deleted_count = await cache.delete_pattern(cache_prefix)
    logger.info(
        f"Invalidated {deleted_count} cache entries for connection {connection_id}"
    )

    await db.delete(connection)
    await db.commit()
