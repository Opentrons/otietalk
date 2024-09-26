.PHONY: black
black:
	pipenv run python -m black ./*.py ./tests/*.py ./analyze/*.py

.PHONY: black-check
black-check:
	pipenv run python -m black ./*.py ./tests/*.py --check

.PHONY: mypy
mypy:
	pipenv run python -m mypy ./*.py ./tests/*.py

.PHONY: ruff
ruff:
	pipenv run python -m ruff check . --fix --unsafe-fixes

.PHONY: ruff-check
ruff-check:
	pipenv run python -m ruff check .

.PHONY: lint
lint:
	$(MAKE) black-check
	$(MAKE) ruff-check


.PHONY: format
format:
	$(MAKE) black
	$(MAKE) ruff

.PHONY: setup
setup:
	pipenv install -d

.PHONY: teardown
teardown:
	pipenv --rm
