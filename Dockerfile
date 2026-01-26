FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py ./app.py
COPY templates/ ./templates/

ENV PORT=8080
EXPOSE 8080

CMD ["gunicorn", "--bind", ":8080", "--workers", "1", "--threads", "8", "--timeout", "0", "app:app"]
