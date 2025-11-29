#!/bin/bash
set -e

# Default values if not set
PUID=${PUID:-1000}
PGID=${PGID:-1000}

# Create group if it doesn't exist, or update if it does
if getent group appuser > /dev/null 2>&1; then
    # Group exists, check if GID matches
    CURRENT_GID=$(getent group appuser | cut -d: -f3)
    if [ "${CURRENT_GID}" != "${PGID}" ]; then
        groupmod -g "${PGID}" appuser
    fi
else
    groupadd -g "${PGID}" appuser
fi

# Create user if it doesn't exist, or update if it does
if id -u appuser > /dev/null 2>&1; then
    # User exists, check if UID/GID match
    CURRENT_UID=$(id -u appuser)
    CURRENT_GID=$(id -g appuser)

    if [ "${CURRENT_UID}" != "${PUID}" ] || [ "${CURRENT_GID}" != "${PGID}" ]; then
        usermod -u "${PUID}" -g "${PGID}" appuser
    fi
else
    useradd -u "${PUID}" -g "${PGID}" -m -s /bin/bash appuser
fi

# Change ownership of application directories that need to be writable
# Use || true to continue even if chown fails (e.g., on read-only mounts)
chown -R appuser:appuser /app/web/.next 2>/dev/null || true
chown -R appuser:appuser /app/fundamental 2>/dev/null || true

# Ensure app user can write to /data directory (mounted volume)
# This is the main directory where the application writes data
if [ -d /data ]; then
    chown -R appuser:appuser /data 2>/dev/null || true
fi

# Switch to app user and execute the startup script
exec gosu appuser "$@"
