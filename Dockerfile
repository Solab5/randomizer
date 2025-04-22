FROM python:3.12-slim

WORKDIR /app

# Create necessary directories
RUN mkdir -p /app/app/static /app/app/templates

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure proper permissions
RUN chmod -R 755 /app/app/static /app/app/templates

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 