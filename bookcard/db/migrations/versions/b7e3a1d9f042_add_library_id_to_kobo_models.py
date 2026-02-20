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

"""Add library_id to Kobo models.

Adds ``library_id`` FK to ``kobo_reading_states``, ``kobo_synced_books``,
and ``kobo_archived_books``.  Backfills from the user's active library in
``user_libraries``; falls back to ``libraries.is_active``.  Rebuilds
unique indexes to include ``library_id``.

Revision ID: b7e3a1d9f042
Revises: 6c30f249c5fa
Create Date: 2026-02-12 22:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7e3a1d9f042"
down_revision: str | Sequence[str] | None = "6c30f249c5fa"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = [
    "kobo_reading_states",
    "kobo_synced_books",
    "kobo_archived_books",
]

OLD_INDEXES = {
    "kobo_reading_states": "idx_kobo_reading_states_user_book",
    "kobo_synced_books": "idx_kobo_synced_books_user_book",
    "kobo_archived_books": "idx_kobo_archived_books_user_book",
}

NEW_INDEXES = {
    "kobo_reading_states": "idx_kobo_reading_states_user_lib_book",
    "kobo_synced_books": "idx_kobo_synced_books_user_lib_book",
    "kobo_archived_books": "idx_kobo_archived_books_user_lib_book",
}


def _backfill_library_id(conn: sa.Connection, table_name: str) -> None:
    """Populate ``library_id`` from the user's active library assignment.

    Strategy:
    1. Join through ``user_libraries`` on ``user_id`` where ``is_active = 1``.
    2. Fall back to the global ``libraries.is_active`` flag for any remaining
       NULL rows (users without a ``UserLibrary`` assignment).
    """
    # Step 1: per-user active library
    conn.execute(
        sa.text(f"""
            UPDATE {table_name}
            SET library_id = (
                SELECT ul.library_id
                FROM user_libraries ul
                WHERE ul.user_id = {table_name}.user_id
                  AND ul.is_active = 1
                LIMIT 1
            )
            WHERE library_id IS NULL
        """)  # noqa: S608 — table_name is a hardcoded migration constant
    )

    # Step 2: global fallback
    conn.execute(
        sa.text(f"""
            UPDATE {table_name}
            SET library_id = (
                SELECT l.id
                FROM libraries l
                WHERE l.is_active = 1
                LIMIT 1
            )
            WHERE library_id IS NULL
        """)  # noqa: S608
    )

    # Step 3: last-resort — pick the first library
    conn.execute(
        sa.text(f"""
            UPDATE {table_name}
            SET library_id = (
                SELECT l.id FROM libraries l ORDER BY l.id LIMIT 1
            )
            WHERE library_id IS NULL
        """)  # noqa: S608
    )


def upgrade() -> None:
    """Add library_id to Kobo tables, backfill, and rebuild indexes."""
    conn = op.get_bind()

    for table in TABLES:
        # 1. Add nullable column
        op.add_column(
            table,
            sa.Column("library_id", sa.Integer(), nullable=True),
        )

        # 2. Backfill
        _backfill_library_id(conn, table)

        # 3. Make NOT NULL
        op.alter_column(table, "library_id", existing_type=sa.Integer(), nullable=False)

        # 4. Add FK constraint
        op.create_foreign_key(
            f"fk_{table}_library_id",
            table,
            "libraries",
            ["library_id"],
            ["id"],
            ondelete="CASCADE",
        )

        # 5. Add index on library_id
        op.create_index(f"ix_{table}_library_id", table, ["library_id"])

        # 6. Drop old unique index, create new one
        op.drop_index(OLD_INDEXES[table], table_name=table)
        op.create_index(
            NEW_INDEXES[table],
            table,
            ["user_id", "library_id", "book_id"],
            unique=True,
        )


def downgrade() -> None:
    """Remove library_id from Kobo tables and restore old indexes."""
    for table in TABLES:
        # Drop new unique index
        op.drop_index(NEW_INDEXES[table], table_name=table)

        # Restore old unique index
        op.create_index(
            OLD_INDEXES[table],
            table,
            ["user_id", "book_id"],
            unique=True,
        )

        # Drop FK, index, and column
        op.drop_index(f"ix_{table}_library_id", table_name=table)
        op.drop_constraint(f"fk_{table}_library_id", table, type_="foreignkey")
        op.drop_column(table, "library_id")
