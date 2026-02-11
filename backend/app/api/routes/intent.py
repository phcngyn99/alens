"""
Analytical intent capture routes.
Stores structured user intent for dimensional modeling.
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import IntentCreate, IntentResponse
from app.auth.dependencies import CurrentUser
from app.storage.database import get_db
from app.storage.models import AnalyticalIntent, DatabaseConnection

router = APIRouter(prefix="/intents", tags=["Analytical Intent"])


@router.post("", response_model=IntentResponse, status_code=status.HTTP_201_CREATED)
async def create_intent(
    intent: IntentCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> IntentResponse:
    """
    Create a new analytical intent.
    Each intent is versioned - creating a new one increments the version.
    """
    # Verify connection belongs to user
    result = await db.execute(
        select(DatabaseConnection).where(
            DatabaseConnection.id == intent.connection_id,
            DatabaseConnection.owner_id == current_user.id,
        )
    )
    connection = result.scalar_one_or_none()
    
    if not connection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connection not found")
    
    # Get next version number
    result = await db.execute(
        select(func.max(AnalyticalIntent.version)).where(
            AnalyticalIntent.connection_id == intent.connection_id
        )
    )
    max_version = result.scalar() or 0
    
    db_intent = AnalyticalIntent(
        connection_id=intent.connection_id,
        version=max_version + 1,
        business_domain=intent.business_domain,
        analytical_goal=intent.analytical_goal,
        time_grain=intent.time_grain,
        key_metrics=intent.key_metrics,
        tables_of_interest=[t.model_dump() for t in intent.tables_of_interest],
        exclusions=intent.exclusions,
    )
    
    db.add(db_intent)
    await db.commit()
    await db.refresh(db_intent)
    
    return IntentResponse.model_validate(db_intent)


@router.get("", response_model=list[IntentResponse])
async def list_intents(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    connection_id: UUID = None,
) -> list[IntentResponse]:
    """List all intents, optionally filtered by connection."""
    query = (
        select(AnalyticalIntent)
        .join(DatabaseConnection)
        .where(DatabaseConnection.owner_id == current_user.id)
    )
    
    if connection_id:
        query = query.where(AnalyticalIntent.connection_id == connection_id)
    
    query = query.order_by(AnalyticalIntent.created_at.desc())
    
    result = await db.execute(query)
    intents = result.scalars().all()
    
    return [IntentResponse.model_validate(i) for i in intents]


@router.get("/{intent_id}", response_model=IntentResponse)
async def get_intent(
    intent_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> IntentResponse:
    """Get a specific intent."""
    result = await db.execute(
        select(AnalyticalIntent)
        .join(DatabaseConnection)
        .where(
            AnalyticalIntent.id == intent_id,
            DatabaseConnection.owner_id == current_user.id,
        )
    )
    intent = result.scalar_one_or_none()
    
    if not intent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Intent not found")
    
    return IntentResponse.model_validate(intent)


@router.delete("/{intent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_intent(
    intent_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete an intent."""
    result = await db.execute(
        select(AnalyticalIntent)
        .join(DatabaseConnection)
        .where(
            AnalyticalIntent.id == intent_id,
            DatabaseConnection.owner_id == current_user.id,
        )
    )
    intent = result.scalar_one_or_none()
    
    if not intent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Intent not found")
    
    await db.delete(intent)
    await db.commit()

