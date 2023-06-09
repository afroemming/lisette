SHELL := /bin/bash

VENV           = .venv
VENV_PYTHON    = $(VENV)/bin/python

# tests
venv:
	python3.11 -m venv $(VENV)

install:
	$(MAKE) venv
	$(VENV_PYTHON) -m pip install -e .[dev]

test:
	$(VENV_PYTHON) -m pytest tests/

run:
	$(VENV_PYTHON) -m lisette --env_file .env

run-debug:
	LISETTE_DEBUG=1 $(VENV_PYTHON) -m lisette --env_file=.env