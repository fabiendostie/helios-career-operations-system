# Multi-stage build for HELIOS Profile Ingestor Service
# Production-ready Docker container with security best practices

# Build stage
FROM python:3.13.1-slim AS builder

# Set build environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Copy requirements first for better layer caching
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy models during build (cached layer)
RUN python -m spacy download en_core_web_sm
RUN python -m spacy download fr_core_news_sm

# Production stage
FROM python:3.13.1-slim AS production

# Set production environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/opt/venv/bin:$PATH" \
    PROFILE_INGESTOR_HOST=0.0.0.0 \
    PROFILE_INGESTOR_PORT=8001

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash --uid 1001 helios

# Set working directory and ownership
WORKDIR /app
RUN chown helios:helios /app

# Copy application code with proper ownership
COPY --chown=helios:helios src/ ./src/
COPY --chown=helios:helios data/ ./data/

# Create directories for runtime data
RUN mkdir -p /app/uploads /app/output /app/logs && \
    chown -R helios:helios /app/uploads /app/output /app/logs

# Switch to non-root user
USER helios

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Expose service port
EXPOSE 8001

# Run the profile ingestor service
CMD ["python", "-m", "src.main", "--host", "0.0.0.0", "--port", "8001"]