# The MIT License (MIT)

# Copyright (c) 2025 knguyen and others

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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

# Define which tables belong to the auth models (exclude Calibre models)
AUTH_TABLES = {
    "users",
    "user_settings",
    "roles",
    "permissions",
    "user_roles",
    "role_permissions",
    "refresh_tokens",
    "invites",
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
    """Filter objects to only include auth-related tables.

    Excludes all Calibre database models (core, media, reading, system)
    from Alembic migrations.

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
        return name in AUTH_TABLES
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
