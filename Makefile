.PHONY: help build up down restart logs migrate seed test clean dev-backend dev-frontend k8s-deploy

# Default target
help:
	@echo "AI Influencer Discovery Platform - Make Commands"
	@echo ""
	@echo "Development:"
	@echo "  make build          - Build all Docker images"
	@echo "  make up             - Start all services"
	@echo "  make down           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make logs           - View backend logs"
	@echo "  make migrate        - Run database migrations"
	@echo "  make seed           - Seed database with sample data"
	@echo "  make test           - Run all tests"
	@echo "  make clean          - Remove all containers and volumes"
	@echo ""
	@echo "Development (Local):"
	@echo "  make dev-backend    - Run backend in development mode"
	@echo "  make dev-frontend   - Run frontend in development mode"
	@echo ""
	@echo "Production:"
	@echo "  make k8s-deploy     - Deploy to Kubernetes"

# Docker Compose commands
build:
	docker-compose build

up:
	docker-compose up -d
	down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f backend

logs-all:
	docker-compose logs -f

# Database
migrate:
	docker-compose exec backend alembic upgrade head

seed:
	docker-compose exec backend python -c "import asyncio; from app.db.seed import seed_all; asyncio.run(seed_all())"

reset-db:
	docker-compose down -v
	docker-compose up -d postgres
	sleep 5
	make migrate
	make seed

# Testing
test-backend:
	docker-compose exec backend pytest

test-frontend:
	cd frontend && npm test

test: test-backend test-frontend

# Cleanup
clean:
	docker-compose down -v
	docker system prune -f

# Local Development
dev-backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

dev-worker:
	cd backend && celery -A app.workers.celery_app worker --loglevel=info

# Kubernetes
k8s-deploy:
	kubectl apply -f infra/k8s/namespace.yaml
	kubectl apply -f infra/k8s/

k8s-delete:
	kubectl delete -f infra/k8s/

k8s-status:
	kubectl get pods -n influencer-platform

# Utilities
shell-backend:
	docker-compose exec backend bash

shell-db:
	docker-compose exec postgres psql -U platform -d influencer_platform

backup-db:
	docker-compose exec postgres pg_dump -U platform influencer_platform > backup_$(shell date +%Y%m%d_%H%M%S).sql

# CI/CD
ci-build:
	docker build -t influencer-platform/backend:latest backend/
	docker build -t influencer-platform/frontend:latest frontend/

ci-push:
	docker push influencer-platform/backend:latest
	docker push influencer-platform/frontend:latest
