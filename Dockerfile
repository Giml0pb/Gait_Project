# Dockerfile para Gait Analysis Pipeline
# Imagen base optimizada con Python 3.11
FROM python:3.11-slim

# Instalar dependencias del sistema necesarias para scipy/numpy
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos de configuracion primero (mejor cache)
COPY pyproject.toml uv.lock ./

# Instalar uv
RUN pip install --no-cache-dir uv

# Instalar dependencias del proyecto
RUN uv sync --no-dev

# Copiar el resto del codigo
COPY src/ ./src/
COPY scripts/ ./scripts/

# Crear directorios para datos y outputs
RUN mkdir -p /app/data/raw/dataset/data
RUN mkdir -p /app/outputs/figures
RUN mkdir -p /app/outputs/tables

# Volumen para datos (el usuario montara su carpeta aqui)
VOLUME ["/app/data", "/app/outputs"]

# Comando por defecto: procesar un trial de ejemplo
# El usuario puede sobreescribir esto
CMD ["uv", "run", "python", "scripts/run_single_trial.py", "HS_1_1"]
