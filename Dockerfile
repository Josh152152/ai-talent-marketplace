FROM python:3.11-slim

WORKDIR /app

# Install build dependencies for native packages
RUN apt-get update && apt-get install -y \
    gcc build-essential python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

EXPOSE 10000

# Bind to Render’s port env var
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:$PORT", "--workers", "1"]
