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

"""Service for author rematch operations.

Follows SRP by handling only rematch business logic.
Uses IOC by accepting dependencies (repositories, services, message broker).
Separates concerns: rematch orchestration vs HTTP handling.
"""

import logging
from typing import TYPE_CHECKING, Any, cast

from sqlmodel import Session, select

if TYPE_CHECKING:
    from bookcard.services.author_service import AuthorService

from bookcard.models.author_metadata import AuthorMapping
from bookcard.models.core import Author
from bookcard.repositories.calibre_book_repository import CalibreBookRepository
from bookcard.repositories.config_repository import LibraryRepository
from bookcard.services.config_service import LibraryService
from bookcard.services.library_scanning.pipeline.link_components import (
    AuthorMappingRepository,
)
from bookcard.services.library_scanning.workers.progress import JobProgressTracker
from bookcard.services.messaging.base import MessageBroker
from bookcard.services.messaging.redis_broker import RedisBroker

logger = logging.getLogger(__name__)


class AuthorRematchService:
    """Service for orchestrating author rematch operations.

    Handles OpenLibrary key normalization, ID resolution, Calibre author
    serialization, and message queue operations for rematch jobs.
    """

    def __init__(
        self,
        session: Session,
        author_service: "AuthorService",
        library_repo: LibraryRepository | None = None,
        library_service: LibraryService | None = None,
        message_broker: MessageBroker | None = None,
    ) -> None:
        """Initialize author rematch service.

        Parameters
        ----------
        session : Session
            Database session.
        author_service : AuthorService
            Author service for retrieving author data.
        library_repo : LibraryRepository | None
            Library repository. If None, creates a new instance.
        library_service : LibraryService | None
            Library service. If None, creates a new instance.
        message_broker : MessageBroker | None
            Message broker for enqueueing rematch jobs.
        """
        self._session = session
        self._author_service = author_service
        self._library_repo = library_repo or LibraryRepository(session)
        self._library_service = library_service or LibraryService(
            session, self._library_repo
        )
        self._message_broker = message_broker

    def _raise_no_active_library_error(self) -> None:
        """Raise ValueError for missing active library.

        Raises
        ------
        ValueError
            Always raises with "No active library found" message.
        """
        error_msg = "No active library found"
        raise ValueError(error_msg)

    def normalize_openlibrary_key(self, key: str) -> str:
        """Normalize OpenLibrary key format.

        Ensures the key has the /authors/ prefix.

        Parameters
        ----------
        key : str
            OpenLibrary key (may or may not have prefix).

        Returns
        -------
        str
            Normalized key with /authors/ prefix.
        """
        normalized = key.strip()
        if not normalized.startswith("/authors/"):
            # Remove any existing /authors/ prefix and add it back
            normalized = normalized.replace("/authors/", "").replace("authors/", "")
            normalized = f"/authors/{normalized}"
        return normalized

    def determine_openlibrary_key(
        self,
        provided_olid: str | None,
        author_data: dict[str, Any],
    ) -> str:
        """Determine OpenLibrary key from request or existing author data.

        Parameters
        ----------
        provided_olid : str | None
            Optional OpenLibrary key from request.
        author_data : dict[str, Any]
            Author data dictionary.

        Returns
        -------
        str
            Normalized OpenLibrary key.

        Raises
        ------
        ValueError
            If no valid key can be determined.
        """
        if isinstance(provided_olid, str) and provided_olid.strip():
            key = self.normalize_openlibrary_key(provided_olid)
            logger.info("Using provided OLID (normalized): %s", key)
            return key

        # Use author's existing key, but check if it's a placeholder (calibre-*)
        existing_key = author_data.get("key")
        logger.debug("No OLID provided, checking existing key: %s", existing_key)

        # Check if it's a placeholder key (starts with "calibre-")
        if (
            existing_key
            and isinstance(existing_key, str)
            and existing_key.startswith("calibre-")
        ):
            logger.warning(
                "Author has placeholder key %s but no OLID provided", existing_key
            )
            error_msg = (
                "Author does not have an OpenLibrary key. "
                "Please provide an OLID to match this author."
            )
            raise ValueError(error_msg)

        if not existing_key:
            logger.warning("Author has no key and no OLID provided")
            error_msg = (
                "Author does not have an OpenLibrary key and no OLID was provided"
            )
            raise ValueError(error_msg)

        logger.info("Using existing key: %s", existing_key)
        return str(existing_key)

    def _resolve_via_metadata_id(self, author_metadata_id: int) -> tuple[int, int, int]:
        """Resolve IDs via author metadata ID.

        Parameters
        ----------
        author_metadata_id : int
            Author metadata identifier.

        Returns
        -------
        tuple[int, int, int]
            Tuple of (library_id, calibre_author_id, author_metadata_id).

        Raises
        ------
        ValueError
            If mapping not found.
        """
        stmt = select(AuthorMapping).where(
            AuthorMapping.author_metadata_id == author_metadata_id
        )
        mapping = self._session.exec(stmt).first()

        if not mapping:
            logger.error(
                "Author metadata ID %s found but no mapping exists",
                author_metadata_id,
            )
            error_msg = "Author mapping not found"
            raise ValueError(error_msg)

        library_id = mapping.library_id
        calibre_author_id = mapping.calibre_author_id
        logger.debug(
            "Found mapping: library_id=%s, calibre_author_id=%s",
            library_id,
            calibre_author_id,
        )
        return library_id, calibre_author_id, author_metadata_id

    def _resolve_via_calibre_prefix(
        self, author_id: str
    ) -> tuple[int, int, int | None]:
        """Resolve IDs via calibre- prefix in author_id.

        Parameters
        ----------
        author_id : str
            Author identifier with calibre- prefix.

        Returns
        -------
        tuple[int, int, int | None]
            Tuple of (library_id, calibre_author_id, author_metadata_id).

        Raises
        ------
        ValueError
            If active library not found or invalid author ID format.
        """
        try:
            calibre_author_id = int(author_id.replace("calibre-", ""))
            logger.debug(
                "Extracted calibre_author_id from author_id: %s",
                calibre_author_id,
            )

            # Get active library
            active_library = self._library_service.get_active_library()

            if not active_library:
                self._raise_no_active_library_error()

            library_id_raw = active_library.id  # type: ignore[attr-defined]
            if library_id_raw is None:
                self._raise_no_active_library_error()

            library_id = cast("int", library_id_raw)

            # Check if mapping exists for this calibre author
            mapping_repo = AuthorMappingRepository(self._session)
            mapping = mapping_repo.find_by_calibre_author_id_and_library(
                calibre_author_id,
                library_id,
            )

            if mapping:
                # Mapping exists - use it
                author_metadata_id = mapping.author_metadata_id
                logger.debug(
                    "Found existing mapping: author_metadata_id=%s",
                    author_metadata_id,
                )
            else:
                # No mapping exists yet - this is a truly unmatched author
                # We'll create the mapping during the match process
                logger.info(
                    "No mapping exists for calibre_author_id=%s, library_id=%s - will create during match",
                    calibre_author_id,
                    library_id,
                )
                author_metadata_id = None

            return library_id, calibre_author_id, author_metadata_id  # noqa: TRY300
        except ValueError as exc:
            if "No active library found" in str(exc):
                raise
            logger.exception("Failed to extract calibre_author_id from %s", author_id)
            error_msg = f"Invalid author ID format: {author_id}"
            raise ValueError(error_msg) from exc

    def resolve_library_and_author_ids(
        self,
        author_id: str,
        author_data: dict[str, Any],
    ) -> tuple[int, int, int | None]:
        """Resolve library ID, Calibre author ID, and metadata ID for rematch.

        Parameters
        ----------
        author_id : str
            Author identifier from path.
        author_data : dict[str, Any]
            Author data dictionary.

        Returns
        -------
        tuple[int, int, int | None]
            Tuple of (library_id, calibre_author_id, author_metadata_id).

        Raises
        ------
        ValueError
            If required IDs or mappings cannot be determined.
        """
        raw_author_metadata_id = author_data.get("id")
        author_metadata_id: int | None
        if isinstance(raw_author_metadata_id, int):
            author_metadata_id = raw_author_metadata_id
        else:
            author_metadata_id = None

        logger.debug(
            "Author metadata ID: %s, is_unmatched: %s",
            author_metadata_id,
            author_data.get("is_unmatched", False),
        )

        if author_metadata_id:
            return self._resolve_via_metadata_id(author_metadata_id)

        if author_id.startswith("calibre-"):
            return self._resolve_via_calibre_prefix(author_id)

        logger.warning(
            "Author metadata ID not found and author_id is not calibre-* format: %s, author_data keys: %s",
            author_id,
            list(author_data.keys()) if author_data else None,
        )
        error_msg = "Author metadata ID not found"
        raise ValueError(error_msg)

    def get_calibre_author_dict(
        self,
        library_id: int,
        calibre_author_id: int,
    ) -> dict[str, Any]:
        """Fetch and serialize Calibre author for rematch.

        Parameters
        ----------
        library_id : int
            Library identifier.
        calibre_author_id : int
            Calibre author identifier.

        Returns
        -------
        dict[str, Any]
            Serialized Calibre author as dictionary.

        Raises
        ------
        ValueError
            If library or author cannot be found.
        """
        library = self._library_repo.get(library_id)
        if not library or not library.calibre_db_path:
            error_msg = "Library or Calibre database path not found"
            raise ValueError(error_msg)

        calibre_repo = CalibreBookRepository(
            library.calibre_db_path,
            library.calibre_db_file or "metadata.db",
        )
        with calibre_repo.get_session() as calibre_session:
            stmt = select(Author).where(Author.id == calibre_author_id)
            calibre_author = calibre_session.exec(stmt).first()

            if not calibre_author:
                error_msg = "Calibre author not found"
                raise ValueError(error_msg)

            return calibre_author.model_dump()

    def enqueue_rematch_job(
        self,
        library_id: int,
        author_dict: dict[str, Any],
        openlibrary_key: str,
        author_metadata_id: int | None,
    ) -> None:
        """Enqueue a single-author rematch job via message broker.

        Parameters
        ----------
        library_id : int
            Library identifier.
        author_dict : dict[str, Any]
            Serialized author dictionary from Calibre.
        openlibrary_key : str
            OpenLibrary key to match against.
        author_metadata_id : int | None
            Optional author metadata identifier.

        Raises
        ------
        ValueError
            If message broker is not available or not a RedisBroker.
        """
        if not isinstance(self._message_broker, RedisBroker):
            error_msg = "Message broker not available"
            raise TypeError(error_msg)

        tracker = JobProgressTracker(self._message_broker)
        tracker.initialize_job(library_id, 1, None)  # 1 item, no task_id needed

        message: dict[str, Any] = {
            "library_id": library_id,
            "author": author_dict,
            "force_rematch": True,
            "openlibrary_key": openlibrary_key,
            "single_author_mode": True,
        }

        # Only include target_author_metadata_id if it exists (for matched authors)
        if author_metadata_id:
            message["target_author_metadata_id"] = author_metadata_id

        logger.debug("Publishing message to match_queue: %s", message)
        self._message_broker.publish("match_queue", message)
