# Use a lightweight official Python image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies for packages like numpy, pandas, etc.
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Copy dependency list and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the port (Render uses this to detect which port the app listens to)
EXPOSE 10000

# Run the app with Gunicorn (production-ready server)
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000", "--workers", "1"]
