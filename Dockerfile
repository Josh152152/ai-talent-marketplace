# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your app's code
COPY . .

# Expose the port Render expects (default is 10000)
EXPOSE 10000

# Set environment variable to match Render's dynamic PORT
ENV PORT=10000

# Start the app with Gunicorn and increased timeout
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000", "--workers", "1", "--timeout", "120"]
