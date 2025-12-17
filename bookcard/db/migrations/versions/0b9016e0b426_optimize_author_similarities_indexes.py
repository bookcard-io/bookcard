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

"""Optimize author similarities indexes.

Revision ID: 0b9016e0b426
Revises: a71f0722640d
Create Date: 2025-11-21 14:21:24.510712

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0b9016e0b426"
down_revision: str | Sequence[str] | None = "a71f0722640d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add composite index on (author2_id, similarity_score) for efficient queries
    # when author is in author2_id position, ordered by score
    op.create_index(
        "idx_author_similarity_score_author2",
        "author_similarities",
        ["author2_id", "similarity_score"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "idx_author_similarity_score_author2", table_name="author_similarities"
    )
