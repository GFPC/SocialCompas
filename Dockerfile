# ── Stage 1: build the MiniApp (React + Vite) ────────────────────────────────
FROM node:20-alpine AS miniapp
WORKDIR /miniapp
COPY miniapp/package.json miniapp/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY miniapp/ ./
# Empty VITE_API_URL = same origin (the app serves both the API and the MiniApp).
ARG VITE_API_URL=""
ARG VITE_YMAPS_KEY=""
ENV VITE_API_URL=$VITE_API_URL VITE_YMAPS_KEY=$VITE_YMAPS_KEY
RUN npm run build

# ── Stage 2: backend (FastAPI + MAX bot) ─────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Prevent Python from writing pyc files and buffer stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8

# Install Python requirements (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .
COPY --from=miniapp /miniapp/dist ./miniapp/dist

# Expose FastAPI port
EXPOSE 8000

# Healthcheck: verify API is alive
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/cities', timeout=4)" || exit 1

# Start unified app (FastAPI REST API + MAX Bot long polling listener)
CMD ["python", "main.py"]
