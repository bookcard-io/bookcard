# Installation

Bookcard can be installed using Docker, which is the recommended method for most users.

## Prerequisites

- Docker and Docker Compose installed on your system
- A Calibre library (or a directory where you want to store your ebooks)

## Docker Installation

### 1. Clone the Repository

```bash
git clone https://github.com/bookcard-io/bookcard.git
cd bookcard
```

### 2. Configure Environment

Create a `.env` file in the project root:

```bash
# Authentication
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=your-secure-password
BOOKCARD_JWT_SECRET=your-jwt-secret-key

# Database (optional - defaults to SQLite)
# BOOKCARD_DATABASE_URL=postgresql+psycopg://user:password@postgres:5432/bookcard

# Redis (optional - for background tasks)
# ENABLE_REDIS=true
# REDIS_PASSWORD=your-redis-password
```

### 3. Start the Application

```bash
docker-compose -f infra/docker-compose.yaml up -d
```

The application will be available at:
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 4. Configure Library Path

Update the volume mounts in `docker-compose.yaml` to point to your Calibre library:

```yaml
volumes:
  - /path/to/your/calibre/library:/books
  - ~/.bookcard:/data
```

Then restart:

```bash
docker-compose -f infra/docker-compose.yaml restart
```

## Manual Installation

For development or manual installation, see the [Developer Guide](../developers/contributing.md).

## Next Steps

- [Usage Guide](usage.md) - Learn how to use Bookcard
- [API Documentation](../api/overview.md) - Integrate with the API
