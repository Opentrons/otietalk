.PHONY: black
black:
	pipenv run python -m black ./*.py

.PHONY: flake8
flake8:
	pipenv run python -m flake8  ./*.py

.PHONY: mypy
mypy:
	pipenv run python -m mypy ./*.py

.PHONY: clean
lint:
	$(MAKE) black
	$(MAKE) mypy
	$(MAKE) flake8

.PHONY: format
format:
	$(MAKE) black

.PHONY: setup
setup:
	pipenv install -d

.PHONY: teardown
teardown:
	pipenv --rm