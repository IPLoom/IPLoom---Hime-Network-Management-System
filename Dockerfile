# --- Final Monolithic Image ---
FROM python:3.12-slim

# Install system dependencies (nmap for scanner)
# Install system dependencies (nmap for scanner, nginx, supervisor)
RUN apt-get update && \
    apt-get install -y --no-install-recommends nmap nginx supervisor net-tools iputils-ping && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install backend dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/app ./app
COPY backend/.env .env

# Copy pre-built frontend assets to nginx static directory
COPY ui/dist ./static

# Copy curated brand icons seed directory into the image
# These are copied to the persistent /data/assets volume on first startup by seed_custom_assets()
COPY ui/public/brand ./seed/brand

# Copy Configuration files
COPY backend/nginx.conf /etc/nginx/nginx.conf
COPY backend/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose ports (Nginx=80, API=8000)
EXPOSE 80 8000

# Environment variables (overridable)
ENV DB_PATH=/data/final_scanner.duckdb \
    DB_SCHEMA_PATH=app/schema.sql \
    DB_INIT_MODE=create \
    ASSETS_DIR=/data/assets

# Create volume mount point for database
VOLUME ["/data"]

# Copy startup script
COPY backend/start.sh ./start.sh
RUN sed -i 's/\r$//' start.sh && chmod +x start.sh

# Run supervisord to manage both Nginx and App
CMD ["/usr/bin/supervisord"]
