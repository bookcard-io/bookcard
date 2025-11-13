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

"""Shelf service for managing book shelves.

Business logic for creating, updating, and managing shelves and book-shelf associations.
"""

from __future__ import annotations

from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from fundamental.models.shelves import BookShelfLink, Shelf

if TYPE_CHECKING:
    from sqlmodel import Session

    from fundamental.repositories.shelf_repository import (
        BookShelfLinkRepository,
        ShelfRepository,
    )


class ShelfService:
    """Operations for managing shelves and book-shelf associations.

    Parameters
    ----------
    session : Session
        Active SQLModel session.
    shelf_repo : ShelfRepository
        Repository for shelf persistence operations.
    link_repo : BookShelfLinkRepository
        Repository for book-shelf link persistence operations.
    """

    def __init__(
        self,
        session: Session,  # type: ignore[type-arg]
        shelf_repo: ShelfRepository,
        link_repo: BookShelfLinkRepository,
        data_directory: str = "/data",
    ) -> None:
        self._session = session
        self._shelf_repo = shelf_repo
        self._link_repo = link_repo
        self._data_directory = Path(data_directory)
        self._ensure_data_directory_exists()

    def _ensure_data_directory_exists(self) -> None:
        """Ensure the data directory and shelves subdirectory exist."""
        self._data_directory.mkdir(parents=True, exist_ok=True)
        (self._data_directory / "shelves").mkdir(parents=True, exist_ok=True)

    def _get_shelf_directory(self, shelf_id: int) -> Path:
        """Get the directory for a shelf's assets.

        Parameters
        ----------
        shelf_id : int
            Shelf identifier.

        Returns
        -------
        Path
            Path to shelf's asset directory.
        """
        return self._data_directory / "shelves" / str(shelf_id)

    def create_shelf(
        self,
        library_id: int,
        user_id: int,
        name: str,
        is_public: bool,
        description: str | None = None,
    ) -> Shelf:
        """Create a new shelf.

        Parameters
        ----------
        library_id : int
            Library ID the shelf belongs to.
        user_id : int
            User ID of the shelf owner.
        name : str
            Shelf name (must be unique per library/user for private, per library for public).
        is_public : bool
            Whether the shelf is shared with everyone.

        Returns
        -------
        Shelf
            Created shelf instance.

        Raises
        ------
        ValueError
            If a shelf with the same name already exists for the library/user/public scope.
        """
        if not self._shelf_repo.check_name_unique(library_id, name, user_id, is_public):
            msg = f"Shelf name '{name}' already exists in this library"
            raise ValueError(msg)

        shelf = Shelf(
            name=name,
            description=description,
            is_public=is_public,
            is_active=True,  # New shelves are active by default (library should be active)
            user_id=user_id,
            library_id=library_id,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            last_modified=datetime.now(UTC),
        )
        self._shelf_repo.add(shelf)
        self._session.flush()
        return shelf

    def update_shelf(
        self,
        shelf_id: int,
        user_id: int,
        name: str | None = None,
        description: str | None = None,
        is_public: bool | None = None,
    ) -> Shelf:
        """Update a shelf.

        Parameters
        ----------
        shelf_id : int
            Shelf ID to update.
        user_id : int
            User ID requesting the update (for permission check).
        name : str | None
            New shelf name (optional).
        is_public : bool | None
            New public status (optional).

        Returns
        -------
        Shelf
            Updated shelf instance.

        Raises
        ------
        ValueError
            If shelf not found, permission denied, or name conflict.
        """
        shelf = self._shelf_repo.get(shelf_id)
        if shelf is None:
            msg = f"Shelf {shelf_id} not found"
            raise ValueError(msg)

        if not self.can_edit_shelf(shelf, user_id, False):
            msg = "Permission denied: cannot edit this shelf"
            raise ValueError(msg)

        if name is not None:
            if not self._shelf_repo.check_name_unique(
                shelf.library_id,
                name,
                user_id,
                shelf.is_public if is_public is None else is_public,
                exclude_id=shelf_id,
            ):
                msg = f"Shelf name '{name}' already exists in this library"
                raise ValueError(msg)
            shelf.name = name
        if description is not None:
            shelf.description = description
        if is_public is not None:
            shelf.is_public = is_public

        shelf.updated_at = datetime.now(UTC)
        self._session.flush()
        return shelf

    def delete_shelf(self, shelf_id: int, user_id: int) -> None:
        """Delete a shelf and all its book associations.

        Parameters
        ----------
        shelf_id : int
            Shelf ID to delete.
        user_id : int
            User ID requesting the deletion (for permission check).

        Raises
        ------
        ValueError
            If shelf not found or permission denied.
        """
        shelf = self._shelf_repo.get(shelf_id)
        if shelf is None:
            msg = f"Shelf {shelf_id} not found"
            raise ValueError(msg)

        if not self.can_edit_shelf(shelf, user_id, False):
            msg = "Permission denied: cannot delete this shelf"
            raise ValueError(msg)

        # Delete all book-shelf links
        self._link_repo.delete_by_shelf(shelf_id)
        # Delete the shelf
        self._shelf_repo.delete(shelf)
        self._session.flush()

    def add_book_to_shelf(
        self,
        shelf_id: int,
        book_id: int,
        user_id: int,
    ) -> BookShelfLink:
        """Add a book to a shelf.

        Parameters
        ----------
        shelf_id : int
            Shelf ID.
        book_id : int
            Calibre book ID.
        user_id : int
            User ID requesting the addition (for permission check).

        Returns
        -------
        BookShelfLink
            Created book-shelf link.

        Raises
        ------
        ValueError
            If shelf not found, permission denied, or book already in shelf.
        """
        shelf = self._shelf_repo.get(shelf_id)
        if shelf is None:
            msg = f"Shelf {shelf_id} not found"
            raise ValueError(msg)

        if not self.can_edit_shelf(shelf, user_id, False):
            msg = "Permission denied: cannot add books to this shelf"
            raise ValueError(msg)

        # Check if book is already in shelf
        existing = self._link_repo.find_by_shelf_and_book(shelf_id, book_id)
        if existing is not None:
            msg = f"Book {book_id} is already in shelf {shelf.name}"
            raise ValueError(msg)

        # Get max order and add 1
        max_order = self._link_repo.get_max_order(shelf_id)
        link = BookShelfLink(
            shelf_id=shelf_id,
            book_id=book_id,
            order=max_order + 1,
            date_added=datetime.now(UTC),
        )
        self._link_repo.add(link)

        # Update shelf last_modified
        shelf.last_modified = datetime.now(UTC)
        self._session.flush()
        return link

    def remove_book_from_shelf(
        self,
        shelf_id: int,
        book_id: int,
        user_id: int,
    ) -> None:
        """Remove a book from a shelf.

        Parameters
        ----------
        shelf_id : int
            Shelf ID.
        book_id : int
            Calibre book ID.
        user_id : int
            User ID requesting the removal (for permission check).

        Raises
        ------
        ValueError
            If shelf not found, permission denied, or book not in shelf.
        """
        shelf = self._shelf_repo.get(shelf_id)
        if shelf is None:
            msg = f"Shelf {shelf_id} not found"
            raise ValueError(msg)

        if not self.can_edit_shelf(shelf, user_id, False):
            msg = "Permission denied: cannot remove books from this shelf"
            raise ValueError(msg)

        link = self._link_repo.find_by_shelf_and_book(shelf_id, book_id)
        if link is None:
            msg = f"Book {book_id} is not in shelf {shelf.name}"
            raise ValueError(msg)

        self._link_repo.delete(link)

        # Update shelf last_modified
        shelf.last_modified = datetime.now(UTC)
        self._session.flush()

    def reorder_books(
        self,
        shelf_id: int,
        book_orders: dict[int, int],
        user_id: int,
    ) -> None:
        """Reorder books in a shelf.

        Parameters
        ----------
        shelf_id : int
            Shelf ID.
        book_orders : dict[int, int]
            Mapping of book_id to new order value.
        user_id : int
            User ID requesting the reorder (for permission check).

        Raises
        ------
        ValueError
            If shelf not found or permission denied.
        """
        shelf = self._shelf_repo.get(shelf_id)
        if shelf is None:
            msg = f"Shelf {shelf_id} not found"
            raise ValueError(msg)

        if not self.can_edit_shelf(shelf, user_id, False):
            msg = "Permission denied: cannot reorder books in this shelf"
            raise ValueError(msg)

        self._link_repo.reorder_books(shelf_id, book_orders)

        # Update shelf last_modified
        shelf.last_modified = datetime.now(UTC)
        self._session.flush()

    def can_edit_shelf(
        self,
        shelf: Shelf,
        user_id: int,
        is_admin: bool,
    ) -> bool:
        """Check if a user can edit a shelf.

        Parameters
        ----------
        shelf : Shelf
            Shelf to check.
        user_id : int
            User ID to check permissions for.
        is_admin : bool
            Whether the user is an admin.

        Returns
        -------
        bool
            True if user can edit the shelf, False otherwise.
        """
        # Private shelf: only owner can edit
        if not shelf.is_public:
            return shelf.user_id == user_id

        # Public shelf: owner or admin can edit
        # (In future, can check for shelves:edit permission)
        return shelf.user_id == user_id or is_admin

    def can_view_shelf(
        self,
        shelf: Shelf,
        user_id: int | None,
    ) -> bool:
        """Check if a user can view a shelf.

        Parameters
        ----------
        shelf : Shelf
            Shelf to check.
        user_id : int | None
            User ID to check permissions for (None for anonymous).

        Returns
        -------
        bool
            True if user can view the shelf, False otherwise.
        """
        # Public shelves: everyone can view
        if shelf.is_public:
            return True

        # Private shelves: only owner can view
        if user_id is None:
            return False
        return shelf.user_id == user_id

    def list_user_shelves(
        self,
        library_id: int,
        user_id: int,
        include_public: bool = True,
    ) -> list[Shelf]:
        """List shelves accessible to a user in a library.

        Parameters
        ----------
        library_id : int
            Library ID to filter by.
        user_id : int
            User ID.
        include_public : bool
            Whether to include public shelves (default: True).

        Returns
        -------
        list[Shelf]
            List of shelves accessible to the user in the library.
        """
        return self._shelf_repo.find_by_library_and_user(
            library_id,
            user_id,
            include_public=include_public,
        )

    def sync_shelf_status_with_library(
        self,
        library_id: int,
        is_active: bool,
    ) -> None:
        """Sync shelf active status with library active status.

        When a library is activated or deactivated, all shelves belonging
        to that library should have their is_active status updated to match.

        Parameters
        ----------
        library_id : int
            Library ID whose shelves should be synced.
        is_active : bool
            Active status to set for all shelves in the library.
        """
        self._shelf_repo.sync_active_status_for_library(library_id, is_active)

    def upload_cover_picture(
        self,
        shelf_id: int,
        user_id: int,
        file_content: bytes,
        filename: str,
    ) -> Shelf:
        """Upload and save a shelf's cover picture.

        Saves the file to {data_directory}/shelves/{shelf_id}/{filename} and updates
        the shelf's cover_picture field. Deletes any existing cover picture
        file before saving the new one.

        Parameters
        ----------
        shelf_id : int
            Shelf identifier.
        user_id : int
            User identifier (must own the shelf).
        file_content : bytes
            File content to save.
        filename : str
            Original filename.

        Returns
        -------
        Shelf
            Updated shelf entity.

        Raises
        ------
        ValueError
            If shelf not found, user doesn't own shelf, invalid file extension,
            or file save fails.
        PermissionError
            If user doesn't have permission to update the shelf.
        """
        shelf = self._shelf_repo.get(shelf_id)
        if shelf is None:
            msg = "shelf_not_found"
            raise ValueError(msg)

        if shelf.user_id != user_id:
            msg = "permission_denied"
            raise PermissionError(msg)

        # Validate file extension
        file_ext = Path(filename).suffix.lower()
        if not file_ext or file_ext not in {
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".webp",
            ".svg",
        }:
            msg = "invalid_file_type"
            raise ValueError(msg)

        # Delete old cover picture if exists
        if shelf.cover_picture:
            old_path = Path(shelf.cover_picture)
            if old_path.is_absolute():
                # Absolute path - delete directly
                with suppress(OSError):
                    old_path.unlink()
            else:
                # Relative path - construct full path
                full_old_path = self._data_directory / shelf.cover_picture
                with suppress(OSError):
                    full_old_path.unlink()

        # Create shelf directory
        shelf_dir = self._get_shelf_directory(shelf_id)
        shelf_dir.mkdir(parents=True, exist_ok=True)

        # Save new file (use original filename)
        cover_path = shelf_dir / filename
        try:
            cover_path.write_bytes(file_content)
        except OSError as exc:
            msg = f"failed_to_save_file: {exc!s}"
            raise ValueError(msg) from exc

        # Update shelf record with relative path from data_directory
        # Store as relative path so it works if data_directory changes
        relative_path = cover_path.relative_to(self._data_directory)
        shelf.cover_picture = str(relative_path)
        shelf.updated_at = datetime.now(UTC)
        self._session.flush()
        return shelf

    def delete_cover_picture(
        self,
        shelf_id: int,
        user_id: int,
    ) -> Shelf:
        """Delete a shelf's cover picture.

        Removes the cover picture file and clears the shelf's cover_picture field.

        Parameters
        ----------
        shelf_id : int
            Shelf identifier.
        user_id : int
            User identifier (must own the shelf).

        Returns
        -------
        Shelf
            Updated shelf entity.

        Raises
        ------
        ValueError
            If shelf not found.
        PermissionError
            If user doesn't have permission to update the shelf.
        """
        shelf = self._shelf_repo.get(shelf_id)
        if shelf is None:
            msg = "shelf_not_found"
            raise ValueError(msg)

        if shelf.user_id != user_id:
            msg = "permission_denied"
            raise PermissionError(msg)

        # Delete cover picture file if exists
        if shelf.cover_picture:
            cover_path = Path(shelf.cover_picture)
            if cover_path.is_absolute():
                # Absolute path - delete directly
                full_path = cover_path
            else:
                # Relative path - construct full path
                full_path = self._data_directory / shelf.cover_picture

            if full_path.exists():
                with suppress(OSError):
                    full_path.unlink()

        shelf.cover_picture = None
        shelf.updated_at = datetime.now(UTC)
        self._session.flush()
        return shelf
