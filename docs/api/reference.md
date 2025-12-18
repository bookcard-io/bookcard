# API Reference

This page provides interactive API documentation generated from the FastAPI OpenAPI schema.

<swagger-ui src="../openapi.json"></swagger-ui>

## Endpoint Categories

The API is organized into the following categories:

- **Authentication** (`/api/auth/*`) - User registration, login, and session management
- **Books** (`/api/books/*`) - Book management, search, and retrieval
- **Shelves** (`/api/shelves/*`) - Shelf creation and book organization
- **Authors** (`/api/authors/*`) - Author information and metadata
- **Libraries** (`/api/libraries/*`) - Library configuration and management
- **Admin** (`/api/admin/*`) - Administrative operations

## Interactive Testing

Use the Swagger UI above to:
- Browse all available endpoints
- View request/response schemas
- Test API calls directly from the browser
- See example requests and responses

## OpenAPI Schema

The complete OpenAPI schema is available at:
- `/openapi.json` - JSON schema
- `/docs` - Swagger UI (when application is running)
