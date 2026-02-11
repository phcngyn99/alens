"""
Database introspection routes.
All operations are READ-ONLY.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    ColumnResponse,
    ForeignKeyResponse,
    SchemaResponse,
    TableDataPreviewResponse,
    TableResponse,
)
from app.auth.dependencies import CurrentUser
from app.auth.encryption import decrypt_value
from app.core.introspect.base import ConnectionConfig
from app.core.introspect.factory import get_introspector
from app.storage.database import get_db
from app.storage.models import DatabaseConnection

router = APIRouter(prefix="/introspect", tags=["Schema Introspection"])


async def _get_connection_and_introspector(
    connection_id: UUID,
    current_user,
    db: AsyncSession,
):
    """Helper to get connection and create introspector."""
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
    return connection, introspector


@router.get("/{connection_id}/schemas", response_model=list[str])
async def list_schemas(
    connection_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[str]:
    """List all schemas in the database (respects whitelist)."""
    _, introspector = await _get_connection_and_introspector(
        connection_id, current_user, db
    )

    try:
        async with introspector:
            return await introspector.get_schemas()
    except ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )


@router.get("/{connection_id}/schemas/{schema_name}/tables", response_model=list[str])
async def list_tables(
    connection_id: UUID,
    schema_name: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[str]:
    """List all tables in a schema."""
    _, introspector = await _get_connection_and_introspector(
        connection_id, current_user, db
    )

    try:
        async with introspector:
            return await introspector.get_tables(schema_name)
    except ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )


@router.get("/{connection_id}/schemas/{schema_name}", response_model=SchemaResponse)
async def introspect_schema(
    connection_id: UUID,
    schema_name: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    include_stats: bool = Query(False, description="Include approximate row counts"),
) -> SchemaResponse:
    """
    Fully introspect a schema - returns all tables with columns, keys, and indexes.
    This is an explicit action that scans the schema.
    """
    _, introspector = await _get_connection_and_introspector(
        connection_id, current_user, db
    )

    try:
        async with introspector:
            schema = await introspector.introspect_schema(schema_name)

            # Optionally get row counts
            if include_stats and hasattr(introspector, "get_approximate_row_count"):
                for table in schema.tables:
                    table.approximate_row_count = (
                        await introspector.get_approximate_row_count(
                            schema_name, table.name
                        )
                    )

            # Convert to response with hints
            table_responses = []
            for table in schema.tables:
                # Determine hint based on characteristics
                hint = None
                if table.has_timestamp_columns and table.fk_count >= 2:
                    hint = "event-like"
                elif table.fk_count == 0:
                    hint = "reference-like"

                table_responses.append(
                    TableResponse(
                        schema_name=table.schema_name,
                        name=table.name,
                        columns=[
                            ColumnResponse(
                                name=c.name,
                                data_type=c.data_type,
                                nullable=c.nullable,
                                is_primary_key=c.is_primary_key,
                                is_foreign_key=c.is_foreign_key,
                                default_value=c.default_value,
                                comment=c.comment,
                            )
                            for c in table.columns
                        ],
                        foreign_keys=[
                            ForeignKeyResponse(
                                name=fk.name,
                                columns=fk.columns,
                                referenced_schema=fk.referenced_schema,
                                referenced_table=fk.referenced_table,
                                referenced_columns=fk.referenced_columns,
                            )
                            for fk in table.foreign_keys
                        ],
                        approximate_row_count=table.approximate_row_count,
                        has_timestamp_columns=table.has_timestamp_columns,
                        fk_count=table.fk_count,
                        hint=hint,
                    )
                )

            return SchemaResponse(name=schema.name, tables=table_responses)
    except ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )


@router.get(
    "/{connection_id}/schemas/{schema_name}/tables/{table_name}",
    response_model=TableResponse,
)
async def introspect_table(
    connection_id: UUID,
    schema_name: str,
    table_name: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TableResponse:
    """Introspect a single table."""
    _, introspector = await _get_connection_and_introspector(
        connection_id, current_user, db
    )

    try:
        async with introspector:
            table = await introspector.introspect_table(schema_name, table_name)

            hint = None
            if table.has_timestamp_columns and table.fk_count >= 2:
                hint = "event-like"
            elif table.fk_count == 0:
                hint = "reference-like"

            return TableResponse(
                schema_name=table.schema_name,
                name=table.name,
                columns=[
                    ColumnResponse(
                        name=c.name,
                        data_type=c.data_type,
                        nullable=c.nullable,
                        is_primary_key=c.is_primary_key,
                        is_foreign_key=c.is_foreign_key,
                        default_value=c.default_value,
                        comment=c.comment,
                    )
                    for c in table.columns
                ],
                foreign_keys=[
                    ForeignKeyResponse(
                        name=fk.name,
                        columns=fk.columns,
                        referenced_schema=fk.referenced_schema,
                        referenced_table=fk.referenced_table,
                        referenced_columns=fk.referenced_columns,
                    )
                    for fk in table.foreign_keys
                ],
                approximate_row_count=table.approximate_row_count,
                has_timestamp_columns=table.has_timestamp_columns,
                fk_count=table.fk_count,
                hint=hint,
            )
    except ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )


@router.get(
    "/{connection_id}/schemas/{schema_name}/tables/{table_name}/preview",
    response_model=TableDataPreviewResponse,
)
async def get_table_preview(
    connection_id: UUID,
    schema_name: str,
    table_name: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(20, ge=1, le=100, description="Number of rows to preview"),
) -> TableDataPreviewResponse:
    """
    Get a preview of table data (sample rows).
    Limited to 100 rows max for performance.
    """
    _, introspector = await _get_connection_and_introspector(
        connection_id, current_user, db
    )

    try:
        async with introspector:
            columns, rows = await introspector.get_sample_data(
                schema_name, table_name, limit
            )
            return TableDataPreviewResponse(
                schema_name=schema_name,
                table_name=table_name,
                columns=columns,
                rows=rows,
                row_count=len(rows),
            )
    except ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )
