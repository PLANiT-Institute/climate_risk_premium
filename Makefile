.PHONY: test test-cov lint typecheck format ci clean

# Run all tests
test:
	python3 -m pytest tests/ -v --tb=short

# Run tests with coverage report
test-cov:
	python3 -m pytest tests/ --cov=src --cov-report=term-missing --tb=short

# Lint with flake8 (errors and warnings, excluding archive code)
lint:
	python3 -m flake8 src/ --max-line-length=100 --extend-ignore=E203,W503,W291,W292,W293 --exclude="*archive*" --select=E,F

# Type check core modules with mypy
typecheck:
	python3 -m mypy src/financials/ src/risk/credit_rating.py src/risk/attribution.py src/risk/financing.py src/scenarios/ --ignore-missing-imports

# Format code with black (dry run)
format-check:
	python3 -m black --check --line-length 100 src/financials/ src/risk/credit_rating.py src/risk/attribution.py src/risk/financing.py src/scenarios/base.py src/scenarios/market.py

# Format code with black (apply)
format:
	python3 -m black --line-length 100 src/financials/ src/risk/credit_rating.py src/risk/attribution.py src/risk/financing.py src/scenarios/base.py src/scenarios/market.py

# Full CI pipeline
ci: lint typecheck test-cov

# Clean pytest cache
clean:
	rm -rf .pytest_cache __pycache__ .mypy_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
