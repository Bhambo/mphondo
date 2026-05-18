# =============================================================
# Mphondo Backend — multi-stage Dockerfile (linux/arm64)
# =============================================================
FROM python:3.12-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# tesseract-ocr for M-Pesa PDF OCR fallback (Português)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-por \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Builder stage ─────────────────────────────────────────────
FROM base AS builder

# Install uv for fast dependency resolution
RUN pip install uv==0.5.14

COPY pyproject.toml ./
COPY app/ ./app/
# Install production deps only (dev extras are opt-in via .[dev])
RUN uv pip install --system .

# ── Runtime stage ─────────────────────────────────────────────
FROM base AS runtime

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . .

# Non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/api/health').raise_for_status()"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
