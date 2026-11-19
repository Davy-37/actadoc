.PHONY: install hooks format lint test check package clean

install:
	pip install -e ".[dev]"

# local quality checks before each commit (to run once after cloning)
hooks:
	pre-commit install

format:
	black . && ruff check --fix .

lint:
	black --check . && ruff check . && mypy src

test:
	pytest -q --cov --cov-report=term-missing

# everything CI runs on a pull request
check:
	pre-commit run --all-files && $(MAKE) test

# build wheel + sdist into dist/
package:
	python -m build

clean:
	rm -rf dist/ .pytest_cache .ruff_cache .mypy_cache .coverage
