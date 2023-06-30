FROM python:3.11-slim

WORKDIR /app
COPY lisette/ ./lisette
COPY alembic/ ./alembic
COPY alembic.ini pyproject.toml README.md LICENSE ./

RUN python -m pip install .

CMD ["python", "-m", "lisette"]
