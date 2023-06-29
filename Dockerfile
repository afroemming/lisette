FROM python:3.11-slim

WORKDIR /app
COPY lisette ./lisette 
COPY pyproject.toml README.md LICENSE ./

RUN python -m pip install .

CMD ["python", "-m", "lisette"]
