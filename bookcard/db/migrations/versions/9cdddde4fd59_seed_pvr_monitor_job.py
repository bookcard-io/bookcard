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

"""Seed PVR monitor job.

Revision ID: 9cdddde4fd59
Revises: 8bcccde3ec48
Create Date: 2025-12-28 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import column, table

# revision identifiers, used by Alembic.
revision = "9cdddde4fd59"
down_revision = "8bcccde3ec48"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Detect database dialect
    op.get_bind()

    # Define table
    jobs_table = table(
        "scheduled_job_definitions",
        column("job_name", sa.String),
        column("task_type", sa.String),
        column("cron_expression", sa.String),
        column("enabled", sa.Boolean),
        column("description", sa.String),
        column("created_at", sa.DateTime),
        column("updated_at", sa.DateTime),
    )

    # Insert data
    # We cast task_type to the enum type if on postgres, otherwise string is fine
    # But since we are using op.execute with table object, SQLAlchemy handles some of it.
    # However, if the column is strictly typed ENUM in postgres, we might need to be careful.
    # The safest way in Alembic for data migration with Enums is often raw SQL or ensuring the Enum type is available.
    # But here we will try simple insert. If task_type is VARCHAR in SQLite it works.
    # In Postgres it is an Enum.

    op.execute(
        jobs_table.insert().values(
            job_name="pvr_download_monitor",
            task_type="PVR_DOWNLOAD_MONITOR",
            cron_expression="*/1 * * * *",
            enabled=True,
            description="Monitors active downloads and imports completed books",
            created_at=sa.func.now(),
            updated_at=sa.func.now(),
        )
    )


def downgrade() -> None:
    """Downgrade database schema."""
    op.execute(
        "DELETE FROM scheduled_job_definitions WHERE job_name = 'pvr_download_monitor'"
    )
