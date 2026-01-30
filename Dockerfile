FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY *.html ./
COPY assets/ ./assets/
COPY blog/ ./blog/
COPY templates/ ./templates/

# Cloud Run uses PORT environment variable
ENV PORT=8080

# Expose port
EXPOSE 8080

# Run Flask app with gunicorn for production
CMD exec gunicorn --bind :$PORT --workers 2 --threads 4 app:app
