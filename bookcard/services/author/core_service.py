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

"""Core author service for CRUD operations.

Follows Single Responsibility Principle by focusing solely on author data operations.
"""

from sqlmodel import Session, select

from bookcard.models.author_metadata import AuthorMetadata, AuthorUserMetadata
from bookcard.models.config import Library
from bookcard.models.core import Author
from bookcard.repositories.author_repository import AuthorRepository
from bookcard.repositories.calibre_book_repository import CalibreBookRepository
from bookcard.services.author.helpers import ensure_active_library
from bookcard.services.author.lookup_strategies import AuthorLookupStrategyChain
from bookcard.services.author_exceptions import (
    AuthorNotFoundError,
    NoActiveLibraryError,
)
from bookcard.services.config_service import LibraryService


class AuthorCoreService:
    """Core service for author CRUD operations.

    Handles author retrieval, listing, and updates.
    Uses repositories for data access, keeping business logic separate.
    """

    def __init__(
        self,
        session: Session,  # type: ignore[type-arg]
        author_repo: AuthorRepository,
        library_service: LibraryService,
    ) -> None:
        """Initialize author core service.

        Parameters
        ----------
        session : Session
            Database session.
        author_repo : AuthorRepository
            Author repository.
        library_service : LibraryService
            Library service for active library management.
        """
        self._session = session
        self._author_repo = author_repo
        self._library_service = library_service
        self._lookup_chain = AuthorLookupStrategyChain()

    def list_authors(
        self,
        page: int = 1,
        page_size: int = 20,
        filter_type: str | None = None,
    ) -> tuple[list[AuthorMetadata], int]:
        """List authors for the active library with pagination.

        Parameters
        ----------
        page : int
            Page number (1-indexed, default: 1).
        page_size : int
            Number of items per page (default: 20).
        filter_type : str | None
            Filter type: "unmatched" to show only unmatched authors, None for all authors.

        Returns
        -------
        tuple[list[AuthorMetadata], int]
            List of author metadata objects and total count.

        Raises
        ------
        NoActiveLibraryError
            If no active library is found.
        """
        active_library = ensure_active_library(self._library_service)
        if active_library.id is None:
            msg = "Active library ID is None"
            raise NoActiveLibraryError(msg)

        library_id: int = active_library.id
        if filter_type == "unmatched":
            authors, total = self._author_repo.list_unmatched_by_library(
                library_id,
                calibre_db_path=active_library.calibre_db_path,
                calibre_db_file=active_library.calibre_db_file,
                page=page,
                page_size=page_size,
            )
        else:
            authors, total = self._author_repo.list_by_library(
                library_id,
                calibre_db_path=active_library.calibre_db_path,
                calibre_db_file=active_library.calibre_db_file,
                page=page,
                page_size=page_size,
            )
        return authors, total

    def get_author(self, author_id: str) -> AuthorMetadata:
        """Get a single author by ID or OpenLibrary key.

        Parameters
        ----------
        author_id : str
            Author ID (numeric) or OpenLibrary key (e.g., "OL23919A").

        Returns
        -------
        AuthorMetadata
            Author metadata object.

        Raises
        ------
        AuthorNotFoundError
            If author is not found.
        NoActiveLibraryError
            If no active library exists.
        """
        active_library = ensure_active_library(self._library_service)

        if active_library.id is None:
            msg = "Active library ID is None"
            raise NoActiveLibraryError(msg)
        library_id: int = active_library.id
        author = self._lookup_chain.lookup(author_id, library_id, self._author_repo)

        if not author:
            msg = f"Author not found: {author_id}"
            raise AuthorNotFoundError(msg)

        return author

    def get_calibre_author_dict(
        self,
        library: Library,
        calibre_author_id: int,
    ) -> dict[str, object]:
        """Fetch author from Calibre database and build dictionary.

        Used when author doesn't have a row in author_metadata table.

        Parameters
        ----------
        library : Library
            Library object with calibre_db_path and calibre_db_file attributes.
        calibre_author_id : int
            Calibre author identifier.

        Returns
        -------
        dict[str, object]
            Author data dictionary matching unmatched author format.

        Raises
        ------
        AuthorNotFoundError
            If library or Calibre database path not found, or author not found.
        """
        if not hasattr(library, "calibre_db_path") or not library.calibre_db_path:
            msg = "Library or Calibre database path not found"
            raise AuthorNotFoundError(msg)

        calibre_db_path: str = library.calibre_db_path
        calibre_db_file: str = (
            getattr(library, "calibre_db_file", None) or "metadata.db"
        )

        calibre_repo = CalibreBookRepository(
            calibre_db_path,
            calibre_db_file,
        )
        with calibre_repo.get_session() as calibre_session:
            stmt = select(Author).where(Author.id == calibre_author_id)
            calibre_author = calibre_session.exec(stmt).first()

            if not calibre_author:
                msg = f"Calibre author not found: {calibre_author_id}"
                raise AuthorNotFoundError(msg)

            # Build dictionary matching unmatched author format
            return {
                "name": calibre_author.name,
                "key": f"calibre-{calibre_author_id}",
                "calibre_id": calibre_author_id,
                "is_unmatched": True,
                "location": "Local Library (Unmatched)",
            }

    def get_similar_authors(
        self,
        author_id: int,
        library_id: int,
        limit: int = 6,
    ) -> list[AuthorMetadata]:
        """Get similar authors for a given author, filtered by library.

        Parameters
        ----------
        author_id : int
            Author identifier.
        library_id : int
            Library identifier to filter similar authors.
        limit : int
            Maximum number of similar authors to return (default: 6).

        Returns
        -------
        list[AuthorMetadata]
            List of similar author metadata objects.
        """
        return self._author_repo.get_similar_authors_in_library(
            author_id,
            library_id,
            limit=limit,
        )

    def update_author_metadata(
        self, author: AuthorMetadata, update: dict[str, object]
    ) -> None:
        """Update AuthorMetadata fields from update dict.

        Parameters
        ----------
        author : AuthorMetadata
            Author metadata object to update.
        update : dict[str, object]
            Update payload with fields to update.
        """
        # Handle name field separately (only update if truthy)
        if update.get("name"):
            author.name = str(update["name"])

        # Map field names to author attributes for optional string fields
        optional_string_fields = [
            "personal_name",
            "fuller_name",
            "title",
            "birth_date",
            "death_date",
            "entity_type",
            "biography",
            "location",
            "photo_url",
        ]

        for field_name in optional_string_fields:
            if field_name in update:
                value = update[field_name]
                setattr(author, field_name, str(value) if value else None)

    def update_user_metadata(self, author_id: int, update: dict[str, object]) -> None:
        """Update user-defined metadata fields.

        Parameters
        ----------
        author_id : int
            Author metadata ID.
        update : dict[str, object]
            Update payload with fields to update.
        """
        user_metadata_fields = ["genres", "styles", "shelves", "similar_authors"]
        for field_name in user_metadata_fields:
            if field_name in update:
                value = update[field_name]
                if value is None:
                    # Delete user-defined value to allow auto-population
                    self._delete_user_metadata(author_id, field_name)
                elif isinstance(value, list):
                    # Save as user-defined - convert to list[str] for type safety
                    str_list = [str(item) for item in value]
                    self._save_user_metadata(author_id, field_name, str_list)

    def _save_user_metadata(
        self,
        author_metadata_id: int,
        field_name: str,
        value: list[str] | dict[str, object] | str,
    ) -> None:
        """Save or update user-defined metadata field.

        Parameters
        ----------
        author_metadata_id : int
            Author metadata ID.
        field_name : str
            Field name (e.g., "genres", "styles").
        value : list[str] | dict[str, object] | str
            Field value to save.
        """
        # Check if user metadata already exists
        existing = self._session.exec(
            select(AuthorUserMetadata).where(
                AuthorUserMetadata.author_metadata_id == author_metadata_id,
                AuthorUserMetadata.field_name == field_name,
            )
        ).first()

        if existing:
            existing.field_value = value  # type: ignore[assignment]
            existing.is_user_defined = True
            self._session.add(existing)
        else:
            user_metadata = AuthorUserMetadata(
                author_metadata_id=author_metadata_id,
                field_name=field_name,
                field_value=value,  # type: ignore[arg-type]
                is_user_defined=True,
            )
            self._session.add(user_metadata)

    def _delete_user_metadata(
        self,
        author_metadata_id: int,
        field_name: str,
    ) -> None:
        """Delete user-defined metadata field (allows auto-population).

        Parameters
        ----------
        author_metadata_id : int
            Author metadata ID.
        field_name : str
            Field name to delete.
        """
        existing = self._session.exec(
            select(AuthorUserMetadata).where(
                AuthorUserMetadata.author_metadata_id == author_metadata_id,
                AuthorUserMetadata.field_name == field_name,
            )
        ).first()

        if existing:
            self._session.delete(existing)
