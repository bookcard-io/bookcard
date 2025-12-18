# API Authentication

Bookcard supports two authentication methods:

1. **JWT (JSON Web Tokens)** - Default authentication
2. **OIDC (OpenID Connect)** - Enterprise SSO integration

## JWT Authentication

### Register a User

```bash
POST /api/auth/register
Content-Type: application/json

{
  "username": "newuser",
  "email": "user@example.com",
  "password": "secure-password"
}
```

### Login

```bash
POST /api/auth/login
Content-Type: application/json

{
  "username": "newuser",
  "password": "secure-password"
}
```

Response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Using the Token

Include the token in the `Authorization` header:

```bash
GET /api/books
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Token Expiration

Tokens expire after a configurable period (default: 3 months). Refresh by logging in again.

## OIDC Authentication

When OIDC is enabled, authentication is handled through your OIDC provider. See the [User Guide](../user-guide/installation.md) for OIDC configuration.

### OIDC Flow

1. User initiates login via `/api/auth/oidc/login`
2. Redirected to OIDC provider
3. User authenticates with provider
4. Redirected back to `/api/auth/oidc/callback`
5. Application issues JWT token

## Current User

Get information about the authenticated user:

```bash
GET /api/auth/me
Authorization: Bearer <token>
```

Response:

```json
{
  "id": 1,
  "username": "newuser",
  "email": "user@example.com",
  "roles": ["user"]
}
```

## Permissions

Different endpoints require different permissions. Check the [API Reference](reference.md) for endpoint-specific requirements.

Common permissions:
- `books:read` - Read books
- `books:write` - Create/update books
- `books:delete` - Delete books
- `shelves:read` - Read shelves
- `shelves:write` - Create/update shelves
- `admin:*` - Administrative access
