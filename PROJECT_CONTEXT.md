# Alens (Analytics Lens) - Project Context

**Version:** 0.1.0  
**Purpose:** Production-ready web application for AI-assisted dimensional data modeling

---

## 🎯 Project Overview

Alens is a full-stack application that helps data engineers and analysts design dimensional data models (star/snowflake schemas) using AI. It connects to relational databases, introspects schema metadata, captures user analytical intent, and generates AI-proposed dimensional models.

### Core Value Proposition
- **Read-only database access** - No mutations, safe for production databases
- **Structured AI prompts** - No chat history, deterministic prompt generation
- **Multi-database support** - PostgreSQL, SQL Server, DB2
- **Caching layer** - Redis-based caching for schema introspection
- **Multi-user support** - Authentication, RBAC, encrypted credentials

---

## 🏗️ Architecture

### Technology Stack

**Backend:**
- **Framework:** FastAPI (Python 3.11+)
- **Database:** PostgreSQL 15 (application storage)
- **ORM:** SQLAlchemy 2.0 (async)
- **Cache:** Redis 7
- **AI Providers:** OpenAI, Anthropic, Azure OpenAI, Azure Anthropic
- **Database Drivers:** asyncpg (PostgreSQL), pyodbc (SQL Server), ibm-db (DB2)

**Frontend:**
- **Framework:** React 18 + TypeScript
- **Build Tool:** Vite
- **Routing:** React Router v6
- **State Management:** Zustand
- **HTTP Client:** Axios
- **Styling:** Tailwind CSS
- **Icons:** Lucide React

**Infrastructure:**
- **Containerization:** Docker + Docker Compose
- **Web Server:** Nginx (frontend)
- **ASGI Server:** Uvicorn (backend)

### Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Network                          │
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐            │
│  │ Frontend │───▶│ Backend  │───▶│   DB     │            │
│  │  Nginx   │    │  FastAPI │    │PostgreSQL│            │
│  │  :3000   │    │  :8080   │    │  :5432   │            │
│  └──────────┘    └──────────┘    └──────────┘            │
│                        │                                   │
│                        ▼                                   │
│                  ┌──────────┐                             │
│                  │  Redis   │                             │
│                  │  :6379   │                             │
│                  └──────────┘                             │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  Test Profile (optional)                             │ │
│  │  ┌──────────────┐    ┌──────────────┐               │ │
│  │  │ SQL Server   │    │   Selenium   │               │ │
│  │  │AdventureWorks│    │    Tests     │               │ │
│  │  │    :1433     │    │              │               │ │
│  │  └──────────────┘    └──────────────┘               │ │
│  └──────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 📂 Project Structure

