.PHONY: help build up down logs test db-reset db-migrate clean install seed celery-logs shell db-shell

help:
	@echo "JHA ML Platform - Available Commands"
	@echo "===================================="
	@echo "make build          - Build Docker image"
	@echo "make up             - Start Docker containers"
	@echo "make up-d           - Start Docker containers (detached)"
	@echo "make down           - Stop Docker containers"
	@echo "make logs           - View container logs (follow mode)"
	@echo "make celery-logs    - View Celery worker logs"
	@echo "make test           - Run test suite"
	@echo "make db-reset       - Reset database (drops volume and recreates)"
	@echo "make db-migrate     - Run database migrations"
	@echo "make seed           - Populate database with sample data"
	@echo "make shell          - Open shell in app container"
	@echo "make db-shell       - Open psql shell in database container"
	@echo "make clean          - Clean up Docker artifacts and caches"
	@echo "make install        - Install Python dependencies locally"

build:
	docker-compose build

up:
	docker-compose up

up-d:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

celery-logs:
	docker-compose logs -f celery-worker

test:
	python -m pytest tests/ -v

db-reset:
	docker-compose down -v
	docker-compose up -d db redis
	@echo "Waiting for DB to start..."
	@sleep 5
	docker-compose up -d app celery-worker

db-migrate:
	docker-compose exec app alembic upgrade head

seed:
	docker-compose exec app python -m database.seed

shell:
	docker-compose exec app bash

db-shell:
	docker-compose exec db psql -U admin jha_ml_platform

install:
	pip install -r requirements.txt

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	docker system prune -f
	rm -rf .pytest_cache/ .coverage htmlcov/
