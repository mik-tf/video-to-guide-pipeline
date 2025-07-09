FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p videos output/{audio,transcriptions,guides} logs tmp

# Set environment variables
ENV PYTHONPATH=/app/src
ENV WHISPER_CACHE_DIR=/app/.cache/whisper

# Create non-root user
RUN useradd -m -u 1000 pipeline && \
    chown -R pipeline:pipeline /app
USER pipeline

# Default command
CMD ["python", "scripts/process_videos.py", "--help"]
