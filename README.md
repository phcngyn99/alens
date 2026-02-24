# Alens (Analytics Lens)

**Version:** 0.1.0
**Status:** Production-ready

A web application that helps design dimensional data models using AI. Connect to relational databases, introspect schemas, define analytical intent, and get AI-proposed star/snowflake schemas.

**Key Feature:** Read-only access. Safe for production databases.

## Quick Start

### Prerequisites
- Docker and Docker Compose
- (Optional) Make for convenience commands

### Start the Application

```bash
# Clone the repository
git clone <repository-url>
cd alens

# Start all services
make up
# OR
docker-compose up -d

# Check status
make status

# Access the application
open http://localhost:3000
```

**Default Login:**
- Username: `wnkadmin`
- Password: `wnkadmin`

### Your First Dimensional Model

1. Login at http://localhost:3000 (default: `wnkadmin` / `wnkadmin`)
2. Add database connection
3. Browse schema and explore tables
4. Define analytical intent
5. Configure AI provider in Settings
6. Generate dimensional model

## Features

- **Database Support:** PostgreSQL, SQL Server, DB2 (read-only)
- **Schema Introspection:** Tables, columns, keys, indexes with Redis caching
- **AI Integration:** OpenAI, Anthropic, Azure (structured prompts, versioned outputs)
- **Dimensional Modeling:** DBML generation, fact/dimension identification, SCD hints
- **ERD Visualization:** DBeaver-style design with interactive features
- **Security:** Encrypted credentials, JWT auth, RBAC

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Frontend   │────▶│   Backend   │────▶│ PostgreSQL  │
│   React     │     │   FastAPI   │     │  (App DB)   │
│   :3000     │     │   :8080     │     │   :5432     │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │    Redis    │
                    │   (Cache)   │
                    │   :6379     │
                    └─────────────┘
```

**Tech Stack:** Python 3.11, FastAPI, React 18, TypeScript, PostgreSQL 15, Redis 7, Docker Compose

## Documentation

- [CHANGELOG.md](CHANGELOG.md) - Version history and release notes
- [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) - Detailed project structure and architecture
- [DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md) - Core design philosophy and patterns
- [AI_AGENT_CONTEXT.md](AI_AGENT_CONTEXT.md) - Guide for AI coding agents
- [tests/README.md](tests/README.md) - E2E testing framework

## Testing

```bash
# Run E2E tests
make test

# View test report
make test-report

# Run specific test
make test-file FILE=test_login.py

# Verbose output
make test-verbose
```

## Development

```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev

# Useful commands
make logs              # View all logs
make shell-backend     # Open backend shell
make shell-db          # Open PostgreSQL shell
make rebuild           # Rebuild containers
make clean             # Remove containers/volumes
```

## Security

- Read-only database access (no mutations)
- Encrypted credentials (Fernet)
- JWT authentication with RBAC
- CORS protection
- SQL injection prevention

## Contributing

1. Read [DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md)
2. Follow existing code patterns
3. Add tests for new features
4. Update [CHANGELOG.md](CHANGELOG.md)

## License

[Specify License]

---

Built for data engineers and analysts
