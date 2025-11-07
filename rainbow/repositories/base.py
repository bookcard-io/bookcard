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
