FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgomp1 \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

# Download Korean font
RUN mkdir -p /app/fonts && \
    wget -q -O /app/fonts/NotoSansKR-Regular.ttf \
    "https://github.com/google/fonts/raw/main/ofl/notosanskr/NotoSansKR%5Bwght%5D.ttf" || \
    echo "Font download failed - will need manual setup"

FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app/fonts /app/fonts

# Create non-root user for security
RUN adduser --disabled-password --gecos '' --uid 1000 appuser && \
    mkdir -p /tmp/results && \
    chown -R appuser:appuser /app /tmp/results

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
