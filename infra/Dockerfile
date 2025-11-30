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

# Install runtime dependencies including gosu for user switching
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gosu \
    && rm -rf /var/lib/apt/lists/*

# ============================================================================
# Install Calibre ebook-convert binary
# ============================================================================
ARG CALIBRE_RELEASE=8.15.0
ENV CALIBRE_RELEASE=${CALIBRE_RELEASE}

# Install additional required packages for Calibre
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libxtst6 \
        libxrandr2 \
        libxkbfile1 \
        libxcomposite1 \
        libopengl0 \
        libnss3 \
        libxkbcommon0 \
        libegl1 \
        libxdamage1 \
        libgl1 \
        libglx-mesa0 \
        libfontconfig1 \
        xz-utils \
        binutils && \
    rm -rf /var/lib/apt/lists/*

# Create directory for Calibre installation
RUN mkdir -p /app/calibre

# Download and install Calibre based on architecture
RUN if [ "$(uname -m)" = "x86_64" ]; then \
        curl -o /calibre.txz -L \
            "https://download.calibre-ebook.com/${CALIBRE_RELEASE}/calibre-${CALIBRE_RELEASE}-x86_64.txz"; \
    elif [ "$(uname -m)" = "aarch64" ]; then \
        curl -o /calibre.txz -L \
            "https://download.calibre-ebook.com/${CALIBRE_RELEASE}/calibre-${CALIBRE_RELEASE}-arm64.txz"; \
    fi && \
    tar xf /calibre.txz -C /app/calibre && \
    rm /calibre.txz

# Add Calibre to PATH
ENV PATH="/app/calibre:${PATH}"

# Create version file
RUN echo "${CALIBRE_RELEASE}" > /app/CALIBRE_RELEASE

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

# Copy startup and entrypoint scripts
COPY infra/start.sh /app/start.sh
COPY infra/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/start.sh /app/entrypoint.sh

# Expose ports
EXPOSE 3000 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health && curl -f http://localhost:3000 || exit 1

# Set entrypoint to handle user creation and switching
ENTRYPOINT ["/app/entrypoint.sh"]

# Run startup script as the default command
CMD ["/app/start.sh"]
