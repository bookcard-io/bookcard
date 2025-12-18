# Users & Permissions

Bookcard includes a robust role-based access control (RBAC) system. Administrators can manage users, assign roles, and configure granular permissions.

![Users & Permissions](../screenshots/users_and_permissions_screen.png){ width="800" }

## Managing Users

To manage users, navigate to **Settings > Admin > Users & Permissions**.

### Creating a User

1.  Click the **Create User** button.
2.  Fill in the required fields:
    -   **Username:** Unique identifier for logging in.
    -   **Email:** User's email address.
    -   **Password:** Initial password (must be at least 8 characters).
    -   **Roles:** Assign one or more roles (e.g., "user", "admin").
3.  Optionally, you can set:
    -   **Full Name:** Display name.
    -   **Device Email:** Default email for "Send to Kindle" functionality.
    -   **Administrator:** Check this to grant full system access (bypasses all permission checks).
    -   **Active:** Uncheck to disable the account without deleting it.

### Editing a User

Click the **Edit** (pencil) icon next to any user in the list to modify their details, reset their password, or change their roles.

## Roles & Permissions

Permissions in Bookcard are granular rights to perform specific actions (e.g., `books:create`, `shelves:delete`). These permissions are grouped into **Roles**, which are then assigned to **Users**.

### Default Roles

Bookcard comes with three default roles seeded during installation:

-   **Admin:** Full system access. Has all permissions.
-   **User:** Standard user. Can read books, manage their own profile, create shelves, make edits, upload, etc.
-   **Viewer:** Read-only access. Can browse and read books but cannot modify anything.

### Custom Roles

Admins can create custom roles with specific sets of permissions. For example, you might create a "Librarian" role that can edit book metadata (`books:write`) but cannot manage system settings or users (`users:write`).

### Available Permissions

Permissions are namespaced by resource and action:

**User Management**
-   `users:create`: Create new users
-   `users:read`: View user list and details
-   `users:write`: Edit user profiles
-   `users:delete`: Delete users

**Book Management**
-   `books:create`: Upload new books
-   `books:read`: View books
-   `books:write`: Edit book metadata
-   `books:delete`: Delete books from the library
-   `books:send`: Use "Send to Device" features

**Shelf Management**
-   `shelves:create`: Create new shelves
-   `shelves:read`: View shelves
-   `shelves:edit`: Edit any shelf (users can always edit their own)
-   `shelves:delete`: Delete shelves

**System**
-   `system:admin`: Full system administration access (implies all other permissions)
