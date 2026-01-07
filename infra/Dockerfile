# Multi-stage Dockerfile for production deployment
# Combines Next.js frontend and FastAPI backend in a single container
# Optimized for layer caching - stable dependencies first, frequently changing code last

# ============================================================================
# Stage 1: Build Next.js frontend (on host architecture)
# ============================================================================
# Use --platform=$BUILDPLATFORM to run the build on the runner's native architecture (e.g. amd64)
# This avoids slow QEMU emulation for heavy build steps like npm install and npm run build
FROM --platform=$BUILDPLATFORM node:22-alpine AS frontend-builder

WORKDIR /app/web

# Copy both package.json and package-lock.json to fix optional dependency issues on ARM64/musl
# See https://github.com/npm/cli/issues/4828
COPY web/package*.json ./

# Install dependencies (full install including devDependencies for building)
RUN npm install

# Copy frontend source code (changes frequently - keep separate from npm install)
COPY web/ .

# Build Next.js application
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production
# Disable Sentry during Docker build to reduce memory usage
ENV NEXT_PUBLIC_SENTRY_DISABLED=1
# Increase Node.js heap size to prevent out-of-memory errors during build
# Use 3GB to leave room for Docker and system overhead
ENV NODE_OPTIONS=--max-old-space-size=3072
RUN npm run build

# ============================================================================
# Stage 1.5: Install frontend production dependencies (on target architecture)
# ============================================================================
# This stage runs on the target architecture (e.g. arm64 via QEMU if needed)
# It installs ONLY production dependencies. This is much faster than full install
# and ensures we have the correct native binaries for the runtime.
FROM node:22-alpine AS frontend-deps

WORKDIR /app/web

COPY web/package*.json ./

# Install only production dependencies
# This might still run on QEMU for arm64, but it's much lighter without devDependencies
RUN npm install --omit=dev

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

# Copy ONLY dependency files (not application code)
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

# ============================================================================
# Layer 1: ALL system dependencies (consolidated, rarely changes)
# ============================================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Runtime essentials
    curl \
    gosu \
    # Calibre dependencies
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
    binutils \
    # KCC dependencies
    git \
    p7zip-full \
    unar \
    libarchive-tools \
    libfreetype6 \
    && rm -rf /var/lib/apt/lists/*

# ============================================================================
# Layer 2: Node.js runtime (stable, rarely changes)
# ============================================================================
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/* && \
    node --version && npm --version

# ============================================================================
# Layer 3: Calibre installation (pinned version, rarely changes)
# ============================================================================
ARG CALIBRE_RELEASE=8.15.0
ENV CALIBRE_RELEASE=${CALIBRE_RELEASE}

RUN mkdir -p /app/calibre && \
    if [ "$(uname -m)" = "x86_64" ]; then \
        curl -o /calibre.txz -L \
            "https://download.calibre-ebook.com/${CALIBRE_RELEASE}/calibre-${CALIBRE_RELEASE}-x86_64.txz"; \
    elif [ "$(uname -m)" = "aarch64" ]; then \
        curl -o /calibre.txz -L \
            "https://download.calibre-ebook.com/${CALIBRE_RELEASE}/calibre-${CALIBRE_RELEASE}-arm64.txz"; \
    fi && \
    tar xf /calibre.txz -C /app/calibre && \
    rm /calibre.txz && \
    echo "${CALIBRE_RELEASE}" > /app/CALIBRE_RELEASE

ENV PATH="/app/calibre:${PATH}"

# ============================================================================
# Layer 4: KCC installation (pinned version, rarely changes)
# ============================================================================
# Install uv for KCC
RUN pip install --no-cache-dir uv

ARG KCC_VERSION=v9.3.7
ENV KCC_VERSION=${KCC_VERSION}

RUN git clone --depth 1 --branch ${KCC_VERSION} https://github.com/ciromattia/kcc.git /opt/kcc || \
    git clone --depth 1 https://github.com/ciromattia/kcc.git /opt/kcc

RUN uv venv /opt/kcc/venv && \
    . /opt/kcc/venv/bin/activate && \
    uv pip install --upgrade pip && \
    uv pip install --no-cache-dir numpy==2.3.5 && \
    uv pip install --no-cache-dir PyMuPDF==1.26.6 && \
    uv pip install --no-cache-dir -r /opt/kcc/requirements-docker.txt || \
    uv pip install --no-cache-dir -r /opt/kcc/requirements.txt && \
    chmod +x /opt/kcc/kcc-c2e.py /opt/kcc/kcc-c2p.py

ENV PATH="/opt/kcc/venv/bin:/opt/kcc:${PATH}"

# ============================================================================
# Layer 5: Python virtual environment (changes when requirements.txt changes)
# ============================================================================
COPY --from=backend-builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# ============================================================================
# Layer 6: Static infrastructure files (changes occasionally)
# ============================================================================
COPY infra/start.sh /app/start.sh
COPY infra/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/start.sh /app/entrypoint.sh

COPY alembic.ini ./

# ============================================================================
# Layer 7: Frontend build output (changes when frontend code changes)
# ============================================================================
COPY --from=frontend-builder /app/web/.next ./web/.next
COPY --from=frontend-builder /app/web/public ./web/public
COPY --from=frontend-builder /app/web/package.json ./web/package.json
# COPY node_modules from frontend-deps (target arch), NOT frontend-builder (host arch)
COPY --from=frontend-deps /app/web/node_modules ./web/node_modules
COPY --from=frontend-builder /app/web/next.config.ts ./web/next.config.ts
COPY --from=frontend-builder /app/web/tsconfig.json ./web/tsconfig.json

# ============================================================================
# Layer 8: Backend application code (changes MOST frequently - LAST)
# ============================================================================
COPY pyproject.toml ./
COPY scripts/ ./scripts/
COPY bookcard/ ./bookcard/

# ============================================================================
# Container configuration
# ============================================================================
EXPOSE 3000 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health && curl -f http://localhost:3000 || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["/app/start.sh"]
