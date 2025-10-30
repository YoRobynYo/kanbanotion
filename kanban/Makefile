.PHONY: help install dev test build clean docker-build docker-run docker-dev

# Default target
help:
	@echo "Available commands:"
	@echo "  install     - Install dependencies"
	@echo "  dev         - Run development server"
	@echo "  test        - Run tests"
	@echo "  build       - Build for production"
	@echo "  clean       - Clean build artifacts"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run  - Run with Docker Compose"
	@echo "  docker-dev  - Run development with Docker"

# Python environment setup
install:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

# Development
dev:
	.venv/bin/uvicorn app.main:app --reload --port 8000

# Testing
test:
	.venv/bin/pytest tests/ -v --cov=app --cov-report=html

# Production build
build:
	.venv/bin/python -m compileall app/

# Clean
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .coverage htmlcov/ .pytest_cache/

# Docker commands
docker-build:
	docker build -t maiway-backend .

docker-run:
	docker-compose up -d

docker-dev:
	docker-compose -f docker-compose.dev.yml up

docker-stop:
	docker-compose down

docker-logs:
	docker-compose logs -f backend

# Database commands
db-migrate:
	.venv/bin/alembic upgrade head

db-reset:
	rm -f dev.db
	.venv/bin/python -c "from app.db import init_db; init_db()"

# Linting and formatting
lint:
	.venv/bin/flake8 app/
	.venv/bin/black --check app/

format:
	.venv/bin/black app/
	.venv/bin/isort app/

# Security
security-check:
	.venv/bin/bandit -r app/
	.venv/bin/safety check