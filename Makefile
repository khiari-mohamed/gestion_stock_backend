.PHONY: help install dev migrate seed test clean docker-up docker-down

help:
	@echo "StockFlow Pro - Development Commands"
	@echo "====================================="
	@echo "make install     - Install dependencies"
	@echo "make dev         - Run development server"
	@echo "make migrate     - Run database migrations"
	@echo "make seed        - Seed database with test data"
	@echo "make test        - Run tests"
	@echo "make docker-up   - Start Docker services"
	@echo "make docker-down - Stop Docker services"
	@echo "make clean       - Clean cache and temp files"

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	prisma generate

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

migrate:
	prisma db push

seed:
	python seed.py

test:
	pytest -v --cov=app --cov-report=html

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache htmlcov .coverage
