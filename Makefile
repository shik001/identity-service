.PHONY: install run test integration-test lint format typecheck clean docker-build docker-run

install:
	pip install -e ".[dev]"

run:
	uvicorn app.main:app --reload --port 8000

test:
	pytest -v -m "not integration"

integration-test:
	pytest -v -m integration

lint:
	ruff check .

format:
	ruff format .

typecheck:
	mypy app/

docker-build:
	docker build -t identity-service .

docker-run:
	docker compose up

clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache .ruff_cache *.egg-info dist build
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
