SHELL := /bin/bash

VENV           = .venv
VENV_PYTHON    = $(VENV)/bin/python

# tests
install:
	poetry install --with dev

test:
	poetry run python -m pytest tests/

run:
	poetry run -m lisette --env-file .env

run-debug:
	poetry run -m lisette --env-file=.env --log-level DEBUG