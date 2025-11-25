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

"""Add cascade relationship to library fkey.

Revision ID: e142ce95cf2f
Revises: 9cb57048d879
Create Date: 2025-11-25 09:38:47.750189

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e142ce95cf2f"
down_revision: str | Sequence[str] | None = "9cb57048d879"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _constraint_exists(
    connection: sa.Connection, table_name: str, constraint_name: str
) -> bool:
    """Check if a foreign key constraint exists on a table.

    Parameters
    ----------
    connection : sa.Connection
        Database connection.
    table_name : str
        Name of the table.
    constraint_name : str
        Name of the constraint to check.

    Returns
    -------
    bool
        True if constraint exists, False otherwise.
    """
    inspector = sa.inspect(connection)
    fks = inspector.get_foreign_keys(table_name)
    # Check if any foreign key has a matching name (handle None/empty names)
    return any(fk.get("name") == constraint_name for fk in fks if fk.get("name"))


def _upgrade_table_postgresql(
    table_name: str, column_name: str, constraint_name: str, referenced_table: str
) -> None:
    """Upgrade a table's foreign key constraint with CASCADE for PostgreSQL.

    Parameters
    ----------
    table_name : str
        Name of the table to modify.
    column_name : str
        Name of the foreign key column.
    constraint_name : str
        Name of the foreign key constraint.
    referenced_table : str
        Name of the referenced table.
    """
    op.alter_column(table_name, column_name, existing_type=sa.INTEGER(), nullable=True)
    op.drop_constraint(constraint_name, table_name, type_="foreignkey")
    op.create_foreign_key(
        None, table_name, referenced_table, [column_name], ["id"], ondelete="CASCADE"
    )


def _upgrade_table_sqlite(
    connection: sa.Connection,
    table_name: str,
    column_name: str,
    constraint_name: str,
    referenced_table: str,
) -> None:
    """Upgrade a table's foreign key constraint with CASCADE for SQLite.

    Parameters
    ----------
    connection : sa.Connection
        Database connection.
    table_name : str
        Name of the table to modify.
    column_name : str
        Name of the foreign key column.
    constraint_name : str
        Name of the foreign key constraint.
    referenced_table : str
        Name of the referenced table.
    """
    with op.batch_alter_table(table_name, schema=None) as batch_op:
        batch_op.alter_column(column_name, existing_type=sa.INTEGER(), nullable=True)
        if _constraint_exists(connection, table_name, constraint_name):
            batch_op.drop_constraint(constraint_name, type_="foreignkey")
        batch_op.create_foreign_key(
            constraint_name, referenced_table, [column_name], ["id"], ondelete="CASCADE"
        )


def _downgrade_table_postgresql(
    table_name: str, column_name: str, constraint_name: str, referenced_table: str
) -> None:
    """Downgrade a table's foreign key constraint for PostgreSQL.

    Parameters
    ----------
    table_name : str
        Name of the table to modify.
    column_name : str
        Name of the foreign key column.
    constraint_name : str
        Name of the foreign key constraint.
    referenced_table : str
        Name of the referenced table.
    """
    op.drop_constraint(constraint_name, table_name, type_="foreignkey")
    op.create_foreign_key(
        constraint_name, table_name, referenced_table, [column_name], ["id"]
    )
    op.alter_column(table_name, column_name, existing_type=sa.INTEGER(), nullable=False)


def _downgrade_table_sqlite(
    connection: sa.Connection,
    table_name: str,
    column_name: str,
    constraint_name: str,
    referenced_table: str,
) -> None:
    """Downgrade a table's foreign key constraint for SQLite.

    Parameters
    ----------
    connection : sa.Connection
        Database connection.
    table_name : str
        Name of the table to modify.
    column_name : str
        Name of the foreign key column.
    constraint_name : str
        Name of the foreign key constraint.
    referenced_table : str
        Name of the referenced table.
    """
    with op.batch_alter_table(table_name, schema=None) as batch_op:
        if _constraint_exists(connection, table_name, constraint_name):
            batch_op.drop_constraint(constraint_name, type_="foreignkey")
        batch_op.create_foreign_key(
            constraint_name, referenced_table, [column_name], ["id"]
        )
        batch_op.alter_column(column_name, existing_type=sa.INTEGER(), nullable=False)


def upgrade() -> None:
    """Upgrade schema."""
    connection = op.get_bind()
    is_postgresql = connection.dialect.name == "postgresql"

    # Define table configurations for foreign key updates
    table_configs = [
        ("annotations", "library_id", "annotations_library_id_fkey", "libraries"),
        (
            "annotations_dirtied",
            "library_id",
            "annotations_dirtied_library_id_fkey",
            "libraries",
        ),
        (
            "author_mappings",
            "library_id",
            "author_mappings_library_id_fkey",
            "libraries",
        ),
        (
            "library_scan_states",
            "library_id",
            "library_scan_states_library_id_fkey",
            "libraries",
        ),
        ("read_status", "library_id", "read_status_library_id_fkey", "libraries"),
        (
            "reading_progress",
            "library_id",
            "reading_progress_library_id_fkey",
            "libraries",
        ),
        (
            "reading_sessions",
            "library_id",
            "reading_sessions_library_id_fkey",
            "libraries",
        ),
        ("shelves", "library_id", "shelves_library_id_fkey", "libraries"),
        ("book_shelf_links", "shelf_id", "book_shelf_links_shelf_id_fkey", "shelves"),
    ]

    # Process each table configuration
    for table_name, column_name, constraint_name, referenced_table in table_configs:
        fkey_name = op.f(f"{constraint_name}")
        if is_postgresql:
            _upgrade_table_postgresql(
                table_name, column_name, fkey_name, referenced_table
            )
            # Create index for read_status after processing it (PostgreSQL)
            if table_name == "read_status":
                op.create_index(
                    "idx_read_status_status", "read_status", ["status"], unique=False
                )
        else:
            # Create index for read_status before processing it (SQLite)
            if table_name == "read_status":
                op.create_index(
                    "idx_read_status_status", "read_status", ["status"], unique=False
                )
            _upgrade_table_sqlite(
                connection, table_name, column_name, fkey_name, referenced_table
            )


def downgrade() -> None:
    """Downgrade schema."""
    connection = op.get_bind()
    is_postgresql = connection.dialect.name == "postgresql"

    # Define table configurations in reverse order for downgrade
    table_configs = [
        ("shelves", "library_id", "shelves_library_id_fkey", "libraries"),
        (
            "reading_sessions",
            "library_id",
            "reading_sessions_library_id_fkey",
            "libraries",
        ),
        (
            "reading_progress",
            "library_id",
            "reading_progress_library_id_fkey",
            "libraries",
        ),
        ("read_status", "library_id", "read_status_library_id_fkey", "libraries"),
        (
            "library_scan_states",
            "library_id",
            "library_scan_states_library_id_fkey",
            "libraries",
        ),
        (
            "author_mappings",
            "library_id",
            "author_mappings_library_id_fkey",
            "libraries",
        ),
        (
            "annotations_dirtied",
            "library_id",
            "annotations_dirtied_library_id_fkey",
            "libraries",
        ),
        ("annotations", "library_id", "annotations_library_id_fkey", "libraries"),
        ("book_shelf_links", "shelf_id", "book_shelf_links_shelf_id_fkey", "shelves"),
    ]

    # Process each table configuration
    for table_name, column_name, constraint_name, referenced_table in table_configs:
        fkey_name = op.f(f"{constraint_name}")
        if is_postgresql:
            # Drop index for read_status before processing it (PostgreSQL)
            if table_name == "read_status":
                op.drop_index("idx_read_status_status", table_name="read_status")
            _downgrade_table_postgresql(
                table_name, column_name, fkey_name, referenced_table
            )
        else:
            # Drop index for read_status before processing it (SQLite)
            if table_name == "read_status":
                op.drop_index("idx_read_status_status", table_name="read_status")
            _downgrade_table_sqlite(
                connection, table_name, column_name, fkey_name, referenced_table
            )
