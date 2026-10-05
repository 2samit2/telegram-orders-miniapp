# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY app ./app
COPY main.py .

# SQLite data directory (mount a volume here to persist orders)
RUN mkdir -p /data
ENV DATABASE_PATH=/data/artisan_coffee.sqlite3

EXPOSE 8000

CMD ["python", "main.py"]