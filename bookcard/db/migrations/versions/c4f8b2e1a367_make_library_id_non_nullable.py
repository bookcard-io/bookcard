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

"""Make library_id non-nullable on BookConversion, MetadataEnforcementOperation, TrackedBook, EPUBFixRun.

Backfills NULL library_id values from ``libraries.is_active`` then changes
the columns to NOT NULL with ``ondelete=CASCADE``.

Revision ID: c4f8b2e1a367
Revises: b7e3a1d9f042
Create Date: 2026-02-12 23:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c4f8b2e1a367"
down_revision: str | Sequence[str] | None = "b7e3a1d9f042"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = [
    "book_conversions",
    "metadata_enforcement_operations",
    "tracked_books",
    "epub_fix_runs",
]

# Old FK constraint names (may vary per DB; use naming convention if known)
OLD_FK_NAMES = {
    "book_conversions": "fk_book_conversions_library_id_libraries",
    "metadata_enforcement_operations": None,  # implicit FK, no named constraint
    "tracked_books": "fk_tracked_books_library_id_libraries",
    "epub_fix_runs": "fk_epub_fix_runs_library_id_libraries",
}


def _backfill_nulls(conn: sa.Connection, table: str) -> None:
    """Fill NULL library_id from the global active library, then first library."""
    # Active library fallback
    conn.execute(
        sa.text(f"""
            UPDATE {table}
            SET library_id = (
                SELECT ul.library_id
                FROM user_libraries ul
                WHERE ul.is_active = 1
                LIMIT 1
            )
            WHERE library_id IS NULL
        """)  # noqa: S608 — table is a hardcoded migration constant
    )

    # Global active library fallback
    conn.execute(
        sa.text(f"""
            UPDATE {table}
            SET library_id = (
                SELECT l.id FROM libraries l WHERE l.is_active = 1 LIMIT 1
            )
            WHERE library_id IS NULL
        """)  # noqa: S608
    )

    # Last-resort: first library by id
    conn.execute(
        sa.text(f"""
            UPDATE {table}
            SET library_id = (
                SELECT l.id FROM libraries l ORDER BY l.id LIMIT 1
            )
            WHERE library_id IS NULL
        """)  # noqa: S608
    )


def upgrade() -> None:
    """Backfill and tighten library_id columns."""
    conn = op.get_bind()

    for table in TABLES:
        # 1. Backfill NULLs
        _backfill_nulls(conn, table)

        # 2. Make NOT NULL
        op.alter_column(table, "library_id", existing_type=sa.Integer(), nullable=False)

        # 3. Drop old FK (if named) and recreate with CASCADE
        old_fk = OLD_FK_NAMES.get(table)
        if old_fk:
            with op.batch_alter_table(table) as batch_op:
                batch_op.drop_constraint(old_fk, type_="foreignkey")
                batch_op.create_foreign_key(
                    f"fk_{table}_library_id",
                    "libraries",
                    ["library_id"],
                    ["id"],
                    ondelete="CASCADE",
                )
        else:
            # For tables without a named constraint, use batch mode
            # to recreate the FK correctly
            with op.batch_alter_table(table) as batch_op:
                batch_op.create_foreign_key(
                    f"fk_{table}_library_id",
                    "libraries",
                    ["library_id"],
                    ["id"],
                    ondelete="CASCADE",
                )


def downgrade() -> None:
    """Revert library_id columns to nullable."""
    for table in TABLES:
        # Drop CASCADE FK
        with op.batch_alter_table(table) as batch_op:
            batch_op.drop_constraint(f"fk_{table}_library_id", type_="foreignkey")
            batch_op.create_foreign_key(
                None,
                "libraries",
                ["library_id"],
                ["id"],
                ondelete="SET NULL",
            )

        # Make nullable again
        op.alter_column(table, "library_id", existing_type=sa.Integer(), nullable=True)
