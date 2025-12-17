# Authentication

Bookcard supports two authentication modes:

1. **Local JWT** (default): Username/password managed by the application
2. **OIDC (SSO)** (optional): Enterprise authentication via any OpenID Connect provider

## Local JWT Authentication

**Default mode** - no configuration needed.

- Users register and login with username/password
- JWT tokens issued by the application
- Enabled when `OIDC_ENABLED=false` or unset

**Default Admin User** (created on first startup):
- Username: `admin` (or `ADMIN_USERNAME`)
- Email: `admin@example.com` (or `ADMIN_EMAIL`)
- Password: `admin123` (or `ADMIN_PASSWORD`)

## OIDC (SSO) Integration

Your OIDC provider handles identity (authentication, user management). The application handles authorization (roles, permissions, RBAC).

### Quick Setup

1. **Create an OIDC client/application in your provider**:
   - Client ID: `bookcard-client` (example)
   - Client type: confidential (if you want to use a client secret)
   - Valid Redirect URI: `http://localhost:3000/api/auth/oidc/callback`
   - Web Origin: `http://localhost:3000`

2. **Set Environment Variables**:
   ```bash
   OIDC_ENABLED=true
   OIDC_ISSUER=https://your-issuer.example.com/
   OIDC_CLIENT_ID=bookcard-client
   OIDC_CLIENT_SECRET=<client-secret>
   OIDC_SCOPES="openid profile email"
   ```

3. **Create users in your provider**, or connect your provider to LDAP/AD as needed.

4. **Restart Application**: `docker-compose restart bookcard`

**First User**: The first SSO user to log in automatically receives admin privileges.

### Required Client Settings

- **Protocol**: `openid-connect`
- **Redirect URI**: `http://localhost:3000/api/auth/oidc/callback` (adjust for your domain)
- **Web Origins**: Your frontend URL

### Environment Variables

**Required**:
- `OIDC_ENABLED=true`
- `OIDC_ISSUER` - OIDC issuer URL
- `OIDC_CLIENT_ID` - Client ID from your provider
- `OIDC_CLIENT_SECRET` - Client secret from your provider (if applicable)

**Optional**:
- `OIDC_SCOPES` - Defaults to `openid profile email`

## Roles and Permissions

**Important**: Roles and permissions are managed **locally** in the application, not in the OIDC provider.

- **OIDC provider**: Identity (authentication, user management)
- **Application**: Authorization (roles, permissions, RBAC)

**Workflow**:
1. User authenticates via OIDC
2. Application creates/links local user record
3. Admin assigns roles via application's admin interface
4. Permissions checked against local RBAC system

This separation enables fine-grained permissions (e.g., `books:read`, `shelves:delete`) and conditional permissions independent of the identity provider.
