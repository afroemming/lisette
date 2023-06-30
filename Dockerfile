FROM python:3.11-slim as base

WORKDIR /app
COPY lisette/ ./lisette
COPY alembic/ ./alembic
COPY alembic.ini pyproject.toml README.md LICENSE ./

RUN python -m pip install .

CMD ["python", "-m", "lisette"]

FROM base as test
WORKDIR /app

RUN python -m pip install .[test]

FROM base as dev
WORKDIR /app

RUN python -m pip install .[all]
