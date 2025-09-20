# Multi-stage Dockerfile for ARCHITECT service
FROM python:3.13.1-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for WeasyPrint
RUN apt-get update && apt-get install -y \
    gcc \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf2.0-dev \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash architect
WORKDIR /app
RUN chown architect:architect /app

# Development stage
FROM base as development

# Install development dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Switch to non-root user
USER architect

# Copy source code
COPY --chown=architect:architect . .

# Expose port
EXPOSE 8004

# Development command
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8004", "--reload"]

# Production stage
FROM base as production

# Install only production dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Switch to non-root user
USER architect

# Copy source code
COPY --chown=architect:architect . .

# Create directories for temporary files
RUN mkdir -p /tmp/architect-temp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8004/health')" || exit 1

# Expose port
EXPOSE 8004

# Production command
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8004", "--workers", "1"]