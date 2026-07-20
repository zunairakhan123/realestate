FROM python:3.11-slim
# Create non-root user
RUN addgroup --system appgroup && adduser --system --group appuser
WORKDIR /app
# Efficient caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chown -R appuser:appgroup /app
USER appuser
# Use Gunicorn with Uvicorn workers for production concurrency
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:8000"]

