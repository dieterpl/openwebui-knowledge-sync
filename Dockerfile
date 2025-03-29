FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV APP_HOME=/app
ENV HOME=/home/app

# Create a non-root user
RUN addgroup --system app && adduser --system --ingroup app app

# Set working directory
WORKDIR ${APP_HOME}

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY --chown=app:app requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY --chown=app:app sync.py .
COPY --chown=app:app .env .

# Create necessary directories
RUN mkdir -p /app/sync_directory ${HOME} /app/data && \
    chown -R app:app /app/sync_directory ${HOME} /app/data

# Switch to non-root user
USER app

# Ensure git config directory exists and is writable
RUN mkdir -p ${HOME}/.config/git

# Set default environment variables
ENV SYNC_INTERVAL=3600
ENV SYNC_DIRECTORY=/app/data

# Expose any necessary ports
EXPOSE 8080

# Run the sync script
CMD ["python", "sync.py"]