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

"""Seed useful magic shelves.

Revision ID: ade158238c51
Revises: a492c10341b8
Create Date: 2026-02-01 14:03:32.056142

"""

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ade158238c51"
down_revision: str | Sequence[str] | None = "a492c10341b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Seed default Magic Shelves (idempotent).

    Notes
    -----
    - These are created as **public** shelves so every user can benefit.
    - Magic shelves are owned by the first admin user (fallback: first user),
      and are created in exactly one library (active library if present,
      otherwise the first library).
    - Seeding is idempotent per `(library_id, is_public, name)` to avoid
      collisions with user-created shelves.
    """
    connection = op.get_bind()

    users_table = sa.table(
        "users",
        sa.column("id", sa.Integer),
        sa.column("is_admin", sa.Boolean),
        sa.column("created_at", sa.DateTime),
    )
    libraries_table = sa.table(
        "libraries",
        sa.column("id", sa.Integer),
        sa.column("is_active", sa.Boolean),
        sa.column("created_at", sa.DateTime),
    )

    # If there are no users yet, skip seeding (shelves require an owner).
    owner_user_id = connection.execute(
        sa
        .select(users_table.c.id)
        .order_by(
            sa.desc(users_table.c.is_admin),
            users_table.c.created_at.asc(),
            users_table.c.id.asc(),
        )
        .limit(1)
    ).scalar()
    if owner_user_id is None:
        return

    # If there are no libraries yet, skip seeding. Seed into ONE library only.
    library_id = connection.execute(
        sa
        .select(libraries_table.c.id)
        .order_by(
            sa.desc(libraries_table.c.is_active),
            libraries_table.c.created_at.asc(),
            libraries_table.c.id.asc(),
        )
        .limit(1)
    ).scalar()
    if library_id is None:
        return

    now = datetime.now(UTC)

    shelves_table = sa.table(
        "shelves",
        sa.column("uuid", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.String),
        sa.column("cover_picture", sa.String),
        sa.column("is_public", sa.Boolean),
        sa.column("is_active", sa.Boolean),
        sa.column("shelf_type", sa.String),
        sa.column("read_list_metadata", sa.JSON),
        sa.column("filter_rules", sa.JSON),
        sa.column("user_id", sa.Integer),
        sa.column("library_id", sa.Integer),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
        sa.column("last_modified", sa.DateTime),
    )

    seeded_prefix = "Seeded: "

    # Rule helpers (JSON matches bookcard/models/magic_shelf_rules.py)
    def group(join_type: str, rules: list[dict[str, object]]) -> dict[str, object]:
        return {"join_type": join_type, "rules": rules}

    def rule(
        field: str,
        operator: str,
        value: object = None,
    ) -> dict[str, object]:
        return {"field": field, "operator": operator, "value": value}

    seeded_shelves: list[dict[str, object]] = [
        {
            "name": "Series hints (no series set)",
            "description": (
                f"{seeded_prefix}Titles that look like they belong to a series "
                "but have no Series metadata."
            ),
            "filter_rules": group(
                "AND",
                [
                    group(
                        "OR",
                        [
                            rule("TITLE", "CONTAINS", "#"),
                            rule("TITLE", "CONTAINS", "No."),
                            rule("TITLE", "CONTAINS", "Vol"),
                            rule("TITLE", "CONTAINS", "Volume"),
                            rule("TITLE", "CONTAINS", "Book "),
                            rule("TITLE", "CONTAINS", "Part "),
                        ],
                    ),
                    rule("SERIES", "IS_EMPTY", None),
                ],
            ),
        },
        {
            "name": "Missing ISBN",
            "description": f"{seeded_prefix}Books with an empty ISBN field.",
            "filter_rules": group("AND", [rule("ISBN", "IS_EMPTY", None)]),
        },
        {
            "name": "Missing identifiers",
            "description": (
                f"{seeded_prefix}Books that have no Identifier rows "
                "(e.g., no DOI/ASIN/etc.)."
            ),
            "filter_rules": group("AND", [rule("IDENTIFIER", "IS_EMPTY", None)]),
        },
        {
            "name": "Missing authors",
            "description": f"{seeded_prefix}Books without any Authors set.",
            "filter_rules": group("AND", [rule("AUTHOR", "IS_EMPTY", None)]),
        },
        {
            "name": "Missing publisher",
            "description": f"{seeded_prefix}Books without any Publisher set.",
            "filter_rules": group("AND", [rule("PUBLISHER", "IS_EMPTY", None)]),
        },
        {
            "name": "Missing language",
            "description": f"{seeded_prefix}Books without any Language set.",
            "filter_rules": group("AND", [rule("LANGUAGE", "IS_EMPTY", None)]),
        },
        {
            "name": "Untagged",
            "description": f"{seeded_prefix}Books with no Tags set.",
            "filter_rules": group("AND", [rule("TAG", "IS_EMPTY", None)]),
        },
        {
            "name": "Highly rated (≥ 4★)",
            "description": (
                f"{seeded_prefix}Books rated 4 stars or higher "
                "(Calibre stores ratings on a 0-10 scale; ≥ 8 ≈ 4★)."
            ),
            "filter_rules": group("AND", [rule("RATING", "GREATER_THAN_OR_EQUALS", 8)]),
        },
        {
            "name": "Highly rated & recent (since 2026-01-01)",
            "description": (
                f"{seeded_prefix}Books rated 4 stars or higher and released on/after "
                "2026-01-01 (hardcoded cutoff)."
            ),
            "filter_rules": group(
                "AND",
                [
                    rule("RATING", "GREATER_THAN_OR_EQUALS", 8),
                    rule("PUBDATE", "GREATER_THAN_OR_EQUALS", "2026-01-01"),
                ],
            ),
        },
    ]

    for shelf in seeded_shelves:
        name = str(shelf["name"])
        exists = connection.execute(
            sa
            .select(sa.literal(1))
            .select_from(shelves_table)
            .where(
                sa.and_(
                    shelves_table.c.library_id == int(library_id),
                    shelves_table.c.is_public.is_(True),
                    shelves_table.c.name == name,
                )
            )
            .limit(1)
        ).first()

        if exists is not None:
            continue

        op.execute(
            shelves_table.insert().values(
                uuid=str(uuid4()),
                name=name,
                description=str(shelf["description"]),
                cover_picture=None,
                is_public=True,
                is_active=True,
                shelf_type="magic_shelf",
                read_list_metadata=None,
                filter_rules=shelf["filter_rules"],
                user_id=int(owner_user_id),
                library_id=int(library_id),
                created_at=now,
                updated_at=now,
                last_modified=now,
            )
        )


def downgrade() -> None:
    """Remove seeded Magic Shelves (best-effort, safe).

    Notes
    -----
    We only delete shelves that still have the `Seeded: ` prefix in the
    description to avoid deleting user-created or user-edited shelves.
    """
    shelves_table = sa.table(
        "shelves",
        sa.column("description", sa.String),
        sa.column("shelf_type", sa.String),
        sa.column("is_public", sa.Boolean),
    )

    op.execute(
        shelves_table.delete().where(
            sa.and_(
                shelves_table.c.shelf_type == "magic_shelf",
                shelves_table.c.is_public.is_(True),
                sa.func.lower(shelves_table.c.description).like("seeded: %"),
            )
        )
    )
