"""
Alens - Analytics Lens Application
Main FastAPI application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import select

from app.api.routes import ai, auth, connections, intent, introspection, users
from app.auth.encryption import encrypt_value
from app.auth.service import create_default_user, get_user_by_username
from app.config import get_settings
from app.storage.database import async_session_maker, init_db
from app.storage.models import DatabaseConnection

settings = get_settings()


async def create_example_connection(session, user_id):
    """
    Create an example AdventureWorks SQL Server connection if it doesn't exist.
    This provides a demo connection for testing the application flow.
    """
    # Check if example connection already exists
    result = await session.execute(
        select(DatabaseConnection).where(
            DatabaseConnection.name == "AdventureWorks (Example)"
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        return None

    # Create example AdventureWorks connection
    # When running with test profile, sqlserver-test container is available
    # Otherwise, this will show a connection error in the UI
    import os

    sqlserver_host = os.environ.get("SQLSERVER_HOST", "sqlserver-test")

    example_conn = DatabaseConnection(
        owner_id=user_id,
        name="AdventureWorks (Example)",
        db_type="sqlserver",
        host=sqlserver_host,  # Uses sqlserver-test container when running tests
        port=1433,
        database_name="AdventureWorks2022",
        username="sa",
        encrypted_password=encrypt_value("YourPassword123!"),
        schema_whitelist=[
            "HumanResources",
            "Person",
            "Production",
            "Purchasing",
            "Sales",
        ],
    )
    session.add(example_conn)
    await session.commit()
    return example_conn


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Initializes database and creates default user on startup.
    """
    # Startup
    await init_db()

    # Create default admin user and example connection
    async with async_session_maker() as session:
        user = await create_default_user(session)
        if user:
            print(f"Created default user: {settings.default_username}")

        # Create example connection for the default user
        admin_user = await get_user_by_username(session, settings.default_username)
        if admin_user:
            example_conn = await create_example_connection(session, admin_user.id)
            if example_conn:
                print("Created example AdventureWorks connection")

    yield

    # Shutdown (cleanup if needed)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    Alens (Analytics Lens) - A production-ready web application that connects to
    relational databases, introspects schema metadata, converts it to DBML, captures
    user analytical intent, and uses AI to propose dimensional models.

    **Read-only access only. No database mutation.**
    """,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(connections.router, prefix="/api")
app.include_router(introspection.router, prefix="/api")
app.include_router(intent.router, prefix="/api")
app.include_router(ai.router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "healthy",
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
