# API Overview

Bookcard provides a RESTful API for programmatic access to your library. The API follows REST conventions and uses JSON for request and response bodies.

## Base URL

```
http://localhost:8000/api
```

For production deployments, replace `localhost:8000` with your domain.

## Authentication

Most API endpoints require authentication. See the [Authentication Guide](authentication.md) for details.

## API Reference

The complete API reference with interactive documentation is available at:

- [Interactive API Reference](reference.md) - Swagger UI with all endpoints
- `/docs` - FastAPI's built-in Swagger UI (when running the application)

## Common Endpoints

### Books
- `GET /api/books` - List books
- `GET /api/books/{id}` - Get book details
- `POST /api/books` - Upload a book
- `DELETE /api/books/{id}` - Delete a book

### Shelves
- `GET /api/shelves` - List shelves
- `POST /api/shelves` - Create a shelf
- `GET /api/shelves/{id}` - Get shelf details
- `PATCH /api/shelves/{id}` - Update a shelf
- `DELETE /api/shelves/{id}` - Delete a shelf

### Authentication
- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current user info

## Response Format

### Success Response

```json
{
  "id": 1,
  "title": "Example Book",
  "author": "Example Author"
}
```

### Error Response

```json
{
  "detail": "Error message describing what went wrong"
}
```

## Rate Limiting

Currently, there are no rate limits on the API. This may change in future versions.

## Versioning

API versioning is handled through the OpenAPI schema. Check the `/openapi.json` endpoint for the current API version and available endpoints.
