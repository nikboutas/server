FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .

# Χρησιμοποιούμε shell form ώστε το $PORT να διαβάζεται σωστά
CMD gunicorn server:app --workers 1 --timeout 120 --bind "0.0.0.0:${PORT:-5000}" --log-level info
