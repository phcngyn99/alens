# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-02-24

### Added
- Initial production-ready release
- Multi-database support (PostgreSQL, SQL Server, DB2)
- Read-only schema introspection with Redis caching
- AI-powered dimensional model generation (OpenAI, Anthropic, Azure)
- DBML export (raw and annotated)
- JWT authentication with RBAC
- Encrypted credential storage (Fernet)
- E2E testing framework with Selenium
- Comprehensive documentation (README, PROJECT_CONTEXT, DESIGN_PRINCIPLES)
- ERD visualization library with DBeaver-style design
- Interactive schema browser with table details
- Analytical intent capture (structured forms)
- Versioned AI outputs

### ERD Features
- DBeaver-style clean, minimal design
- Jump/bridge effects for line crossings (circuit diagram style)
- Grayscale focus mode for unrelated tables
- Global settings management (colors, grayscale, opacity)
- Smart centering (most connected table, entire view)
- Zoom controls (button-only, disabled mouse/touchpad)
- Collision detection for moveable cards
- Column-specific relationship lines
- Expand/collapse table columns
- Pan and zoom with grid lines

### Changed
- Refactored ERD library following KISS and DRY principles
- Removed debug console.log statements from production code
- Removed deprecated config properties (opacity settings, duplicate bridgeSize)
- Removed unused layout property (padding)
- Added viewport dimension constants for maintainability
- Standardized jump effect using quadratic Bezier curves
- Fixed Redis cache Pydantic model serialization

### Security
- Read-only database access (no mutations)
- Encrypted credentials (Fernet symmetric encryption)
- JWT authentication with bcrypt password hashing
- RBAC (admin/user roles)
- CORS protection
- SQL injection prevention (parameterized queries)

## [0.0.1] - 2026-02-11

### Added
- Initial project setup
- Basic FastAPI backend structure
- React frontend with TypeScript
- Docker Compose deployment
- PostgreSQL application database
- Redis caching layer

