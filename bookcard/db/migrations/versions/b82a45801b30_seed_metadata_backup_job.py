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

"""Seed metadata backup job.

Revision ID: b82a45801b30
Revises: a82a45801b29
Create Date: 2025-01-25 01:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text
from sqlalchemy.sql import column, table

# revision identifiers, used by Alembic.
revision = "b82a45801b30"
down_revision = "a82a45801b29"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema.

    Idempotently seeds the metadata backup scheduled job.
    """
    connection = op.get_bind()

    # Get existing job names
    result = connection.execute(text("SELECT job_name FROM scheduled_job_definitions"))
    existing_jobs = {row[0] for row in result.fetchall()}

    # Define table
    jobs_table = table(
        "scheduled_job_definitions",
        column("job_name", sa.String),
        column("task_type", sa.String),
        column("cron_expression", sa.String),
        column("enabled", sa.Boolean),
        column("description", sa.String),
        column("arguments", sa.JSON),
        column("created_at", sa.DateTime),
        column("updated_at", sa.DateTime),
    )

    job_name = "metadata_backup_all_libraries"

    if job_name not in existing_jobs:
        op.execute(
            jobs_table.insert().values(
                job_name=job_name,
                task_type="METADATA_BACKUP",
                cron_expression="0 0 * * *",  # Daily at 00:00
                enabled=True,
                description="Backup metadata.db for all libraries",
                arguments={},
                created_at=sa.func.now(),
                updated_at=sa.func.now(),
            )
        )


def downgrade() -> None:
    """Downgrade database schema.

    Removes the metadata backup job.
    """
    jobs_table = table(
        "scheduled_job_definitions",
        column("job_name", sa.String),
    )

    op.execute(
        jobs_table.delete().where(
            jobs_table.c.job_name == "metadata_backup_all_libraries"
        )
    )
