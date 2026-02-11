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

"""Add library_id to book_shelf_links.

Revision ID: 6c30f249c5fa
Revises: c1e626fc8d52
Create Date: 2026-02-08 19:32:33.139806
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlmodel import Session, select

from bookcard.models.shelves import BookShelfLink, Shelf

# revision identifiers, used by Alembic.
revision: str = "6c30f249c5fa"
down_revision: str | Sequence[str] | None = "c1e626fc8d52"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Add library_id as nullable first (to allow data population)
    op.add_column(
        "book_shelf_links",
        sa.Column("library_id", sa.Integer(), nullable=True),
    )

    # 2. Populate library_id from the parent shelf's library_id using ORM
    bind = op.get_bind()
    session = Session(bind=bind)
    links = session.exec(select(BookShelfLink)).all()
    for link in links:
        shelf = session.get(Shelf, link.shelf_id)
        if shelf:
            link.library_id = shelf.library_id
    session.flush()

    # 3. Use batch mode for SQLite compatibility: make NOT NULL,
    #    add index, unique constraint, and foreign key
    with op.batch_alter_table("book_shelf_links") as batch_op:
        batch_op.alter_column("library_id", nullable=False)
        batch_op.create_index(
            "ix_book_shelf_links_library_id",
            ["library_id"],
            unique=False,
        )
        batch_op.create_unique_constraint(
            "uq_shelf_book_library",
            ["shelf_id", "book_id", "library_id"],
        )
        batch_op.create_foreign_key(
            "fk_book_shelf_links_library_id",
            "libraries",
            ["library_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("book_shelf_links") as batch_op:
        batch_op.drop_constraint(
            "fk_book_shelf_links_library_id",
            type_="foreignkey",
        )
        batch_op.drop_constraint(
            "uq_shelf_book_library",
            type_="unique",
        )
        batch_op.drop_index("ix_book_shelf_links_library_id")
        batch_op.drop_column("library_id")
