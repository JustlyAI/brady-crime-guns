# Brady Gun Project - Crime Gun Supply Chain Dashboard
# Multi-platform container build (supports ARM64/AMD64)

FROM python:3.11-slim

# Build arguments
ARG PORT=8501

# Labels
LABEL org.opencontainers.image.title="Brady Crime Gun Dashboard"
LABEL org.opencontainers.image.description="Crime gun supply chain analysis dashboard"
LABEL org.opencontainers.image.source="https://github.com/bradygunproject/brady-gun-analysis"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PORT=${PORT}

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Copy dependency files first (for better caching)
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
# Note: data/ not copied - using PostgreSQL via DATABASE_URL in production

# Create Streamlit config directory and config
RUN mkdir -p /home/appuser/.streamlit
COPY <<EOF /home/appuser/.streamlit/config.toml
[server]
port = ${PORT}
address = "0.0.0.0"
headless = true
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false

[theme]
base = "light"
EOF

# Set ownership
RUN chown -R appuser:appuser /app /home/appuser

# Switch to non-root user
USER appuser

# Expose port
EXPOSE ${PORT}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:${PORT}/_stcore/health || exit 1

# Run Streamlit
CMD ["sh", "-c", "streamlit run src/brady/dashboard/app.py --server.port=${PORT}"]
