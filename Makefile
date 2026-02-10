.PHONY: up down build logs migrate migrate-create test-backend shell-backend shell-frontend lint

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

logs-backend:
	docker compose logs -f backend

logs-frontend:
	docker compose logs -f frontend

migrate:
	docker compose exec backend alembic upgrade head

migrate-create:
	@read -p "Migration message: " msg; \
	docker compose exec backend alembic revision --autogenerate -m "$$msg"

test-backend:
	docker compose exec backend pytest -v

shell-backend:
	docker compose exec backend bash

shell-frontend:
	docker compose exec frontend sh

lint:
	docker compose exec backend ruff check app/
	docker compose exec backend ruff format --check app/

format:
	docker compose exec backend ruff check --fix app/
	docker compose exec backend ruff format app/

restart-backend:
	docker compose restart backend

restart-frontend:
	docker compose restart frontend
