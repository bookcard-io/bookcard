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

"""Seed all supported scheduled jobs.

Revision ID: a82a45801b29
Revises: 59cd1bc8d36c
Create Date: 2025-01-25 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text
from sqlalchemy.sql import column, table

# revision identifiers, used by Alembic.
revision = "a82a45801b29"
down_revision = "59cd1bc8d36c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema.

    Idempotently seeds all supported scheduled job definitions.
    Only creates jobs that don't already exist in the database.
    """
    connection = op.get_bind()

    # Get existing job names using raw SQL for compatibility
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

    # Define all supported scheduled jobs
    # Each tuple: (job_name, description, task_type, cron_expression, enabled)
    jobs_to_seed = [
        (
            "pvr_download_monitor",
            "Monitor PVR downloads and import completed items",
            "PVR_DOWNLOAD_MONITOR",
            "*/5 * * * *",
            True,
        ),
        (
            "epub_fix_daily_scan",
            "Daily scan for EPUB issues and auto-fix",
            "EPUB_FIX_DAILY_SCAN",
            "0 4 * * *",
            False,
        ),
        (
            "prowlarr_sync",
            "Sync indexers from Prowlarr",
            "PROWLARR_SYNC",
            "0 */6 * * *",
            False,
        ),
        (
            "indexer_health_check",
            "Daily health check for configured indexers",
            "INDEXER_HEALTH_CHECK",
            "0 4 * * *",
            False,
        ),
        (
            "library_scan",
            "Scan library for authors, genres, series, and publishers",
            "LIBRARY_SCAN",
            "0 4 * * 0",  # Weekly on Sunday at 4am UTC
            True,  # Enabled by default
        ),
    ]

    # Insert only jobs that don't exist
    # Use table.insert() which handles JSON columns properly via SQLAlchemy
    for job_name, description, task_type, cron_expression, enabled in jobs_to_seed:
        if job_name in existing_jobs:
            continue

        op.execute(
            jobs_table.insert().values(
                job_name=job_name,
                task_type=task_type,
                cron_expression=cron_expression,
                enabled=enabled,
                description=description,
                arguments={},  # Empty dict, SQLAlchemy will handle JSON conversion
                created_at=sa.func.now(),
                updated_at=sa.func.now(),
            )
        )


def downgrade() -> None:
    """Downgrade database schema.

    Removes all seeded jobs except pvr_download_monitor (which was seeded
    in a previous migration).
    """
    jobs_to_remove = [
        "epub_fix_daily_scan",
        "prowlarr_sync",
        "indexer_health_check",
        "library_scan",
    ]

    for job_name in jobs_to_remove:
        op.execute(
            text(
                "DELETE FROM scheduled_job_definitions WHERE job_name = :job_name"
            ).bindparams(job_name=job_name)
        )
