"""
Database introspection routes.
All operations are READ-ONLY.
Includes caching to reduce database queries.
"""

import logging
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
from app.config import get_settings
from app.core.cache import CacheKeys, get_cache
from app.core.introspect.base import ConnectionConfig
from app.core.introspect.factory import get_introspector
from app.storage.database import get_db
from app.storage.models import DatabaseConnection

logger = logging.getLogger(__name__)
settings = get_settings()
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
    """List all schemas in the database (respects whitelist). Results are cached."""
    cache = get_cache()
    cache_key = CacheKeys.schemas(connection_id)

    # Check cache first
    cached = await cache.get(cache_key)
    if cached is not None:
        logger.debug(f"Cache hit for schemas: {connection_id}")
        return cached

    _, introspector = await _get_connection_and_introspector(
        connection_id, current_user, db
    )

    try:
        async with introspector:
            schemas = await introspector.get_schemas()
            # Cache the result
            await cache.set(cache_key, schemas, settings.cache_ttl_seconds)
            logger.debug(f"Cached schemas for connection: {connection_id}")
            return schemas
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
    """List all tables in a schema. Results are cached."""
    cache = get_cache()
    cache_key = CacheKeys.tables(connection_id, schema_name)

    # Check cache first
    cached = await cache.get(cache_key)
    if cached is not None:
        logger.debug(f"Cache hit for tables: {connection_id}/{schema_name}")
        return cached

    _, introspector = await _get_connection_and_introspector(
        connection_id, current_user, db
    )

    try:
        async with introspector:
            tables = await introspector.get_tables(schema_name)
            # Cache the result
            await cache.set(cache_key, tables, settings.cache_ttl_seconds)
            logger.debug(f"Cached tables for: {connection_id}/{schema_name}")
            return tables
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
    This is an explicit action that scans the schema. Results are cached.
    """
    cache = get_cache()
    cache_key = CacheKeys.schema_detail(connection_id, schema_name, include_stats)

    # Check cache first
    cached = await cache.get(cache_key)
    if cached is not None:
        logger.debug(f"Cache hit for schema detail: {connection_id}/{schema_name}")
        return cached

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

            response = SchemaResponse(name=schema.name, tables=table_responses)
            # Cache the result
            await cache.set(cache_key, response, settings.cache_ttl_seconds)
            logger.debug(f"Cached schema detail for: {connection_id}/{schema_name}")
            return response
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
    """Introspect a single table. Results are cached."""
    cache = get_cache()
    cache_key = CacheKeys.table_detail(connection_id, schema_name, table_name)

    # Check cache first
    cached = await cache.get(cache_key)
    if cached is not None:
        logger.debug(f"Cache hit for table: {connection_id}/{schema_name}/{table_name}")
        return cached

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

            response = TableResponse(
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
            # Cache the result
            await cache.set(cache_key, response, settings.cache_ttl_seconds)
            logger.debug(
                f"Cached table detail for: {connection_id}/{schema_name}/{table_name}"
            )
            return response
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
    Limited to 100 rows max for performance. Results are cached with shorter TTL.
    """
    cache = get_cache()
    cache_key = CacheKeys.table_preview(connection_id, schema_name, table_name, limit)

    # Check cache first
    cached = await cache.get(cache_key)
    if cached is not None:
        logger.debug(
            f"Cache hit for preview: {connection_id}/{schema_name}/{table_name}"
        )
        return cached

    _, introspector = await _get_connection_and_introspector(
        connection_id, current_user, db
    )

    try:
        async with introspector:
            columns, rows = await introspector.get_sample_data(
                schema_name, table_name, limit
            )
            response = TableDataPreviewResponse(
                schema_name=schema_name,
                table_name=table_name,
                columns=columns,
                rows=rows,
                row_count=len(rows),
            )
            # Cache with shorter TTL since data changes more often
            await cache.set(cache_key, response, settings.cache_preview_ttl_seconds)
            logger.debug(
                f"Cached preview for: {connection_id}/{schema_name}/{table_name}"
            )
            return response
    except ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )
