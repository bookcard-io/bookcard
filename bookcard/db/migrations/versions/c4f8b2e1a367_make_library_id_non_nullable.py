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
from sqlalchemy import inspect

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


def _find_library_fk_name(conn: sa.Connection, table: str) -> str | None:
    """Return the existing FK name on ``table.library_id`` → ``libraries.id``.

    The name is looked up via the SQLAlchemy ``Inspector`` rather than
    hard-coded, so the migration works regardless of which naming
    convention (or none) produced the original constraint.  PostgreSQL
    defaults to ``<table>_<column>_fkey`` while a project configured with
    SQLAlchemy's recommended convention would yield
    ``fk_<table>_<column>_<referred_table>`` — both resolve here.

    Parameters
    ----------
    conn : sqlalchemy.Connection
        Active migration connection.
    table : str
        Table whose ``library_id`` FK should be inspected.

    Returns
    -------
    str | None
        The constraint name, or ``None`` if no such FK exists or the
        dialect reports it unnamed (e.g. some SQLite schemas).
    """
    insp = inspect(conn)
    for fk in insp.get_foreign_keys(table):
        if (
            fk.get("constrained_columns") == ["library_id"]
            and fk.get("referred_table") == "libraries"
        ):
            return fk.get("name")
    return None


def _backfill_nulls(conn: sa.Connection, table: str) -> None:
    """Fill NULL ``library_id`` values from the active library, then any library.

    Notes
    -----
    ``is_active`` is a ``BOOLEAN`` column.  PostgreSQL strictly forbids
    ``boolean = integer`` comparisons, so the literal ``TRUE`` is used rather
    than ``1``.  ``TRUE``/``FALSE`` are also understood by SQLite (>= 3.23),
    keeping the migration dialect-portable.
    """
    # Active library fallback
    conn.execute(
        sa.text(f"""
            UPDATE {table}
            SET library_id = (
                SELECT ul.library_id
                FROM user_libraries ul
                WHERE ul.is_active = TRUE
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
                SELECT l.id FROM libraries l WHERE l.is_active = TRUE LIMIT 1
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

        # 3. Drop the existing library_id FK (whatever its name) and recreate
        #    it with ON DELETE CASCADE under our canonical name.
        old_fk = _find_library_fk_name(conn, table)
        with op.batch_alter_table(table) as batch_op:
            if old_fk:
                batch_op.drop_constraint(old_fk, type_="foreignkey")
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
