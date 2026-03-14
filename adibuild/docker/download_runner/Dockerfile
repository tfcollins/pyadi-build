FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

# Install additional dependencies
RUN apt-get update && apt-get install -y \
    xvfb \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
RUN pip install --no-cache-dir \
    playwright-stealth \
    requests

# Create working directory
WORKDIR /app

# Copy entrypoint script
COPY entrypoint.py /app/

# Entrypoint will be xvfb-run python entrypoint.py
ENTRYPOINT ["xvfb-run", "--auto-servernum", "--server-args=-screen 0 1920x1080x24", "python", "/app/entrypoint.py"]