```
alens/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/               # API routes
│   │   │   ├── routes/
│   │   │   │   ├── auth.py           # Authentication endpoints
│   │   │   │   ├── users.py          # User management
│   │   │   │   ├── connections.py    # Database connections
│   │   │   │   ├── introspection.py  # Schema introspection
│   │   │   │   ├── intent.py         # Analytical intent capture
│   │   │   │   └── ai.py             # AI model generation
│   │   │   └── schemas.py     # Pydantic request/response models
│   │   ├── auth/              # Authentication & security
│   │   │   ├── dependencies.py       # Auth dependencies
│   │   │   ├── encryption.py         # Fernet encryption
│   │   │   ├── security.py           # JWT, bcrypt
│   │   │   └── service.py            # User service
│   │   ├── core/              # Business logic
│   │   │   ├── ai/
│   │   │   │   ├── adapter.py        # AI provider adapter
│   │   │   │   └── prompt_builder.py # Structured prompt generation
│   │   │   ├── exporters/
│   │   │   │   └── dbml.py           # DBML exporter
│   │   │   ├── introspect/
│   │   │   │   ├── base.py           # Base introspector
│   │   │   │   ├── factory.py        # Introspector factory
│   │   │   │   ├── postgresql.py     # PostgreSQL introspector
│   │   │   │   ├── sqlserver.py      # SQL Server introspector
│   │   │   │   └── db2.py            # DB2 introspector
│   │   │   ├── models/
│   │   │   │   └── schema.py         # Schema metadata models
│   │   │   ├── stats/
│   │   │   │   └── collector.py      # Statistics collector
│   │   │   └── cache.py       # Redis caching layer
│   │   ├── storage/           # Database models
│   │   │   ├── database.py           # SQLAlchemy setup
│   │   │   └── models.py             # ORM models
│   │   ├── config.py          # Application settings
│   │   └── main.py            # FastAPI app entry point
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── Layout.tsx            # Main layout
│   │   │   ├── TableDetailsPanel.tsx # Table details
│   │   │   ├── TableERD.tsx          # ERD visualization (legacy)
│   │   │   └── FullSchemaERD.tsx     # Full schema ERD with new library
│   │   ├── lib/
│   │   │   └── erd/              # Reusable ERD library
│   │   │       ├── components/
│   │   │       │   ├── ERDCanvas.tsx      # SVG canvas
│   │   │       │   ├── ERDContainer.tsx   # Main container
│   │   │       │   ├── ERDNode.tsx        # Table node
│   │   │       │   └── ERDRelationship.tsx # Relationship lines
│   │   │       ├── context/
│   │   │       │   └── ERDContext.tsx     # React Context for state
│   │   │       ├── hooks/
│   │   │       │   ├── useDragging.ts     # Drag & drop
│   │   │       │   ├── useExpand.ts       # Expand/collapse
│   │   │       │   ├── usePanZoom.ts      # Pan & zoom
│   │   │       │   └── useSelection.ts    # Table selection
│   │   │       ├── config.ts         # Default configuration
│   │   │       ├── types.ts          # TypeScript types
│   │   │       ├── utils.ts          # Layout & path generation
│   │   │       └── index.ts          # Public API
│   │   ├── hooks/
│   │   │   └── useAuth.ts            # Auth hook
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx         # Login
│   │   │   ├── ConnectionsPage.tsx   # Connections list
│   │   │   ├── SchemaPage.tsx        # Schema browser
│   │   │   ├── IntentPage.tsx        # Intent definition
│   │   │   ├── GeneratePage.tsx      # AI generation
│   │   │   └── SettingsPage.tsx      # Settings (includes ERD settings)
│   │   ├── services/
│   │   │   └── api.ts                # API client
│   │   ├── types/
│   │   │   └── index.ts              # TypeScript types
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   └── vite.config.ts
│
├── tests/                      # E2E testing
│   ├── pages/                 # Page Object Model
│   │   ├── base_page.py
│   │   ├── login_page.py
│   │   ├── connections_page.py
│   │   ├── schema_page.py
│   │   └── intent_page.py
│   ├── sqlserver/             # AdventureWorks test DB
│   ├── conftest.py            # Pytest fixtures
│   ├── test_login.py
│   ├── test_connections.py
│   ├── test_schema_browser.py
│   ├── test_intent_page.py
│   ├── test_error_handling.py
│   ├── test_adventureworks_integration.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── docker-compose.yml
├── Makefile
└── README.md
```

---

## 🔄 Application Workflow

### 1. User Authentication
- JWT-based authentication with bcrypt password hashing
- Default admin user: `wnkadmin` / `wnkadmin`
- Role-based access control (RBAC): `admin` and `user` roles
- Token stored in localStorage, auto-refresh on 401

### 2. Database Connection Management
- Users create database connections with encrypted credentials
- Supported databases: PostgreSQL, SQL Server, DB2
- Credentials encrypted using Fernet (symmetric encryption)
- Schema whitelist support for limiting introspection scope
- Connection testing before saving

### 3. Schema Introspection
- **Read-only** database access via system catalogs
- Introspects: schemas, tables, columns, primary keys, foreign keys, indexes
- Auto-detection of timestamp columns and FK patterns
- Redis caching (5-minute TTL for schemas, 1-minute for data previews)
- Supports approximate row counts and table statistics

### 4. Intent Definition
- Structured capture of analytical requirements:
  - **Business Domain**: e.g., "Sales Analytics", "HR Reporting"
  - **Analytical Goal**: `reporting`, `bi`, or `ad-hoc`
  - **Time Grain**: `daily`, `weekly`, or `monthly`
  - **Key Metrics**: List of metrics to track
  - **Tables of Interest**: User-selected tables with fact/dimension hints
  - **Exclusions**: Tables/schemas to exclude from modeling
- Versioned intents (each new intent increments version)

