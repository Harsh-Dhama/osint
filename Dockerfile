# Dockerfile for OSINT Platform - WhatsApp Auto-Scraper

FROM python:3.11-slim

# Metadata
LABEL maintainer="Harsh Dhama <harsh.dhama@example.com>"
LABEL description="OSINT Platform - WhatsApp Intelligence Module"
LABEL version="1.0.0"

# Install system dependencies for Playwright and Chromium
RUN apt-get update && apt-get install -y \
    # Chromium dependencies
    chromium \
    chromium-driver \
    # Playwright dependencies
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxext6 \
    libxrender1 \
    libxi6 \
    libxtst6 \
    # Additional utilities
    wget \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN python -m playwright install chromium
RUN python -m playwright install-deps

# Create necessary directories
RUN mkdir -p data logs reports uploads backups \
    data/whatsapp_session \
    data/face_database \
    logs/whatsapp \
    reports/whatsapp \
    reports/facial \
    reports/tracker \
    uploads/whatsapp \
    uploads/facial \
    uploads/social

# Copy application code
COPY backend/ ./backend/
COPY electron-app/ ./electron-app/
COPY docs/ ./docs/
COPY tests/ ./tests/
COPY scripts/ ./scripts/
COPY *.py ./
COPY *.md ./

# Set permissions
RUN chmod +x backend/main.py

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run application
CMD ["python", "backend/main.py"]
