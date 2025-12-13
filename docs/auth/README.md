# Authentication

Fundamental supports two authentication modes:

1. **Local JWT** (default): Username/password managed by the application
2. **Keycloak OIDC** (optional): Enterprise authentication via Keycloak with LDAP/AD/OAuth2/SAML support

## Local JWT Authentication

**Default mode** - no configuration needed.

- Users register and login with username/password
- JWT tokens issued by the application
- Enabled when `KEYCLOAK_ENABLED=false` or unset

**Default Admin User** (created on first startup):
- Username: `admin` (or `ADMIN_USERNAME`)
- Email: `admin@example.com` (or `ADMIN_EMAIL`)
- Password: `admin123` (or `ADMIN_PASSWORD`)

## Keycloak OIDC Integration

Keycloak handles identity (authentication, user management). The application handles authorization (roles, permissions, RBAC).

### Quick Setup

1. **Start Keycloak** (bundled):
   ```bash
   docker-compose --profile keycloak up -d
   ```

2. **Access Admin Console**: http://localhost:8080
   - Username: `admin`
   - Password: `admin123`

3. **Create OIDC Client**:
   - **Clients** → **Create client**
   - Client ID: `fundamental-client`
   - Protocol: `openid-connect`
   - Access Type: `confidential`
   - Valid Redirect URIs: `http://localhost:3000/api/auth/keycloak/callback`
   - Web Origins: `http://localhost:3000`
   - Copy the **Secret** from **Credentials** tab

4. **Set Environment Variables**:
   ```bash
   KEYCLOAK_ENABLED=true
   KEYCLOAK_URL=http://keycloak:8080
   KEYCLOAK_REALM=fundamental
   KEYCLOAK_CLIENT_ID=fundamental-client
   KEYCLOAK_CLIENT_SECRET=<secret-from-step-3>
   ```

5. **Create Users in Keycloak**: **Users** → **Add user** (set password in **Credentials** tab)

6. **Restart Application**: `docker-compose restart fundamental`

**First User**: The first Keycloak user to log in automatically receives admin privileges.

### Configuration Scenarios

#### Bundled Keycloak
Use the Keycloak container in docker-compose. Follow Quick Setup above.

#### External Keycloak
Use an existing Keycloak instance:

```bash
KEYCLOAK_ENABLED=true
KEYCLOAK_URL=https://keycloak.company.com
KEYCLOAK_REALM=company-realm
KEYCLOAK_CLIENT_ID=fundamental-client
KEYCLOAK_CLIENT_SECRET=<client-secret>
```

Configure the OIDC client in your Keycloak instance with the same settings as Quick Setup step 3.

#### LDAP/AD via Keycloak
1. Complete Keycloak setup (bundled or external)
2. In Keycloak: **Identity Providers** → **Add provider** → **LDAP** or **Active Directory**
3. Configure LDAP connection settings
4. Users authenticate with LDAP credentials; application sees only OIDC flow

**Note**: The application has no LDAP code - all LDAP integration is handled by Keycloak.

### Required Client Settings

- **Client Protocol**: `openid-connect`
- **Access Type**: `confidential`
- **Valid Redirect URIs**: `http://localhost:3000/api/auth/keycloak/callback` (adjust for your domain)
- **Web Origins**: Your frontend URL

### Environment Variables

**Required**:
- `KEYCLOAK_ENABLED=true`
- `KEYCLOAK_URL` - Keycloak base URL
- `KEYCLOAK_REALM` - Realm name
- `KEYCLOAK_CLIENT_ID` - Client ID from Keycloak
- `KEYCLOAK_CLIENT_SECRET` - Client secret from Keycloak

**Optional**:
- `KEYCLOAK_ISSUER` - Auto-generated from URL + realm if not set
- `KEYCLOAK_SCOPES` - Defaults to `openid profile email`

## Roles and Permissions

**Important**: Roles and permissions are managed **locally** in the application, not in Keycloak.

- **Keycloak**: Identity (authentication, user management)
- **Application**: Authorization (roles, permissions, RBAC)

**Workflow**:
1. User authenticates via Keycloak
2. Application creates/links local user record
3. Admin assigns roles via application's admin interface
4. Permissions checked against local RBAC system

This separation enables fine-grained permissions (e.g., `books:read`, `shelves:delete`) and conditional permissions independent of the identity provider.
