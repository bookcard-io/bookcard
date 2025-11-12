# Copyright (C) 2025 knguyen and others
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Standalone script to recover admin account access.

This script allows recovery of admin account access when credentials
are forgotten. It updates the password hash for all users with
is_admin=True in the database.

Usage
-----
    python -m scripts.recover_admin <new_password>
    python scripts/recover_admin.py <new_password>

Examples
--------
    python -m scripts.recover_admin "my_new_secure_password"
    python scripts/recover_admin.py admin123

    # Docker deployment
    docker exec -it fundamental-backend python -m scripts.recover_admin <password>

Notes
-----
- Uses the same password hashing (bcrypt) as the application
- Works with both SQLite and PostgreSQL databases
- Updates all admin users, not just the first one
"""

from __future__ import annotations

import sys

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from fundamental.config import AppConfig
from fundamental.services.security import PasswordHasher


def main() -> None:
    """Reset password for all admin users."""
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: recover_admin <new_password>\n")
        sys.stderr.write("This will reset the password for all admin users.\n")
        sys.exit(1)

    new_password = sys.argv[1]

    if len(new_password) < 8:
        sys.stderr.write(
            "Warning: Password is less than 8 characters. "
            "Consider using a stronger password.\n"
        )

    try:
        # Get database configuration
        config = AppConfig.from_env()
        engine = create_engine(config.database_url)

        # Hash the new password using the same method as the application
        hasher = PasswordHasher()
        password_hash = hasher.hash(new_password)

        # Update all admin users
        with engine.connect() as conn:
            result = conn.execute(
                text("UPDATE users SET password_hash = :hash WHERE is_admin = TRUE"),
                {"hash": password_hash},
            )
            conn.commit()
            rows_updated = result.rowcount

        if rows_updated == 0:
            sys.stderr.write(
                "Warning: No admin users found in the database. "
                "No passwords were updated.\n"
            )
            sys.exit(1)

        sys.stdout.write(
            f"✓ Successfully reset password for {rows_updated} admin user(s)\n"
        )
        sys.stdout.write(f"  New password: {new_password}\n")
        sys.stdout.write(
            "  You can now log in with any admin account using this password.\n"
        )
    except ValueError as e:
        sys.stderr.write(f"Error: Configuration error: {e}\n")
        sys.exit(1)
    except SQLAlchemyError as e:
        sys.stderr.write(f"Error: Database error: {e}\n")
        sys.exit(1)
    except Exception as e:  # noqa: BLE001
        # Catch-all for truly unexpected errors to provide user-friendly messages
        # in CLI context (e.g., from PasswordHasher or other dependencies)
        sys.stderr.write(f"Error: Unexpected error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
