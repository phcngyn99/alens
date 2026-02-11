.PHONY: help build up down restart logs logs-backend logs-frontend logs-db clean rebuild status shell-backend shell-db test-api test test-build test-report

# Default target
help:
	@echo "Alens - Available Commands"
	@echo "=========================="
	@echo "  make build          - Build all Docker images"
	@echo "  make up             - Start all containers"
	@echo "  make down           - Stop and remove all containers"
	@echo "  make restart        - Restart all containers"
	@echo "  make rebuild        - Rebuild and restart all containers"
	@echo "  make status         - Show container status"
	@echo "  make logs           - Show logs from all containers"
	@echo "  make logs-backend   - Show backend logs"
	@echo "  make logs-frontend  - Show frontend logs"
	@echo "  make logs-db        - Show database logs"
	@echo "  make shell-backend  - Open shell in backend container"
	@echo "  make shell-db       - Open psql in database container"
	@echo "  make test-api       - Test API endpoints"
	@echo "  make test           - Run E2E Selenium tests"
	@echo "  make test-build     - Build test container"
	@echo "  make test-report    - Open test report in browser"
	@echo "  make clean          - Remove containers, images, and volumes"

# Build all images
build:
	docker-compose build

# Start all containers
up:
	docker-compose up -d

# Stop and remove containers
down:
	docker-compose down

# Restart all containers
restart: down up

# Rebuild and restart
rebuild:
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d

# Show container status
status:
	@docker-compose ps
	@echo ""
	@echo "Health Check:"
	@curl -s http://localhost:3000/api/connections/drivers | python3 -m json.tool 2>/dev/null || echo "API not responding"

# Show all logs
logs:
	docker-compose logs -f

# Show backend logs
logs-backend:
	docker-compose logs -f backend

# Show frontend logs
logs-frontend:
	docker-compose logs -f frontend

# Show database logs
logs-db:
	docker-compose logs -f db

# Open shell in backend container
shell-backend:
	docker-compose exec backend /bin/bash

# Open psql in database container
shell-db:
	docker-compose exec db psql -U alens -d alens

# Test API endpoints
test-api:
	@echo "Testing API endpoints..."
	@echo ""
	@echo "1. Health check (drivers):"
	@curl -s http://localhost:3000/api/connections/drivers | python3 -m json.tool
	@echo ""
	@echo "2. Login test:"
	@curl -s -X POST http://localhost:3000/api/auth/login \
		-H "Content-Type: application/x-www-form-urlencoded" \
		-d "username=wnkadmin&password=wnkadmin" | python3 -m json.tool

# Clean everything (containers, images, volumes)
clean:
	docker-compose down -v --rmi local
	@echo "Cleaned up containers, images, and volumes"

# Build test container
test-build:
	docker-compose build tests

# Run E2E Selenium tests
test:
	@echo "Running E2E tests..."
	@echo "Make sure the application is running (make up)"
	@mkdir -p tests/reports
	docker-compose --profile test run --rm tests

# Run specific test file
test-file:
	@echo "Usage: make test-file FILE=test_login.py"
	@mkdir -p tests/reports
	docker-compose --profile test run --rm tests pytest -v --html=reports/report.html --self-contained-html $(FILE)

# Run tests with verbose output
test-verbose:
	@mkdir -p tests/reports
	docker-compose --profile test run --rm tests pytest -v -s --html=reports/report.html --self-contained-html

# Open test report in browser (macOS)
test-report:
	@if [ -f tests/reports/report.html ]; then \
		open tests/reports/report.html; \
	else \
		echo "No test report found. Run 'make test' first."; \
	fi

# Clean test reports
test-clean:
	rm -rf tests/reports/*
	@echo "Test reports cleaned"

