FROM python:3.11-slim

WORKDIR /app

# Prevent Python from writing pyc files and buffer stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Start unified app (FastAPI REST API + MAX Bot long polling listener)
CMD ["python", "main.py"]
