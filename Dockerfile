FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000

# ⏱️ Increase timeout from default (30s) to 120s
CMD sh -c "gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120"
