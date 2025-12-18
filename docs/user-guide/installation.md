# Application Installation

Bookcard can be installed using Docker, which is the recommended method for most users.

## Prerequisites

### Install Docker

Bookcard relies on Docker. Please ensure you have Docker installed on your system.
For detailed installation instructions, see the [Docker Installation Guide](docker-installation.md).

### Other Prerequisites

- A an optional existing Calibre library (or a directory where you want to store your ebooks).  You can get started without one.

## Application Installation

### 1. Clone the Repository

```bash
git clone https://github.com/bookcard-io/bookcard.git
cd bookcard
```

### 2. Configure Environment

Create a `.env` file in the project root.

The supplied `docker-compose.yaml` includes Redis and Postgres services. You can use these or point to your own instances.

```bash
# Authentication
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=your-secure-password
BOOKCARD_JWT_SECRET=your-jwt-secret-key

# Database
# If using the included Postgres service (default):
BOOKCARD_DATABASE_URL=postgresql+psycopg://admin:admin123@postgres:5432/bookcard
# If using your own Postgres:
# BOOKCARD_DATABASE_URL=postgresql+psycopg://user:password@your-postgres-host:5432/bookcard

# Redis
# If using the included Redis service (default):
ENABLE_REDIS=true
REDIS_HOST=redis
REDIS_PORT=6379
# If using your own Redis:
# REDIS_HOST=your-redis-host
# REDIS_PORT=6379
# REDIS_PASSWORD=your-redis-password
```

### 3. Start the Application

```bash
docker compose -f infra/docker-compose.yaml up -d
```

The application will be available at:
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 4. Configure Library Path

Update the volume mounts in `infra/docker-compose.yaml` to point to your Calibre library and data directory. You can also optionally configure automatic ingestion and Calibre plugin support.

```yaml
volumes:
  # The location of your existing Calibre library (Required)
  - /path/to/your/calibre/library:/books

  # The location for Bookcard's internal data (Required)
  - ~/.bookcard:/data

  # Optional: Directory for automatic book ingestion
  # Files placed here will be imported and DELETED after successful ingestion
  - /path/to/ingest/directory:/data/books_ingest

  # Optional: Calibre configuration directory
  # Map this if you need to use Calibre plugins (e.g. DeDRM)
  - /path/to/calibre/config:/home/appuser/.config/calibre
```

Then restart:

```bash
docker compose -f infra/docker-compose.yaml restart
```

## Manual Installation

For development or manual installation, see the [Developer Guide](../developers/workflow.md).

## Next Steps

- [Usage Guide](usage.md) - Learn how to use Bookcard
- [API Documentation](../api/overview.md) - Integrate with the API
