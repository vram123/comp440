# Use a small official Python image
FROM python:3.11-slim

WORKDIR /app

# Avoid .pyc and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# (Optional) system build tools (handy for some wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# Install deps first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Expose Flask port
EXPOSE 5000

# Where we’ll keep the SQLite DB in the container
ENV DATABASE_PATH=/data/app.db

# Ensure the /data folder exists
RUN mkdir -p /data

# On start: if /data/app.db doesn’t exist, init the DB once; then run the app
CMD ["sh", "-c", "\
  if [ ! -f \"$DATABASE_PATH\" ]; then \
    python init_db.py && \
    mv app.db /data/app.db || true; \
  fi; \
  python app.py \
"]
