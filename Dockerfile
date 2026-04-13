FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml .
COPY src/ ./src/

RUN pip install --no-cache-dir uv && \
    uv pip install --system .

EXPOSE 8000
CMD ["langgraph", "up", "--port", "8000", "--no-browser"]