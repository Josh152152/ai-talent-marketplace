# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose port 10000
EXPOSE 10000

# Set environment variable for Render port
ENV PORT=10000

# Start app with gunicorn, using main.py:app
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "main:app", "--workers", "1", "--timeout", "120"]
