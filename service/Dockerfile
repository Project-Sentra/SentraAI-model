# AI Service Dockerfile - Multi-stage build
# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Stage 2: Production
FROM python:3.11-slim AS production

# Create non-root user
RUN groupadd -r sentra && useradd -r -g sentra sentra

WORKDIR /app

# Install runtime dependencies for OpenCV and ML
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/*

# Copy application code
COPY --chown=sentra:sentra . .

# Create models directory (models will be downloaded at runtime if needed)
RUN mkdir -p ./models && chown sentra:sentra ./models

# Switch to non-root user
USER sentra

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5001/api/health || exit 1

# Expose port
EXPOSE 5001

# Environment variables
ENV PORT=5001
ENV HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5001"]
