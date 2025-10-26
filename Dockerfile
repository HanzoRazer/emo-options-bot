# Multi-stage Docker build for EMO Options Bot
# Optimized for production deployment with security best practices

# =============================================================================
# Build Stage - Create application package
# =============================================================================

FROM python:3.11-slim as builder

# Build arguments
ARG EMO_ENV=prod
ARG BUILD_DATE
ARG VCS_REF

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create application user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt requirements-ml.txt ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    if [ "$EMO_ENV" = "prod" ]; then \
        pip install -r requirements-ml.txt; \
    fi && \
    pip install gunicorn[gevent]

# Copy application code
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY alembic/ ./alembic/
COPY alembic.ini ./
COPY .env.example ./

# Create necessary directories
RUN mkdir -p data logs backups temp && \
    chown -R appuser:appuser /app

# =============================================================================
# Runtime Stage - Minimal production image
# =============================================================================

FROM python:3.11-slim as runtime

# Build arguments
ARG EMO_ENV=prod
ARG BUILD_DATE
ARG VCS_REF

# Metadata labels
LABEL maintainer="EMO Options Bot Team" \
      org.opencontainers.image.title="EMO Options Bot" \
      org.opencontainers.image.description="AI-powered options trading bot with real-time analysis" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.source="https://github.com/your-org/emo-options-bot"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    EMO_ENV=${EMO_ENV} \
    PATH="/app/.local/bin:$PATH" \
    PYTHONPATH="/app/src"

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create application user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy from builder stage
COPY --from=builder --chown=appuser:appuser /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder --chown=appuser:appuser /usr/local/bin /usr/local/bin
COPY --from=builder --chown=appuser:appuser /app /app

# Create volume mount points
VOLUME ["/app/data", "/app/logs", "/app/backups"]

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8082/health || exit 1

# Expose ports
EXPOSE 8082 8083

# =============================================================================
# Entry point and startup
# =============================================================================

# Copy startup script
COPY --chown=appuser:appuser docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

# Default command
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["web"]