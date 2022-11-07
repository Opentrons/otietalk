.PHONY: black
black:
	pipenv run python -m black ./*.py ./tests/*.py

.PHONY: flake8
flake8:
	pipenv run python -m flake8  ./*.py ./tests/*.py

.PHONY: mypy
mypy:
	pipenv run python -m mypy ./*.py ./tests/*.py

.PHONY: bandit
bandit:
	pipenv run python -m bandit -r ./*.py ./tests/*.py

.PHONY: isort
isort:
	pipenv run python -m isort .

.PHONY: lint
lint:
	$(MAKE) isort
	$(MAKE) black
# $(MAKE) mypy
# $(MAKE) flake8
# $(MAKE) bandit

.PHONY: format
format:
	$(MAKE) black

.PHONY: setup
setup:
	pipenv install -d

.PHONY: teardown
teardown:
	pipenv --rm
