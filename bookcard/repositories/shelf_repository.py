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

"""Repository layer for shelf persistence operations.

Provides data access for shelves and book-shelf associations.
Shelves are stored in the application database (bookcard.db), not Calibre's metadata.db.
"""

from __future__ import annotations

from sqlalchemy import desc, func
from sqlmodel import Session, or_, select

from bookcard.models.shelves import BookShelfLink, Shelf


class ShelfRepository:
    """Repository for Shelf entities.

    Provides CRUD operations and specialized queries for shelves.
    """

    def __init__(self, session: Session) -> None:
        """Initialize shelf repository.

        Parameters
        ----------
        session : Session
            Active SQLModel session.
        """
        self._session = session

    def add(self, shelf: Shelf) -> Shelf:
        """Add a new shelf to the session.

        Parameters
        ----------
        shelf : Shelf
            Shelf instance to persist.

        Returns
        -------
        Shelf
            The added shelf instance.
        """
        self._session.add(shelf)
        return shelf

    def get(self, shelf_id: int) -> Shelf | None:
        """Retrieve a shelf by ID.

        Parameters
        ----------
        shelf_id : int
            Shelf primary key.

        Returns
        -------
        Shelf | None
            Shelf entity if found, None otherwise.
        """
        return self._session.get(Shelf, shelf_id)

    def find_by_library_and_user(
        self,
        library_id: int,
        user_id: int,
        include_public: bool = True,
    ) -> list[Shelf]:
        """Find shelves for a library and user.

        Parameters
        ----------
        library_id : int
            Library ID to filter by.
        user_id : int
            User ID to find shelves for.
        include_public : bool
            Whether to include public shelves (default: True).

        Returns
        -------
        list[Shelf]
            List of shelves in the library owned by the user, optionally including public shelves.
            Sorted by created_at descending (newest first).
        """
        if include_public:
            stmt = (
                select(Shelf)
                .where(
                    Shelf.library_id == library_id,
                    Shelf.is_active == True,  # noqa: E712
                    or_(
                        Shelf.user_id == user_id,
                        Shelf.is_public == True,  # noqa: E712
                    ),
                )
                .order_by(desc(Shelf.created_at))
            )
        else:
            stmt = (
                select(Shelf)
                .where(
                    Shelf.library_id == library_id,
                    Shelf.is_active == True,  # noqa: E712
                    Shelf.user_id == user_id,
                )
                .order_by(desc(Shelf.created_at))
            )
        return list(self._session.exec(stmt).all())

    def find_by_library(self, library_id: int) -> list[Shelf]:
        """Find all shelves for a library (regardless of user or active status).

        Parameters
        ----------
        library_id : int
            Library ID to filter by.

        Returns
        -------
        list[Shelf]
            List of all shelves in the library.
        """
        stmt = select(Shelf).where(Shelf.library_id == library_id)
        return list(self._session.exec(stmt).all())

    def sync_active_status_for_library(
        self,
        library_id: int,
        is_active: bool,
    ) -> None:
        """Sync shelf active status with library active status.

        Updates all shelves belonging to a library to match the library's
        active status. This is called when a library is activated or deactivated.

        Parameters
        ----------
        library_id : int
            Library ID whose shelves should be synced.
        is_active : bool
            Active status to set for all shelves in the library.
        """
        shelves = self.find_by_library(library_id)
        for shelf in shelves:
            shelf.is_active = is_active
            self._session.add(shelf)
        self._session.flush()

    def find_public_shelves(self, library_id: int) -> list[Shelf]:
        """Find all public shelves in a library.

        Parameters
        ----------
        library_id : int
            Library ID to filter by.

        Returns
        -------
        list[Shelf]
            List of all public shelves in the library.
        """
        stmt = select(Shelf).where(
            Shelf.library_id == library_id,
            Shelf.is_public == True,  # noqa: E712
        )
        return list(self._session.exec(stmt).all())

    def find_by_uuid(self, uuid: str) -> Shelf | None:
        """Find a shelf by UUID.

        Parameters
        ----------
        uuid : str
            Shelf UUID.

        Returns
        -------
        Shelf | None
            Shelf if found, None otherwise.
        """
        stmt = select(Shelf).where(Shelf.uuid == uuid)
        return self._session.exec(stmt).first()

    def find_by_name(
        self,
        library_id: int,
        name: str,
        user_id: int | None,
        is_public: bool,
    ) -> Shelf | None:
        """Find a shelf by library, name, user, and public status.

        Parameters
        ----------
        library_id : int
            Library ID to filter by.
        name : str
            Shelf name to search for.
        user_id : int | None
            User ID for private shelves. Ignored for public shelves.
        is_public : bool
            Whether to search for public shelves.

        Returns
        -------
        Shelf | None
            Shelf if found, None otherwise.
        """
        stmt = select(Shelf).where(
            Shelf.library_id == library_id,
            Shelf.name == name,
            Shelf.is_public == is_public,
        )
        if not is_public and user_id is not None:
            stmt = stmt.where(Shelf.user_id == user_id)
        return self._session.exec(stmt).first()

    def check_name_unique(
        self,
        library_id: int,
        name: str,
        user_id: int,
        is_public: bool,
        exclude_id: int | None = None,
    ) -> bool:
        """Check if a shelf name is unique for the given library, user/public status.

        Parameters
        ----------
        library_id : int
            Library ID to check within.
        name : str
            Shelf name to check.
        user_id : int
            User ID (for private shelves) or any user (for public shelves).
        is_public : bool
            Whether checking for public shelf uniqueness.
        exclude_id : int | None
            Shelf ID to exclude from check (for updates).

        Returns
        -------
        bool
            True if name is unique, False otherwise.
        """
        stmt = select(Shelf).where(
            Shelf.library_id == library_id,
            Shelf.name == name,
            Shelf.is_public == is_public,
        )
        if not is_public:
            stmt = stmt.where(Shelf.user_id == user_id)
        if exclude_id is not None:
            stmt = stmt.where(Shelf.id != exclude_id)
        existing = self._session.exec(stmt).first()
        return existing is None

    def delete(self, shelf: Shelf) -> None:
        """Delete a shelf.

        Parameters
        ----------
        shelf : Shelf
            Shelf to delete.
        """
        self._session.delete(shelf)


