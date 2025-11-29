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

"""Add metadata enforcement operations table.

Revision ID: a1b2c3d4e5f6
Revises: f1c9a933a49a
Create Date: 2025-11-27 22:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "676e525dec3d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Detect database dialect
    connection = op.get_bind()
    is_postgresql = connection.dialect.name == "postgresql"

    # Add auto_metadata_enforcement column to libraries table
    if is_postgresql:
        op.add_column(
            "libraries",
            sa.Column(
                "auto_metadata_enforcement",
                sa.Boolean(),
                nullable=False,
                server_default="1",
            ),
        )
    else:
        # SQLite: Use batch operations to add column
        with op.batch_alter_table("libraries", schema=None) as batch_op:
            batch_op.add_column(
                sa.Column(
                    "auto_metadata_enforcement",
                    sa.Boolean(),
                    nullable=False,
                    server_default="1",
                ),
            )

    op.create_table(
        "metadata_enforcement_operations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("library_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "in_progress",
                "completed",
                "failed",
                name="enforcementstatus",
                native_enum=is_postgresql,
                create_type=not is_postgresql,  # Don't create type for PostgreSQL, we do it manually
            ),
            nullable=False,
        ),
        sa.Column("enforced_at", sa.DateTime(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("opf_updated", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("cover_updated", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column(
            "ebook_files_updated", sa.Boolean(), nullable=False, server_default="0"
        ),
        sa.Column("supported_formats", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["library_id"],
            ["libraries.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_metadata_enforcement_operations_book_id"),
        "metadata_enforcement_operations",
        ["book_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_metadata_enforcement_operations_library_id"),
        "metadata_enforcement_operations",
        ["library_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_metadata_enforcement_operations_status"),
        "metadata_enforcement_operations",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_metadata_enforcement_operations_enforced_at"),
        "metadata_enforcement_operations",
        ["enforced_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_metadata_enforcement_operations_created_at"),
        "metadata_enforcement_operations",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Detect database dialect
    connection = op.get_bind()
    is_postgresql = connection.dialect.name == "postgresql"

    op.drop_index(
        op.f("ix_metadata_enforcement_operations_created_at"),
        table_name="metadata_enforcement_operations",
    )
    op.drop_index(
        op.f("ix_metadata_enforcement_operations_enforced_at"),
        table_name="metadata_enforcement_operations",
    )
    op.drop_index(
        op.f("ix_metadata_enforcement_operations_status"),
        table_name="metadata_enforcement_operations",
    )
    op.drop_index(
        op.f("ix_metadata_enforcement_operations_library_id"),
        table_name="metadata_enforcement_operations",
    )
    op.drop_index(
        op.f("ix_metadata_enforcement_operations_book_id"),
        table_name="metadata_enforcement_operations",
    )
    op.drop_table("metadata_enforcement_operations")

    # Drop enum type for PostgreSQL
    if is_postgresql:
        op.execute(sa.text("DROP TYPE IF EXISTS enforcementstatus"))

    # Remove auto_metadata_enforcement column from libraries table
    if is_postgresql:
        op.drop_column("libraries", "auto_metadata_enforcement")
    else:
        # SQLite: Use batch operations to drop column
        with op.batch_alter_table("libraries", schema=None) as batch_op:
            batch_op.drop_column("auto_metadata_enforcement")
