# Dockerfile (root)
FROM mcr.microsoft.com/playwright/python:v1.45.1-jammy

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Ensure Chromium is available (base image already includes, keep as fallback)
RUN python -m playwright install --with-deps chromium

# Copy the rest of the project
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Run API + Bot (src.main runs both)
CMD ["python", "-m", "src.main"]
