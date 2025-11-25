.PHONY: mypy
mypy:
	uv run mypy --namespace-packages .

.PHONY: ruff
ruff:
	uv run ruff check . --fix --unsafe-fixes

.PHONY: ruff-check
ruff-check:
	uv run ruff check .

.PHONY: lint
lint:
	$(MAKE) ruff-check
	$(MAKE) mypy

.PHONY: setup
setup:
	uv sync --python 3.14 --frozen

.PHONY: teardown
teardown:
	rm -rf .venv
