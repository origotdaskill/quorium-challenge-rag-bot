FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ .

# Create documents directory
RUN mkdir -p /app/documents

# Expose port
EXPOSE 9754

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9754"]
