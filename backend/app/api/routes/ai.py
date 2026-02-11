"""
AI integration routes.
Handles model generation and AI credential management.
"""

import re
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    AICredentialCreate,
    AICredentialResponse,
    AIOutputResponse,
    GenerateModelRequest,
)
from app.auth.dependencies import CurrentUser
from app.auth.encryption import decrypt_value, encrypt_value
from app.core.ai.adapter import AIAdapter
from app.core.ai.prompt_builder import PromptPayload, UserIntent
from app.core.exporters.dbml import DBMLExporter, TableAnnotation
from app.core.introspect.base import ConnectionConfig
from app.core.introspect.factory import get_introspector
from app.storage.database import get_db
from app.storage.models import (
    AICredential,
    AIOutput,
    AnalyticalIntent,
    DatabaseConnection,
)

router = APIRouter(prefix="/ai", tags=["AI Integration"])


@router.post(
    "/credentials",
    response_model=AICredentialResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_ai_credential(
    credential: AICredentialCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AICredentialResponse:
    """
    Store AI API credentials (encrypted).

    For Azure providers, endpoint_url and api_version are required.
    """
    # Validate Azure-specific fields
    if credential.provider in ("azure_openai", "azure_anthropic"):
        if not credential.endpoint_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="endpoint_url is required for Azure providers",
            )
        if not credential.api_version:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="api_version is required for Azure providers",
            )

    db_credential = AICredential(
        user_id=current_user.id,
        provider=credential.provider,
        encrypted_api_key=encrypt_value(credential.api_key),
        model_name=credential.model_name,
        max_tokens=credential.max_tokens,
        endpoint_url=credential.endpoint_url,
        deployment_name=credential.deployment_name or credential.model_name,
        api_version=credential.api_version,
    )

    db.add(db_credential)
    await db.commit()
    await db.refresh(db_credential)

    return AICredentialResponse.model_validate(db_credential)


@router.get("/credentials", response_model=list[AICredentialResponse])
async def list_ai_credentials(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[AICredentialResponse]:
    """List AI credentials (without API keys)."""
    result = await db.execute(
        select(AICredential).where(AICredential.user_id == current_user.id)
    )
    credentials = result.scalars().all()
    return [AICredentialResponse.model_validate(c) for c in credentials]


@router.post("/generate", response_model=AIOutputResponse)
async def generate_dimensional_model(
    request: GenerateModelRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AIOutputResponse:
    """
    Generate a dimensional model using AI.

    This is an explicit action that:
    1. Retrieves the intent and connection
    2. Introspects the schema
    3. Generates DBML
    4. Calls the AI with a structured prompt
    5. Stores and returns the result
    """
    # Get intent
    result = await db.execute(
        select(AnalyticalIntent)
        .join(DatabaseConnection)
        .where(
            AnalyticalIntent.id == request.intent_id,
            DatabaseConnection.owner_id == current_user.id,
        )
    )
    intent = result.scalar_one_or_none()

    if not intent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Intent not found"
        )

    # Get connection
    result = await db.execute(
        select(DatabaseConnection).where(DatabaseConnection.id == intent.connection_id)
    )
    connection = result.scalar_one_or_none()

    # Get AI credentials
    result = await db.execute(
        select(AICredential).where(AICredential.user_id == current_user.id)
    )
    credential = result.scalar_one_or_none()

    if not credential:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No AI credentials configured. Please add API credentials first.",
        )

    # Introspect schema and generate DBML
    config = ConnectionConfig(
        host=connection.host,
        port=connection.port,
        database=connection.database_name,
        username=connection.username,
        password=decrypt_value(connection.encrypted_password),
        schema_whitelist=connection.schema_whitelist,
    )

    introspector = get_introspector(connection.db_type, config)

    async with introspector:
        # Get schemas and introspect
        schemas = await introspector.get_schemas()
        all_tables = []

        for schema_name in schemas:
            schema = await introspector.introspect_schema(schema_name)
            all_tables.extend(schema.tables)

        # Create DBML exporter with first schema (simplified)
        if schemas:
            schema = await introspector.introspect_schema(schemas[0])
            exporter = DBMLExporter(schema)

            # Add annotations from intent
            for table_info in intent.tables_of_interest:
                exporter.add_annotation(
                    TableAnnotation(
                        table_name=table_info["name"],
                        is_likely_fact=table_info.get("is_likely_fact", False),
                        is_likely_dimension=table_info.get(
                            "is_likely_dimension", False
                        ),
                        description=table_info.get("description"),
                    )
                )

            raw_dbml = exporter.export_raw()
            annotated_dbml = exporter.export_annotated()
        else:
            raw_dbml = "// No schemas found"
            annotated_dbml = "// No schemas found"

    # Build prompt payload
    user_intent = UserIntent(
        business_domain=intent.business_domain,
        analytical_goal=intent.analytical_goal,
        time_grain=intent.time_grain,
        key_metrics=intent.key_metrics,
        tables_of_interest=intent.tables_of_interest,
        exclusions=intent.exclusions,
    )

    payload = PromptPayload(
        raw_dbml=raw_dbml,
        annotated_dbml=annotated_dbml,
        user_intent=user_intent,
    )

    # Call AI with Azure-specific parameters if applicable
    adapter = AIAdapter(
        provider=credential.provider,
        api_key=decrypt_value(credential.encrypted_api_key),
        model=credential.model_name,
        max_tokens=credential.max_tokens,
        endpoint_url=credential.endpoint_url,
        deployment_name=credential.deployment_name,
        api_version=credential.api_version,
    )

    ai_response = await adapter.generate_dimensional_model(payload)

    # Parse AI response to extract sections
    content = ai_response.content
    dbml_match = re.search(r"```dbml\n(.*?)```", content, re.DOTALL)
    dimensional_dbml = dbml_match.group(1) if dbml_match else ""

    # Get next version
    result = await db.execute(
        select(func.max(AIOutput.version)).where(AIOutput.intent_id == intent.id)
    )
    max_version = result.scalar() or 0

    # Store output
    ai_output = AIOutput(
        intent_id=intent.id,
        version=max_version + 1,
        model_explanation=content,
        dimension_details={},  # Could parse from response
        assumptions="",  # Could parse from response
        dimensional_dbml=dimensional_dbml,
        ai_provider=ai_response.provider,
        ai_model=ai_response.model,
        prompt_tokens=ai_response.prompt_tokens,
        completion_tokens=ai_response.completion_tokens,
    )

    db.add(ai_output)
    await db.commit()
    await db.refresh(ai_output)

    return AIOutputResponse.model_validate(ai_output)
