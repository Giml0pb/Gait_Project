FROM python:3.11-slim

WORKDIR /app
ENV MPLBACKEND=Agg \
    MPLCONFIGDIR=/tmp/matplotlib \
    UV_NO_DEV=1 \
    PATH="/app/.venv/bin:$PATH"

RUN pip install --no-cache-dir uv==0.9.5
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev --no-install-project
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY main.py ./
RUN uv sync --locked --no-dev
ENV UV_FROZEN=1
RUN mkdir -p /app/data/raw/dataset/data /app/outputs

VOLUME ["/app/data", "/app/outputs"]
CMD ["gait-lab", "demo", "--output-dir", "/app/outputs/demo"]