### 5. DBML Generation
- Converts introspected schema to DBML (Database Markup Language)
- Two outputs:
  - **Raw DBML**: Exact schema representation
  - **Annotated DBML**: Includes user hints and auto-detected patterns
- Auto-annotations:
  - Tables with timestamp columns → "may be event-like"
  - Tables with no FKs → "may be reference/lookup table"
  - Tables with 3+ FKs → "may be fact table"

### 6. AI Model Generation
- Structured prompt generation (no chat history)
- Prompt includes:
  - User intent (business domain, goals, metrics)
  - Tables of interest with hints
  - Raw and annotated DBML
  - Optional statistics
- AI providers supported:
  - **OpenAI**: GPT-4 Turbo, GPT-4
  - **Anthropic**: Claude 3 Opus, Claude 3 Sonnet
  - **Azure OpenAI**: Custom deployments
  - **Azure Anthropic**: Azure AI Services
- AI response parsing:
  - Model explanation (fact tables, grain, measures)
  - Dimension details (attributes, SCD strategies)
  - Assumptions and uncertainties
  - Dimensional DBML output
- Versioned outputs (multiple generations per intent)

---

## 🗄️ Database Schema (Application Storage)

### Users Table
```sql
users (
  id UUID PRIMARY KEY,
  username VARCHAR(100) UNIQUE,
  hashed_password VARCHAR(255),
  role VARCHAR(20),  -- 'admin' or 'user'
  is_active BOOLEAN,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)
```

### Database Connections Table
```sql
database_connections (
  id UUID PRIMARY KEY,
  owner_id UUID REFERENCES users(id),
  name VARCHAR(100),
  db_type VARCHAR(50),  -- 'postgresql', 'sqlserver', 'db2'
  host VARCHAR(255),
  port INTEGER,
  database_name VARCHAR(100),
  username VARCHAR(100),
  encrypted_password TEXT,  -- Fernet encrypted
  schema_whitelist JSON,    -- Optional list of schemas
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)
```

### Analytical Intents Table
```sql
analytical_intents (
  id UUID PRIMARY KEY,
  connection_id UUID REFERENCES database_connections(id),
  version INTEGER,
  business_domain TEXT,
  analytical_goal VARCHAR(50),  -- 'reporting', 'bi', 'ad-hoc'
  time_grain VARCHAR(50),       -- 'daily', 'weekly', 'monthly'
  key_metrics JSON,             -- List of metric names
  tables_of_interest JSON,      -- List with fact/dimension hints
  exclusions JSON,              -- Tables/schemas to exclude
  created_at TIMESTAMP
)
```

### AI Outputs Table
```sql
ai_outputs (
  id UUID PRIMARY KEY,
  intent_id UUID REFERENCES analytical_intents(id),
  version INTEGER,
  model_explanation TEXT,
  dimension_details JSON,
  assumptions TEXT,
  dimensional_dbml TEXT,
  ai_provider VARCHAR(50),
  ai_model VARCHAR(100),
  prompt_tokens INTEGER,
  completion_tokens INTEGER,
  created_at TIMESTAMP
)
```

### AI Credentials Table
```sql
ai_credentials (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  provider VARCHAR(50),  -- 'openai', 'anthropic', 'azure_openai', 'azure_anthropic'
  encrypted_api_key TEXT,
  model_name VARCHAR(100),
  max_tokens INTEGER,
  endpoint_url VARCHAR(500),      -- Azure only
  deployment_name VARCHAR(100),   -- Azure only
  api_version VARCHAR(50),        -- Azure only
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)
```

---

## 🔌 API Endpoints

### Authentication (`/api/auth`)
- `POST /login` - Login with username/password (returns JWT)

### Users (`/api/users`)
- `GET /me` - Get current user
- `POST /me/change-password` - Change password
- `GET /` - List all users (admin only)
- `POST /` - Create user (admin only)
- `GET /{id}` - Get user by ID (admin only)
- `PATCH /{id}` - Update user (admin only)
- `DELETE /{id}` - Delete user (admin only)

### Connections (`/api/connections`)
- `GET /drivers` - Get database driver status
- `GET /` - List user's connections
- `POST /` - Create new connection
- `GET /{id}` - Get connection by ID
- `PATCH /{id}` - Update connection
- `DELETE /{id}` - Delete connection
- `POST /{id}/test` - Test connection

