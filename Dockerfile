# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install pip packages
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose the port Render will inject
EXPOSE 10000

# Use shell form to allow $PORT to be evaluated
CMD gunicorn app:app --bind 0.0.0.0:${PORT:-10000} --workers 1
