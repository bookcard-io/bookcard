# Multi-stage Dockerfile for production deployment
# Combines Next.js frontend and FastAPI backend in a single container

# ============================================================================
# Stage 1: Build Next.js frontend
# ============================================================================
FROM node:22-alpine AS frontend-builder

WORKDIR /app/web

# Copy package files for dependency installation
COPY web/package*.json ./

# Install dependencies (including dev dependencies needed for build)
# Use npm install if package-lock.json is out of sync, otherwise npm ci is faster
RUN npm install

# Copy frontend source code
COPY web/ .

# Build Next.js application
# Disable telemetry and set production mode
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production
RUN npm run build

# ============================================================================
# Stage 2: Build Python backend dependencies
# ============================================================================
FROM python:3.12-slim AS backend-builder

WORKDIR /app

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster dependency management
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml requirements.txt ./

# Create virtual environment and install dependencies
RUN uv venv /opt/venv && \
    . /opt/venv/bin/activate && \
    uv pip install -r requirements.txt

# ============================================================================
# Stage 3: Production image
# ============================================================================
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=backend-builder /opt/venv /opt/venv

# Set PATH to use virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Copy backend application code
COPY fundamental/ ./fundamental/
COPY scripts/ ./scripts/
COPY alembic.ini ./
COPY pyproject.toml ./

# Copy built Next.js application from frontend builder
COPY --from=frontend-builder /app/web/.next ./web/.next
COPY --from=frontend-builder /app/web/public ./web/public
COPY --from=frontend-builder /app/web/package.json ./web/package.json
COPY --from=frontend-builder /app/web/node_modules ./web/node_modules
COPY --from=frontend-builder /app/web/next.config.ts ./web/next.config.ts
COPY --from=frontend-builder /app/web/tsconfig.json ./web/tsconfig.json

# Install Node.js for running Next.js
# Using NodeSource repository for Node.js 22 LTS
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/* && \
    node --version && npm --version

# Copy startup script
COPY infra/start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Expose ports
EXPOSE 3000 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health && curl -f http://localhost:3000 || exit 1

# Run startup script
CMD ["/app/start.sh"]
