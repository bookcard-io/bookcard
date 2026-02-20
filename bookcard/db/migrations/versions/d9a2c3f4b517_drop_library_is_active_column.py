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

"""Drop Library.is_active column.

Active-library semantics are now per-user via the ``UserLibrary`` table.
The legacy ``Library.is_active`` column is no longer read by any code
path and can be safely removed.

Revision ID: d9a2c3f4b517
Revises: c4f8b2e1a367
Create Date: 2026-02-12 23:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d9a2c3f4b517"
down_revision: str | Sequence[str] | None = "c4f8b2e1a367"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Drop the is_active column and its index from the libraries table."""
    with op.batch_alter_table("libraries") as batch_op:
        batch_op.drop_index("ix_libraries_is_active")
        batch_op.drop_column("is_active")


def downgrade() -> None:
    """Restore the is_active column with a default of False."""
    with op.batch_alter_table("libraries") as batch_op:
        batch_op.add_column(
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default="0")
        )
        batch_op.create_index("ix_libraries_is_active", ["is_active"])