class BookShelfLinkRepository:
    """Repository for BookShelfLink entities.

    Manages book-shelf associations and ordering.
    """

    def __init__(self, session: Session) -> None:
        """Initialize book-shelf link repository.

        Parameters
        ----------
        session : Session
            Active SQLModel session.
        """
        self._session = session

    def add(self, link: BookShelfLink) -> BookShelfLink:
        """Add a new book-shelf link.

        Parameters
        ----------
        link : BookShelfLink
            Link instance to persist.

        Returns
        -------
        BookShelfLink
            The added link instance.
        """
        self._session.add(link)
        return link

    def get(self, link_id: int) -> BookShelfLink | None:
        """Retrieve a link by ID.

        Parameters
        ----------
        link_id : int
            Link primary key.

        Returns
        -------
        BookShelfLink | None
            Link entity if found, None otherwise.
        """
        return self._session.get(BookShelfLink, link_id)

    def find_by_shelf(self, shelf_id: int) -> list[BookShelfLink]:
        """Find all book links for a shelf.

        Parameters
        ----------
        shelf_id : int
            Shelf ID.

        Returns
        -------
        list[BookShelfLink]
            List of book-shelf links, ordered by order field.
        """
        stmt = (
            select(BookShelfLink)
            .where(BookShelfLink.shelf_id == shelf_id)
            .order_by(BookShelfLink.order)
        )
        return list(self._session.exec(stmt).all())

    def find_by_book(self, book_id: int) -> list[BookShelfLink]:
        """Find all shelf links for a book.

        Parameters
        ----------
        book_id : int
            Calibre book ID.

        Returns
        -------
        list[BookShelfLink]
            List of book-shelf links for the book.
        """
        stmt = select(BookShelfLink).where(BookShelfLink.book_id == book_id)
        return list(self._session.exec(stmt).all())

    def find_by_shelf_and_book(
        self,
        shelf_id: int,
        book_id: int,
    ) -> BookShelfLink | None:
        """Find a specific book-shelf link.

        Parameters
        ----------
        shelf_id : int
            Shelf ID.
        book_id : int
            Calibre book ID.

        Returns
        -------
        BookShelfLink | None
            Link if found, None otherwise.
        """
        stmt = select(BookShelfLink).where(
            BookShelfLink.shelf_id == shelf_id,
            BookShelfLink.book_id == book_id,
        )
        return self._session.exec(stmt).first()

    def get_max_order(self, shelf_id: int) -> int:
        """Get the maximum order value for a shelf.

        Parameters
        ----------
        shelf_id : int
            Shelf ID.

        Returns
        -------
        int
            Maximum order value, or 0 if no books in shelf.
        """
        stmt = select(func.max(BookShelfLink.order)).where(
            BookShelfLink.shelf_id == shelf_id,
        )
        result = self._session.exec(stmt).first()
        return result if result is not None else 0

    def reorder_books(
        self,
        shelf_id: int,
        book_orders: dict[int, int],
    ) -> None:
        """Update order values for books in a shelf.

        Parameters
        ----------
        shelf_id : int
            Shelf ID.
        book_orders : dict[int, int]
            Mapping of book_id to new order value.
        """
        for book_id, order in book_orders.items():
            link = self.find_by_shelf_and_book(shelf_id, book_id)
            if link is not None:
                link.order = order
                self._session.add(link)

    def delete(self, link: BookShelfLink) -> None:
        """Delete a book-shelf link.

        Parameters
        ----------
        link : BookShelfLink
            Link to delete.
        """
        self._session.delete(link)

    def delete_by_shelf(self, shelf_id: int) -> None:
        """Delete all links for a shelf.

        Parameters
        ----------
        shelf_id : int
            Shelf ID.
        """
        links = self.find_by_shelf(shelf_id)
        for link in links:
            self._session.delete(link)