### Introspection (`/api/introspect`)
- `GET /{connection_id}/schemas` - List schemas
- `GET /{connection_id}/schemas/{schema_name}/tables` - List tables in schema
- `GET /{connection_id}/schemas/{schema_name}` - Introspect full schema
- `GET /{connection_id}/schemas/{schema_name}/tables/{table_name}` - Introspect table
- `GET /{connection_id}/schemas/{schema_name}/tables/{table_name}/preview` - Preview table data

### Intent (`/api/intents`)
- `POST /` - Create analytical intent
- `GET /` - List intents for connection
- `GET /{id}` - Get intent by ID

### AI (`/api/ai`)
- `POST /credentials` - Save AI credentials
- `GET /credentials` - Get user's AI credentials
- `DELETE /credentials/{id}` - Delete AI credential
- `POST /generate` - Generate dimensional model
- `GET /outputs` - List AI outputs for intent
- `GET /outputs/{id}` - Get AI output by ID

---

## 🧪 Testing Framework

### E2E Testing with Selenium
- **Framework:** Pytest + Selenium WebDriver
- **Browser:** Chromium (headless)
- **Pattern:** Page Object Model (POM)
- **Reports:** HTML reports with pytest-html

### Test Coverage
1. **Login Tests** - Authentication flow, error handling
2. **Connections Tests** - CRUD operations, connection testing
3. **Schema Browser Tests** - Schema/table introspection, error handling
4. **Intent Page Tests** - Intent definition, table selection
5. **Error Handling Tests** - 401/404/503 responses, validation errors
6. **AdventureWorks Integration** - Full workflow with test database

### Running Tests
```bash
make up              # Start application
make test-build      # Build test container (first time)
make test            # Run all tests
make test-report     # Open HTML report
make test-verbose    # Run with verbose output
make test-file FILE=test_login.py  # Run specific test
```

---

## 🔐 Security Features

### Authentication & Authorization
- JWT tokens with configurable expiration (default: 24 hours)
- Bcrypt password hashing with salt
- Role-based access control (RBAC)
- Protected routes with dependency injection

### Encryption
- **Database passwords**: Fernet symmetric encryption
- **AI API keys**: Fernet symmetric encryption
- **Encryption key**: Configurable via environment variable

### Database Security
- **Read-only access**: No INSERT/UPDATE/DELETE operations
- **Parameterized queries**: SQL injection prevention
- **Schema whitelisting**: Limit introspection scope
- **Connection pooling**: Pre-ping for stale connections

### CORS
- Configurable allowed origins
- Credentials support enabled
- All methods and headers allowed (configurable)

---

## ⚙️ Configuration

### Environment Variables

**Backend (`backend/app/config.py`):**
```bash
# Application
APP_NAME=Alens
APP_VERSION=0.1.0
DEBUG=false

# Database (application storage)
DATABASE_URL=postgresql+asyncpg://alens:alens@db:5432/alens

# Security
SECRET_KEY=change-this-in-production
ENCRYPTION_KEY=change-this-32-byte-key
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Default admin user
DEFAULT_USERNAME=wnkadmin
DEFAULT_PASSWORD=wnkadmin

# AI Configuration
AI_PROVIDER=openai  # or 'anthropic'
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
AI_MODEL=gpt-4-turbo-preview
AI_MAX_TOKENS=4096
AI_TEMPERATURE=0.1

# Redis
REDIS_URL=redis://redis:6379/0
CACHE_TTL_SECONDS=300
CACHE_PREVIEW_TTL_SECONDS=60

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

**Docker Compose:**
```bash
# SQL Server (test profile)
SQLSERVER_HOST=sqlserver-test
MSSQL_SA_PASSWORD=YourPassword123!

# Test environment
BASE_URL=http://frontend
API_URL=http://backend:8000
HEADLESS=true
```

---

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Make (optional, for convenience commands)

### Installation & Startup
```bash
# Clone repository
git clone <repository-url>
cd alens

# Start all services
make up
# OR
docker-compose up -d

# Check status
make status

# View logs
make logs
make logs-backend
make logs-frontend
```

### Access Application
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8080
- **API Docs:** http://localhost:8080/docs
- **Default Login:** `wnkadmin` / `wnkadmin`

### Development Workflow
```bash
# Backend development
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend development
cd frontend
npm install
npm run dev

