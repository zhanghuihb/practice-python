FROM python:3.11-slim

# Install system dependencies for DOC support
RUN apt-get update && apt-get install -y \
    antiword \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Environment variables
ENV FILE_BROWSER_ROOT=/data
ENV FILE_BROWSER_HOST=0.0.0.0
ENV FILE_BROWSER_PORT=8000

# Run application
CMD ["python", "main.py"]
