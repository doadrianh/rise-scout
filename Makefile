.PHONY: install dev test lint type-check fmt clean cdk-install bootstrap synth diff deploy

install:
	uv sync --no-dev

dev:
	uv sync

test:
	pytest tests/ -v --tb=short

test-unit:
	pytest tests/unit/ -v --tb=short

test-integration:
	pytest tests/integration/ -v --tb=short -m integration

lint:
	ruff check src/ tests/
	ruff format --check src/ tests/

type-check:
	mypy src/

fmt:
	ruff check --fix src/ tests/
	ruff format src/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name '*.egg-info' -exec rm -rf {} +
	rm -rf dist build .mypy_cache .ruff_cache .pytest_cache htmlcov
	rm -rf cdk/layers/

cdk-install:
	cd cdk && npm install

bootstrap:
	cd cdk && npx cdk bootstrap

synth:
	cd cdk && npx cdk synth

diff:
	cd cdk && npx cdk diff

deploy:
	cd cdk && npx cdk deploy --all --require-approval never
