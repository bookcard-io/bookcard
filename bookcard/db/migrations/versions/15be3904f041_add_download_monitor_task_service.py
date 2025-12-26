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

"""Add download monitor task service.

Revision ID: 15be3904f041
Revises: 132c759984a6
Create Date: 2025-12-25 13:42:11.056491

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "15be3904f041"
down_revision: str | Sequence[str] | None = "132c759984a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Detect database dialect
    connection = op.get_bind()
    is_postgresql = connection.dialect.name == "postgresql"

    # Define the enum type for task_type column with new value
    task_type_enum = sa.Enum(
        "BOOK_UPLOAD",
        "MULTI_BOOK_UPLOAD",
        "BOOK_CONVERT",
        "BOOK_STRIP_DRM",
        "EMAIL_SEND",
        "METADATA_BACKUP",
        "THUMBNAIL_GENERATE",
        "LIBRARY_SCAN",
        "AUTHOR_METADATA_FETCH",
        "OPENLIBRARY_DUMP_DOWNLOAD",
        "OPENLIBRARY_DUMP_INGEST",
        "EPUB_FIX_SINGLE",
        "EPUB_FIX_BATCH",
        "EPUB_FIX_DAILY_SCAN",
        "INGEST_DISCOVERY",
        "INGEST_BOOK",
        "PVR_DOWNLOAD_MONITOR",
        name="tasktype",
        native_enum=False,
    )

    if is_postgresql:
        op.alter_column(
            "task_statistics",
            "task_type",
            existing_type=sa.VARCHAR(length=50),
            type_=task_type_enum,
            existing_nullable=False,
        )
        op.alter_column(
            "tasks",
            "task_type",
            existing_type=sa.VARCHAR(length=50),
            type_=task_type_enum,
            existing_nullable=False,
        )
    else:
        # SQLite: Use batch operations to recreate table with new column type
        with op.batch_alter_table("task_statistics", schema=None) as batch_op:
            batch_op.alter_column(
                "task_type",
                existing_type=sa.VARCHAR(length=50),
                type_=task_type_enum,
                existing_nullable=False,
            )
        with op.batch_alter_table("tasks", schema=None) as batch_op:
            batch_op.alter_column(
                "task_type",
                existing_type=sa.VARCHAR(length=50),
                type_=task_type_enum,
                existing_nullable=False,
            )

    # Add pvr_download_monitor_enabled to scheduled_tasks_config
    op.add_column(
        "scheduled_tasks_config",
        sa.Column(
            "pvr_download_monitor_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )

    op.create_table(
        "scheduled_job_definitions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_name", sqlmodel.AutoString(length=255), nullable=False),
        sa.Column("description", sqlmodel.AutoString(length=1000), nullable=True),
        sa.Column(
            "task_type",
            task_type_enum,
            nullable=False,
        ),
        sa.Column(
            "cron_expression",
            sqlmodel.AutoString(length=100),
            nullable=False,
        ),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("arguments", sa.JSON(), nullable=True),
        sa.Column("job_metadata", sa.JSON(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_scheduled_jobs_enabled_name",
        "scheduled_job_definitions",
        ["enabled", "job_name"],
        unique=False,
    )
    op.create_index(
        "idx_scheduled_jobs_task_type",
        "scheduled_job_definitions",
        ["task_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_scheduled_job_definitions_created_at"),
        "scheduled_job_definitions",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_scheduled_job_definitions_cron_expression"),
        "scheduled_job_definitions",
        ["cron_expression"],
        unique=False,
    )
    op.create_index(
        op.f("ix_scheduled_job_definitions_enabled"),
        "scheduled_job_definitions",
        ["enabled"],
        unique=False,
    )
    op.create_index(
        op.f("ix_scheduled_job_definitions_job_name"),
        "scheduled_job_definitions",
        ["job_name"],
        unique=True,
    )
    op.create_index(
        op.f("ix_scheduled_job_definitions_task_type"),
        "scheduled_job_definitions",
        ["task_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_scheduled_job_definitions_user_id"),
        "scheduled_job_definitions",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Detect database dialect
    connection = op.get_bind()
    is_postgresql = connection.dialect.name == "postgresql"

    op.drop_index(
        op.f("ix_scheduled_job_definitions_user_id"),
        table_name="scheduled_job_definitions",
    )
    op.drop_index(
        op.f("ix_scheduled_job_definitions_task_type"),
        table_name="scheduled_job_definitions",
    )
    op.drop_index(
        op.f("ix_scheduled_job_definitions_job_name"),
        table_name="scheduled_job_definitions",
    )
    op.drop_index(
        op.f("ix_scheduled_job_definitions_enabled"),
        table_name="scheduled_job_definitions",
    )
    op.drop_index(
        op.f("ix_scheduled_job_definitions_cron_expression"),
        table_name="scheduled_job_definitions",
    )
    op.drop_index(
        op.f("ix_scheduled_job_definitions_created_at"),
        table_name="scheduled_job_definitions",
    )
    op.drop_index(
        "idx_scheduled_jobs_task_type", table_name="scheduled_job_definitions"
    )
    op.drop_index(
        "idx_scheduled_jobs_enabled_name", table_name="scheduled_job_definitions"
    )
    op.drop_table("scheduled_job_definitions")

    # Remove pvr_download_monitor_enabled from scheduled_tasks_config
    op.drop_column("scheduled_tasks_config", "pvr_download_monitor_enabled")

    # Define the enum type for task_type column (original values)
    task_type_enum = sa.Enum(
        "BOOK_UPLOAD",
        "MULTI_BOOK_UPLOAD",
        "BOOK_CONVERT",
        "BOOK_STRIP_DRM",
        "EMAIL_SEND",
        "METADATA_BACKUP",
        "THUMBNAIL_GENERATE",
        "LIBRARY_SCAN",
        "AUTHOR_METADATA_FETCH",
        "OPENLIBRARY_DUMP_DOWNLOAD",
        "OPENLIBRARY_DUMP_INGEST",
        "EPUB_FIX_SINGLE",
        "EPUB_FIX_BATCH",
        "EPUB_FIX_DAILY_SCAN",
        "INGEST_DISCOVERY",
        "INGEST_BOOK",
        name="tasktype",
        native_enum=False,
    )

    if is_postgresql:
        op.alter_column(
            "tasks",
            "task_type",
            existing_type=sa.VARCHAR(length=50),
            type_=task_type_enum,
            existing_nullable=False,
        )
        op.alter_column(
            "task_statistics",
            "task_type",
            existing_type=sa.VARCHAR(length=50),
            type_=task_type_enum,
            existing_nullable=False,
        )
    else:
        # SQLite: Use batch operations to recreate table with new column type
        with op.batch_alter_table("tasks", schema=None) as batch_op:
            batch_op.alter_column(
                "task_type",
                existing_type=sa.VARCHAR(length=50),
                type_=task_type_enum,
                existing_nullable=False,
            )
        with op.batch_alter_table("task_statistics", schema=None) as batch_op:
            batch_op.alter_column(
                "task_type",
                existing_type=sa.VARCHAR(length=50),
                type_=task_type_enum,
                existing_nullable=False,
            )
