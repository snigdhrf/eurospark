FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml .
COPY src/ ./src/

RUN pip install --no-cache-dir uv && \
    uv pip install --system .

EXPOSE 10000
CMD sh -c "langgraph up --port ${PORT:-10000} --no-browser"