# Alens (Analytics Lens)

**Version:** 0.1.0
**Status:** Production-ready

A web application that helps design dimensional data models using AI. Connect to relational databases, introspect schemas, define analytical intent, and get AI-proposed star/snowflake schemas.

---

## 🎯 What is Alens?

Alens bridges the gap between relational databases and dimensional modeling. It:

1. **Connects** to your databases (PostgreSQL, SQL Server, DB2)
2. **Introspects** schema metadata (tables, columns, relationships)
3. **Converts** to DBML format with auto-detected patterns
4. **Captures** your analytical intent (business domain, metrics, time grain)
5. **Generates** AI-proposed dimensional models with explanations

**Key Feature:** Read-only access. Safe for production databases.

---

## 🚀 Quick Start

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

1. **Login** at http://localhost:3000
2. **Add Connection** - Connect to your database (or use the example AdventureWorks)
3. **Browse Schema** - Explore tables and relationships
4. **Define Intent** - Describe your analytical goals
5. **Configure AI** - Add your OpenAI or Anthropic API key in Settings
6. **Generate Model** - Get AI-proposed dimensional model

---

## 📋 Features

### Database Support
- ✅ PostgreSQL
- ✅ SQL Server
- ✅ IBM DB2
- 🔒 Read-only access (no mutations)
- 🔐 Encrypted credential storage

### Schema Introspection
- Tables, columns, data types
- Primary keys, foreign keys, indexes
- Approximate row counts
- Auto-detection of fact/dimension patterns
- Redis caching for performance

### AI Integration
- OpenAI (GPT-4, GPT-4 Turbo)
- Anthropic (Claude 3 Opus, Sonnet)
- Azure OpenAI
- Azure Anthropic
- Structured prompts (deterministic, reproducible)
- Versioned outputs

### Dimensional Modeling
- DBML generation (raw + annotated)
- Fact table identification
- Dimension table design
- Grain definition
- SCD (Slowly Changing Dimension) hints
- Assumptions and uncertainties

---

## 🏗️ Architecture

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

**Tech Stack:**
- **Backend:** Python 3.11, FastAPI, SQLAlchemy (async)
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS
- **Database:** PostgreSQL 15 (application storage)
- **Cache:** Redis 7
- **Deployment:** Docker Compose

---

## 📚 Documentation

- **[AI_AGENT_CONTEXT.md](AI_AGENT_CONTEXT.md)** - Comprehensive guide for AI coding agents
- **[DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md)** - Core design philosophy and patterns
- **[PROJECT_CONTEXT.md](PROJECT_CONTEXT.md)** - Detailed project structure and architecture
- **[tests/README.md](tests/README.md)** - E2E testing framework guide

---

## 🧪 Testing

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

**Test Coverage:**
- Authentication and authorization
- Database connection management
- Schema introspection
- Intent definition
- AI model generation
- Error handling

---

## 🛠️ Development

### Backend Development
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Useful Commands
```bash
make logs              # View all logs
make logs-backend      # Backend logs only
make shell-backend     # Open backend shell
make shell-db          # Open PostgreSQL shell
make rebuild           # Rebuild all containers
make clean             # Remove all containers/volumes
```

---

## 🔐 Security

- **Read-only database access** - No mutations on target databases
- **Encrypted credentials** - Fernet symmetric encryption
- **JWT authentication** - Secure token-based auth
- **RBAC** - Role-based access control (admin/user)
- **CORS protection** - Configurable allowed origins
- **SQL injection prevention** - Parameterized queries only

---

## 🎨 Design Philosophy

### Core Principles
1. **KISS** - Keep logic explicit and readable
2. **DRY** - Shared abstractions for database connectors
3. **Deterministic** - Same inputs → same outputs
4. **Read-only** - No database mutations, ever
5. **Explicit consent** - No background jobs without user action

### UI/UX
- Apple-style simplicity
- Light theme (clean, professional)
- Structured forms over free-form chat
- Sensible defaults
- Progressive disclosure

See [DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md) for details.

---

## 🔄 Workflow

1. **Connect** - Add database connection with credentials
2. **Explore** - Browse schemas, tables, relationships
3. **Select** - Choose tables of interest
4. **Define** - Capture analytical intent (structured form)
5. **Generate** - AI proposes dimensional model
6. **Review** - Examine fact tables, dimensions, grain
7. **Download** - Export DBML, explanations, diagrams

---

## 📦 Project Structure

```
alens/
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── api/      # API routes
│   │   ├── auth/     # Authentication
│   │   ├── core/     # Business logic
│   │   ├── storage/  # Database models
│   │   └── main.py   # Entry point
│   └── requirements.txt
├── frontend/          # React frontend
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── types/
│   └── package.json
├── tests/             # E2E tests (Selenium)
├── docker-compose.yml
└── Makefile
```

---

## 🤝 Contributing

1. Read [DESIGN_PRINCIPLES.md](DESIGN_PRINCIPLES.md)
2. Review [AI_AGENT_CONTEXT.md](AI_AGENT_CONTEXT.md)
3. Follow existing code patterns
4. Add tests for new features
5. Update documentation

---

## 📄 License

[Specify License]

---

## 🙏 Acknowledgments

- **DBML** - Database Markup Language specification
- **Kimball** - Dimensional modeling methodology
- **FastAPI** - Modern Python web framework
- **React** - UI library

---

## 📞 Support

For issues, questions, or contributions, please refer to the documentation files or open an issue.

---

**Built with ❤️ for data engineers and analysts**