# Run tests
make test
make test-report
```

---

## 📊 Key Design Decisions

### 1. Read-Only Database Access
- **Why:** Safety for production databases, no risk of data mutation
- **How:** Only SELECT queries, no DML operations
- **Trade-off:** Cannot create test tables or modify data

### 2. Structured Prompts (No Chat History)
- **Why:** Deterministic, reproducible, version-controlled
- **How:** Build prompts from structured intent + DBML
- **Trade-off:** Less conversational, requires upfront intent definition

### 3. Redis Caching
- **Why:** Reduce database load, improve response times
- **How:** TTL-based caching with pattern-based invalidation
- **Trade-off:** Potential stale data, requires Redis infrastructure

### 4. Versioned Intents & Outputs
- **Why:** Track evolution of requirements and AI responses
- **How:** Auto-increment version on each creation
- **Trade-off:** More storage, no update operations

### 5. Encrypted Credentials
- **Why:** Secure storage of sensitive data
- **How:** Fernet symmetric encryption
- **Trade-off:** Requires secure key management

### 6. Multi-Provider AI Support
- **Why:** Flexibility, avoid vendor lock-in
- **How:** Adapter pattern with provider-specific implementations
- **Trade-off:** More complex code, testing overhead

---

## 🐛 Known Limitations

1. **DB2 Support:** Requires manual installation of `ibm-db` driver
2. **No Real-Time Collaboration:** Single-user editing of intents
3. **No DBML Validation:** AI-generated DBML not validated before storage
4. **Limited Statistics:** Approximate row counts only (no histograms)
5. **No Schema Diff:** Cannot compare schema versions over time
6. **Single AI Call:** No iterative refinement of dimensional models

---

## 🔮 Future Enhancements

- [ ] Real-time collaboration with WebSockets
- [ ] DBML validation and syntax highlighting
- [ ] Schema version tracking and diff visualization
- [ ] Iterative AI refinement with feedback loops
- [ ] Export to dbt, Looker, Tableau
- [ ] Data profiling and quality metrics
- [ ] Automated SCD implementation suggestions
- [ ] Integration with data catalogs (Alation, Collibra)

---

## 📝 Development Notes for AI Agents

### When Adding New Features

1. **Backend Changes:**
   - Add route in `backend/app/api/routes/`
   - Add Pydantic schemas in `backend/app/api/schemas.py`
   - Add database model in `backend/app/storage/models.py`
   - Update dependencies in `backend/app/auth/dependencies.py` if needed
   - Add caching logic in `backend/app/core/cache.py` if applicable

2. **Frontend Changes:**
   - Add TypeScript types in `frontend/src/types/index.ts`
   - Add API methods in `frontend/src/services/api.ts`
   - Create page component in `frontend/src/pages/`
   - Add route in `frontend/src/App.tsx`
   - Update navigation in `frontend/src/components/Layout.tsx`

3. **Testing:**
   - Add E2E test in `tests/test_*.py`
   - Create page object in `tests/pages/*.py` if needed
   - Update `tests/conftest.py` for new fixtures

### Code Style Guidelines

**Backend:**
- Use async/await for all I/O operations
- Type hints required for all functions
- Docstrings for public APIs
- Pydantic for validation
- Dependency injection for database sessions

**Frontend:**
- TypeScript strict mode
- Functional components with hooks
- Axios for API calls
- Tailwind for styling
- React Query for data fetching (if added)

### Database Introspection Pattern

```python
# 1. Get introspector from factory
introspector = get_introspector(db_type, config)

# 2. Use context manager
async with introspector:
    # 3. Get schemas
    schemas = await introspector.get_schemas()

    # 4. Introspect schema
    schema = await introspector.introspect_schema(schema_name)

    # 5. Access tables
    for table in schema.tables:
        print(table.name, table.columns)
```

### AI Prompt Building Pattern

```python
# 1. Build user intent
user_intent = UserIntent(
    business_domain="Sales",
    analytical_goal="reporting",
    time_grain="daily",
    key_metrics=["revenue", "orders"],
    tables_of_interest=[...],
    exclusions=[]
)

# 2. Generate DBML
exporter = DBMLExporter(schema)
raw_dbml = exporter.export_raw()
annotated_dbml = exporter.export_annotated()

# 3. Build payload
payload = PromptPayload(
    raw_dbml=raw_dbml,
    annotated_dbml=annotated_dbml,
    user_intent=user_intent
)

# 4. Call AI
adapter = AIAdapter(provider, api_key, model)
response = await adapter.generate_dimensional_model(payload)
```

---

## 📚 Additional Resources

- **DBML Specification:** https://dbml.dbdiagram.io/docs/
- **Dimensional Modeling:** Kimball's "The Data Warehouse Toolkit"
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **React Router:** https://reactrouter.com/
- **SQLAlchemy Async:** https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html

---

## 🛠️ Common Development Tasks

### Adding a New Database Type

1. **Create introspector** in `backend/app/core/introspect/newdb.py`:
```python
from .base import BaseIntrospector

class NewDBIntrospector(BaseIntrospector):
    @property
    def db_type(self) -> str:
        return "newdb"

    async def connect(self):
        # Implementation
        pass

    # Implement all abstract methods
```

2. **Register in factory** (`backend/app/core/introspect/factory.py`):
```python
INTROSPECTOR_REGISTRY["newdb"] = NewDBIntrospector
```

3. **Update frontend types** (`frontend/src/types/index.ts`):
```typescript
export type DatabaseType = 'postgresql' | 'sqlserver' | 'db2' | 'newdb';
```

### Adding a New API Endpoint

1. **Define schemas** (`backend/app/api/schemas.py`):
```python
class NewFeatureRequest(BaseModel):
    field: str

class NewFeatureResponse(BaseModel):
    id: UUID
    result: str
```

2. **Create route** (`backend/app/api/routes/new_feature.py`):
```python
router = APIRouter(prefix="/new-feature", tags=["New Feature"])

@router.post("", response_model=NewFeatureResponse)
async def create_feature(
    request: NewFeatureRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Implementation
    return NewFeatureResponse(id=..., result=...)
```

3. **Register router** (`backend/app/main.py`):
```python
from app.api.routes import new_feature
app.include_router(new_feature.router, prefix="/api")
```

4. **Add frontend API method** (`frontend/src/services/api.ts`):
```typescript
export const newFeature = {
  create: async (request: NewFeatureRequest): Promise<NewFeatureResponse> => {
    const { data } = await api.post('/new-feature', request);
    return data;
  },
};
```

### Adding a New AI Provider

1. **Add provider method** (`backend/app/core/ai/adapter.py`):
```python
async def _call_new_provider(self, system_prompt: str, user_prompt: str) -> AIResponse:
    # Implementation
    pass
```

2. **Update generate method**:
```python
elif self.provider == "new_provider":
    return await self._call_new_provider(system_prompt, user_prompt)
```

---

## 🔍 Debugging & Troubleshooting

### Check Service Health
```bash
# Application
curl http://localhost:3000/api/connections/drivers | jq

# Backend
curl http://localhost:8080/api/health

# Database
docker-compose exec db psql -U alens -d alens -c "SELECT 1"

# Redis
docker-compose exec redis redis-cli ping
```

### View Database
```bash
# Connect to PostgreSQL
make shell-db

# List tables
\dt

# Query users
SELECT * FROM users;

# Query connections
SELECT id, name, db_type, host FROM database_connections;
```

### Common Issues

**"Connection refused" in tests**
- Solution: Ensure application is running (`make up`)

**"Driver not found" for SQL Server**
- Solution: pyodbc requires ODBC driver installation (handled in Dockerfile)

**"Encryption key error"**
- Solution: Ensure `ENCRYPTION_KEY` is set and is 32 bytes (Fernet requirement)

**Redis connection errors**
- Solution: Check Redis is running (`docker-compose ps redis`)

**CORS errors in frontend**
- Solution: Update `CORS_ORIGINS` in backend config

**Type errors in TypeScript**
- Solution: Run `npm run build` to check types before committing

---

## 📋 Code Review Checklist

Before submitting changes:
- [ ] Code follows existing patterns
- [ ] Type hints added (Python) / types defined (TypeScript)
- [ ] Docstrings added for public APIs
- [ ] Error handling implemented
- [ ] Tests added/updated
- [ ] No breaking changes (or documented)
- [ ] Security considerations addressed
- [ ] Performance implications considered
- [ ] Documentation updated
- [ ] Commit message is clear
- [ ] Read-only database access maintained
- [ ] No plaintext secrets in code

---

## 🎯 Critical Rules for Development

### MUST DO
1. ✅ **Maintain read-only database access** - Only SELECT queries
2. ✅ **Use async/await** - All I/O operations must be async
3. ✅ **Add type hints** - All functions must have type annotations
4. ✅ **Validate with Pydantic** - All API inputs/outputs use Pydantic
5. ✅ **Handle errors gracefully** - Use try/except, return meaningful errors
6. ✅ **Cache expensive operations** - Use Redis for schema introspection
7. ✅ **Encrypt sensitive data** - Use Fernet for passwords/API keys
8. ✅ **Version outputs** - Intents and AI outputs are versioned
9. ✅ **Test changes** - Add E2E tests for new features
10. ✅ **Document code** - Add docstrings and inline comments

### MUST NOT DO
1. ❌ **No database mutations** - No INSERT/UPDATE/DELETE on target databases
2. ❌ **No free-form chat** - Use structured intent, not chat history
3. ❌ **No magic/reflection** - Explicit logic only
4. ❌ **No blocking I/O** - Use async for all database/network calls
5. ❌ **No plaintext secrets** - Always encrypt credentials
6. ❌ **No auto-background jobs** - User must trigger actions explicitly
7. ❌ **No cross-user access** - Enforce user ownership
8. ❌ **No unvalidated inputs** - Always use Pydantic schemas
9. ❌ **No SQL injection** - Use parameterized queries
10. ❌ **No breaking changes** - Maintain backward compatibility

---

## 📖 Original Vision & Evolution

### What Changed from Original Prompt
1. **Storage:** SQLite → PostgreSQL (better async support, production-ready)
2. **Deployment:** Single container → Multi-container (separation of concerns)
3. **Frontend:** Simple → React + TypeScript (better DX, type safety)
4. **AI Support:** Single provider → Multi-provider (OpenAI, Anthropic, Azure)
5. **Testing:** None → Comprehensive E2E with Selenium

### What Stayed True to Original Vision
1. ✅ Read-only database access
2. ✅ Structured intent capture (not free-form chat)
3. ✅ Deterministic prompt building
4. ✅ Strategy pattern for introspection
5. ✅ DBML generation (raw + annotated)
6. ✅ Versioned outputs
7. ✅ Light theme UI
8. ✅ Clear separation of concerns
9. ✅ Security-first design
10. ✅ Explicit user actions

### Why Changes Were Made
- **PostgreSQL:** Better async support, production-ready, easier migrations
- **Multi-container:** Easier development, better scalability, clearer separation
- **TypeScript:** Type safety, better IDE support, fewer runtime errors
- **Multi-provider:** Avoid vendor lock-in, user choice, Azure support
- **E2E Testing:** Confidence in deployments, regression prevention

---

## 📊 Recent Updates

### 2026-02-24: ERD Library Refactoring
- **Cleaned up ERD library** following KISS and DRY principles
- **Removed debug console.log statements** from production code
- **Removed deprecated config properties** (opacity settings, duplicate bridgeSize)
- **Removed unused layout property** (padding)
- **Added viewport dimension constants** (DEFAULT_VIEWPORT_WIDTH, DEFAULT_VIEWPORT_HEIGHT)
- **Standardized jump effect** using quadratic Bezier curves for consistency
- **Centralized viewport dimensions** for better maintainability
- **All tests passing** (25 passed, 6 skipped)
- **No TypeScript errors**

### ERD Features
- **DBeaver-style design** - Clean, minimal visualization with blue headers
- **Jump/bridge effects** - Semicircular arcs where lines cross (circuit diagram style)
- **Grayscale focus** - Unrelated tables fade when a table is selected
- **Global settings** - ERD settings managed at app level (colors, grayscale, opacity)
- **Smart centering** - Most connected table centered, entire view centered
- **Zoom controls** - Disabled mouse/touchpad zoom, only zoom through buttons
- **Collision detection** - Moveable database cards with grid lines
- **Column-specific relationships** - Lines connect to specific columns, not just tables

---

**Last Updated:** 2026-02-24
**Maintainer:** Development Team
**License:** [Specify License]


