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

"""Alembic environment file."""

from logging.config import fileConfig
from typing import TYPE_CHECKING, Literal

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool
from sqlalchemy.schema import SchemaItem
from sqlmodel import SQLModel

if TYPE_CHECKING:
    from collections.abc import Sequence

from fundamental.models.auth import (
    Invite,
    Permission,
    RefreshToken,
    Role,
    RolePermission,
    User,
    UserRole,
    UserSetting,
)
from fundamental.models.openlibrary import (
    OpenLibraryAuthor,
    OpenLibraryAuthorWork,
    OpenLibraryEdition,
    OpenLibraryEditionIsbn,
    OpenLibraryWork,
)

# Load environment variables from .env file
# The .env file is at the project root, which is 4 levels up from this file
# (fundamental/db/migrations/env.py -> fundamental/db/migrations -> fundamental/db -> moose -> project root)
load_dotenv()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def get_database_url() -> str:
    """Resolve database URL using the application's configuration logic.

    This delegates to ``AppConfig._get_database_url`` to ensure the Alembic
    environment uses the exact same resolution rules (including percent-encoding
    of passwords and support for ``MOOSE_DATABASE_URL``) as the runtime app.
    """
    from fundamental.config import AppConfig

    return AppConfig.from_env().database_url


# add your model's MetaData object here
# for 'autogenerate' support
# All SQLModel table classes have been imported above, which registers them
# with SQLModel.metadata. We use that metadata object for Alembic.
target_metadata = SQLModel.metadata

# Define which tables to exclude from migrations (Calibre models)
# These tables are defined in fundamental/models/core.py, media.py, reading.py, and system.py
EXCLUDED_TABLES = {
    # From core.py
    "authors",
    "publishers",
    "series",
    "tags",
    "languages",
    "ratings",
    "books",
    "comments",
    "identifiers",
    "books_authors_link",
    "books_languages_link",
    "books_publishers_link",
    "books_ratings_link",
    "books_series_link",
    "books_tags_link",
    # From media.py
    "data",
    "conversion_options",
    # From reading.py
    "annotations",
    "annotations_dirtied",
    "last_read_positions",
    # From system.py
    "preferences",
    "library_id",
    "metadata_dirtied",
    "feeds",
    "custom_columns",
    "books_plugin_data",
}

# Define indices to exclude from autogenerate
# These are manually created indices that use PostgreSQL-specific syntax
# (GIN indices with jsonb_path_ops and gin_trgm_ops) that Alembic can't autogenerate,
# or indices that exist in the database but are managed separately from the model
EXCLUDED_INDICES = {
    # OpenLibrary GIN indices created manually in migration 34c7ece3865c
    "ix_openlibrary_authors_data",
    "ix_openlibrary_authors_name",
    "ix_openlibrary_editions_data",
    "ix_openlibrary_editions_subtitle",
    "ix_openlibrary_editions_title",
    "ix_openlibrary_works_data",
    "ix_openlibrary_works_subtitle",
    "ix_openlibrary_works_title",
}


def include_object(
    _obj: SchemaItem,
    name: str | None,
    type_: Literal[
        "schema",
        "table",
        "column",
        "index",
        "unique_constraint",
        "foreign_key_constraint",
    ],
    _reflected: bool,
    _compare_to: SchemaItem | None,
) -> bool:
    """Filter objects to exclude Calibre database models and manually created indices.

    Excludes all tables from fundamental/models/core.py, media.py, reading.py,
    and system.py from Alembic migrations. Also excludes manually created
    PostgreSQL-specific indices that use GIN operators.

    Parameters
    ----------
    _obj : SchemaItem
        The schema item being examined (unused).
    name : str | None
        Name of the object, or None if not applicable.
    type_ : Literal["schema", "table", "column", "index", "unique_constraint", "foreign_key_constraint"]
        Type of object being examined.
    _reflected : bool
        Whether the object was reflected from the database (unused).
    _compare_to : SchemaItem | None
        The schema item being compared against (unused).

    Returns
    -------
    bool
        True to include the object, False to exclude it.
    """
    if type_ == "table" and name is not None:
        return name not in EXCLUDED_TABLES
    if type_ == "index" and name is not None:
        return name not in EXCLUDED_INDICES
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Override the sqlalchemy.url in config with the one from environment
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
