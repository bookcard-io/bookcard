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

"""Repository base classes.

Provides generic, typed repository for CRUD operations using SQLModel.
Adheres to SRP/IOC: persistence logic is isolated from domain and services.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from sqlmodel import Session, SQLModel, select

if TYPE_CHECKING:
    from collections.abc import Iterable

TModel = TypeVar("TModel", bound=SQLModel)


class Repository[TModel]:
    """Generic repository for a single SQLModel entity.

    Parameters
    ----------
    session : Session
        Active SQLModel session (DI/IOC friendly).
    model_type : type[TModel]
        The SQLModel subclass this repository manages.
    """

    def __init__(self, session: Session, model_type: type[TModel]) -> None:
        self._session = session
        self._model_type = model_type

    def add(self, entity: TModel) -> TModel:
        """Add a new entity to the session.

        Parameters
        ----------
        entity : TModel
            The entity instance to persist.
        """
        self._session.add(entity)
        return entity

    def get(self, entity_id: int) -> TModel | None:
        """Retrieve an entity by primary key.

        Parameters
        ----------
        entity_id : int
            Primary key value.
        """
        return self._session.get(self._model_type, entity_id)

    def list(self, limit: int | None = None, offset: int = 0) -> Iterable[TModel]:
        """List entities with simple pagination.

        Parameters
        ----------
        limit : int | None
            Maximum number of records to return.
        offset : int
            Number of records to skip.
        """
        stmt = select(self._model_type).offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        return self._session.exec(stmt).all()

    def delete(self, entity: TModel) -> None:
        """Delete an entity.

        Parameters
        ----------
        entity : TModel
            The entity instance to remove.
        """
        self._session.delete(entity)

    def flush(self) -> None:
        """Flush pending changes to the database."""
        self._session.flush()

    def refresh(self, entity: TModel) -> TModel:
        """Refresh and return the entity state from the database."""
        self._session.refresh(entity)
        return entity
