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

"""Author service for business logic.

Follows SRP by focusing solely on author business operations.
Uses IOC by accepting repositories and services as dependencies.
Separates concerns: data access (repository) vs business logic (service).
"""

import contextlib
import re
from pathlib import Path

from sqlalchemy.orm import selectinload
from sqlmodel import Session, desc, select

from fundamental.models.author_metadata import (
    AuthorAlternateName,
    AuthorLink,
    AuthorMapping,
    AuthorMetadata,
    AuthorPhoto,
    AuthorRemoteId,
    AuthorUserMetadata,
    AuthorUserPhoto,
    AuthorWork,
)
from fundamental.repositories.author_repository import AuthorRepository
from fundamental.repositories.config_repository import LibraryRepository
from fundamental.services.config_service import LibraryService
from fundamental.services.library_scanning.data_sources.registry import (
    DataSourceRegistry,
)
from fundamental.services.library_scanning.matching.types import MatchResult
from fundamental.services.library_scanning.pipeline.ingest import (
    IngestStage,
    IngestStageFactory,
)
from fundamental.services.library_scanning.pipeline.ingest_components import (
    AuthorDataFetcher,
)
from fundamental.services.library_scanning.scan_factories import (
    PipelineContextFactory,
)


class AuthorService:
    """Service for author business operations.

    Handles author retrieval, serialization, and similar author logic.
    Uses repositories for data access, keeping business logic separate.
    """

    def __init__(
        self,
        session: Session,  # type: ignore[type-arg]
        author_repo: AuthorRepository | None = None,
        library_service: LibraryService | None = None,
        library_repo: LibraryRepository | None = None,
        data_directory: str = "/data",
    ) -> None:
        """Initialize author service.

        Parameters
        ----------
        session : Session
            Database session.
        author_repo : AuthorRepository | None
            Author repository. If None, creates a new instance.
        library_service : LibraryService | None
            Library service. If None, creates a new instance.
        library_repo : LibraryRepository | None
            Library repository. If None, creates a new instance.
        data_directory : str
            Data directory path for storing files (default: "/data").
        """
        self._session = session
        self._author_repo = author_repo or AuthorRepository(session)
        self._data_directory = Path(data_directory)
        self._ensure_data_directory_exists()

        if library_service is None:
            from fundamental.repositories.config_repository import LibraryRepository
            from fundamental.services.config_service import LibraryService

            lib_repo = library_repo or LibraryRepository(session)
            self._library_service = LibraryService(session, lib_repo)
        else:
            self._library_service = library_service

    def _ensure_data_directory_exists(self) -> None:
        """Ensure the data directory exists, creating it if necessary."""
        self._data_directory.mkdir(parents=True, exist_ok=True)
        (self._data_directory / "authors").mkdir(parents=True, exist_ok=True)

    def list_authors_for_active_library(
        self,
        page: int = 1,
        page_size: int = 20,
        filter_type: str | None = None,
    ) -> tuple[list[dict[str, object]], int]:
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
        tuple[list[dict[str, object]], int]
            List of author dictionaries and total count.

        Raises
        ------
        ValueError
            If no active library is found.
        """
        active_library = self._library_service.get_active_library()
        if not active_library or active_library.id is None:
            msg = "No active library found"
            raise ValueError(msg)

        if filter_type == "unmatched":
            authors, total = self._author_repo.list_unmatched_by_library(
                active_library.id,
                calibre_db_path=active_library.calibre_db_path,
                calibre_db_file=active_library.calibre_db_file,
                page=page,
                page_size=page_size,
            )
        else:
            authors, total = self._author_repo.list_by_library(
                active_library.id,
                calibre_db_path=active_library.calibre_db_path,
                calibre_db_file=active_library.calibre_db_file,
                page=page,
                page_size=page_size,
            )
        return [self._build_author_dict(author) for author in authors], total

    def get_author_by_id_or_key(
        self,
        author_id: str,
        include_similar: bool = True,
    ) -> dict[str, object]:
        """Get a single author by ID or OpenLibrary key.

        Parameters
        ----------
        author_id : str
            Author ID (numeric) or OpenLibrary key (e.g., "OL23919A").
        include_similar : bool
            Whether to include similar authors (default: True).

        Returns
        -------
        dict[str, object]
            Author data dictionary.

        Raises
        ------
        ValueError
            If author is not found or no active library exists.
        """
        active_library = self._library_service.get_active_library()
        if not active_library or active_library.id is None:
            msg = "No active library found"
            raise ValueError(msg)

        author = self._lookup_author(author_id, active_library.id)

        if not author:
            msg = f"Author not found: {author_id}"
            raise ValueError(msg)

        author_data = self._build_author_dict(author)

        # Add similar authors if requested
        if include_similar and author.id:
            similar_authors = self._get_similar_authors(
                author.id,
                active_library.id,
            )
            if similar_authors:
                author_data["similar_authors"] = similar_authors

        return author_data

    def _lookup_author(self, author_id: str, library_id: int) -> AuthorMetadata | None:
        """Lookup author by various key formats.

        Parameters
        ----------
        author_id : str
            Author identifier string.
        library_id : int
            Library identifier.

        Returns
        -------
        AuthorMetadata | None
            Author metadata object or None if not found.
        """
        # 1. Check for custom "calibre-{id}" format
        if author_id.startswith("calibre-"):
            try:
                calibre_id = int(author_id.replace("calibre-", ""))
                return self._author_repo.get_by_calibre_id_and_library(
                    calibre_id, library_id
                )
            except ValueError:
                pass

        # 2. Check for custom "local-{id}" format
        if author_id.startswith("local-"):
            try:
                metadata_id = int(author_id.replace("local-", ""))
                return self._author_repo.get_by_id_and_library(metadata_id, library_id)
            except ValueError:
                pass

        # 3. Try to parse as integer ID (standard lookup by metadata ID)
        try:
            author_metadata_id = int(author_id)
            return self._author_repo.get_by_id_and_library(
                author_metadata_id,
                library_id,
            )
        except ValueError:
            pass

        # 4. Treat as OpenLibrary key
        return self._author_repo.get_by_openlibrary_key_and_library(
            author_id,
            library_id,
        )

    def fetch_author_metadata(
        self,
        author_id: str,
    ) -> dict[str, object]:
        """Fetch and update metadata for a single author.

        Triggers the ingest stage of the pipeline for this author only.
        Fetches latest biography, metadata, subjects, etc. from OpenLibrary.

        Parameters
        ----------
        author_id : str
            Author ID (numeric) or OpenLibrary key (e.g., "OL23919A").

        Returns
        -------
        dict[str, object]
            Result dictionary with success status, message, and stats.

        Raises
        ------
        ValueError
            If author is not found, no active library exists, or fetch fails.
        """
        # Get the author to retrieve OpenLibrary key
        author_data = self.get_author_by_id_or_key(author_id)
        # The author dict uses "key" for the OpenLibrary key (matching OpenLibrary API format)
        openlibrary_key_raw = author_data.get("key")
        if not openlibrary_key_raw or not isinstance(openlibrary_key_raw, str):
            msg = "Author does not have an OpenLibrary key"
            raise ValueError(msg)
        openlibrary_key: str = openlibrary_key_raw

        # Get active library
        active_library = self._library_service.get_active_library()
        if not active_library or active_library.id is None:
            msg = "No active library found"
            raise ValueError(msg)

        # Create data source
        data_source = DataSourceRegistry.create_source("openlibrary")

        # Create pipeline context
        def noop_progress(
            _progress: float, _metadata: dict[str, object] | None = None
        ) -> None:
            """No-op progress callback."""

        library_repo = LibraryRepository(self._session)
        context_factory = PipelineContextFactory(library_repo)  # type: ignore[arg-type]
        context = context_factory.create_context(
            library_id=active_library.id,
            session=self._session,
            data_source=data_source,
            progress_callback=noop_progress,
        )

        # Fetch latest author data from OpenLibrary
        author_fetcher = AuthorDataFetcher(data_source)
        latest_author_data = author_fetcher.fetch_author(openlibrary_key)

        if not latest_author_data:
            msg = f"Could not fetch author data from OpenLibrary for key: {openlibrary_key}"
            raise ValueError(msg)

        # Create MatchResult for the author
        match_result = MatchResult(
            confidence_score=1.0,
            matched_entity=latest_author_data,
            match_method="manual_refresh",
            calibre_author_id=None,
        )

        # Create ingest stage components (configured for forced refresh - no restrictions)
        components = IngestStageFactory.create_components(
            session=self._session,
            data_source=data_source,
            max_works_per_author=None,  # No limit on works per author in forced refresh
        )
        # Create ingest stage with stale data settings set to None (always refresh)
        ingest_stage = IngestStage(
            author_fetcher=components["author_fetcher"],
            ingestion_uow=components["ingestion_uow"],
            deduplicator=components["deduplicator"],
            progress_tracker=components["progress_tracker"],
            stale_data_max_age_days=None,  # Always refresh
            stale_data_refresh_interval_days=None,  # Always refresh
        )

        # Set the match result in context
        context.match_results = [match_result]

        # Execute ingest stage
        result = ingest_stage.execute(context)

        if not result.success:
            msg = f"Ingest failed: {result.message}"
            raise ValueError(msg)

        return {
            "success": True,
            "message": result.message,
            "stats": result.stats,
        }

    def _get_similar_authors(
        self,
        author_id: int,
        library_id: int,
        limit: int = 6,
    ) -> list[dict[str, object]]:
        """Get similar authors for a given author, filtered by library.

        Optimized to batch fetch authors and filter by library in a single query.

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
        list[dict[str, object]]
            List of similar author dictionaries.
        """
        # Batch fetch similar authors with library filtering in a single query
        similar_authors = self._author_repo.get_similar_authors_in_library(
            author_id,
            library_id,
            limit=limit,
        )

        return [self._build_author_dict(author) for author in similar_authors]

    def _build_remote_ids_dict(self, author: AuthorMetadata) -> dict[str, str]:
        """Build remote IDs dictionary.

        Parameters
        ----------
        author : AuthorMetadata
            Author metadata record.

        Returns
        -------
        dict[str, str]
            Dictionary mapping identifier type to value.
        """
        return {
            remote_id.identifier_type: remote_id.identifier_value
            for remote_id in author.remote_ids
        }

    def _build_photos_list(self, author: AuthorMetadata) -> list[int]:
        """Build photos list from author photos.

        Parameters
        ----------
        author : AuthorMetadata
            Author metadata record.

        Returns
        -------
        list[int]
            List of OpenLibrary photo IDs.
        """
        return [
            photo.openlibrary_photo_id
            for photo in author.photos
            if photo.openlibrary_photo_id and photo.openlibrary_photo_id > 0
        ]

    def _build_links_list(self, author: AuthorMetadata) -> list[dict[str, str]]:
        """Build links list from author links.

        Parameters
        ----------
        author : AuthorMetadata
            Author metadata record.

        Returns
        -------
        list[dict[str, str]]
            List of link dictionaries.
        """
        return [
            {
                "title": link.title or "",
                "url": link.url,
                "type": {"key": link.link_type or "/type/link"},
            }
            for link in author.links
        ]

    def _build_subjects_list(self, author: AuthorMetadata) -> list[str]:
        """Build subjects list from author works.

        Parameters
        ----------
        author : AuthorMetadata
            Author metadata record.

        Returns
        -------
        list[str]
            Sorted list of unique subject names.
        """
        subjects_set: set[str] = set()
        for work in author.works:
            for subject in work.subjects:
                subjects_set.add(subject.subject_name)
        return sorted(subjects_set)

    def _build_bio_dict(self, biography: str | None) -> dict[str, str] | None:
        """Build bio dictionary if biography exists.

        Parameters
        ----------
        biography : str | None
            Biography text.

        Returns
        -------
        dict[str, str] | None
            Bio dictionary or None.
        """
        if not biography:
            return None
        return {"type": "/type/text", "value": biography}

    def _build_author_dict(
        self,
        author: AuthorMetadata,
    ) -> dict[str, object]:
        """Build author dictionary for response.

        Parameters
        ----------
        author : AuthorMetadata
            Author metadata record.

        Returns
        -------
        dict[str, object]
            Author data dictionary matching OpenLibrary format.
        """
        # Handle unmatched authors (transient objects without AuthorMapping)
        # Check if this is an unmatched author by checking if it has an ID
        # Unmatched authors have id=None and a _calibre_id attribute
        calibre_id = getattr(author, "_calibre_id", None)
        if author.id is None and calibre_id is not None:
            # This is an unmatched author (no AuthorMapping exists)
            return {
                "name": author.name,
                "key": f"calibre-{calibre_id}",
                "calibre_id": calibre_id,
                "is_unmatched": True,
                "location": "Local Library (Unmatched)",  # Placeholder
            }

        # Handle unmatched authors that have been persisted (matched_by="unmatched")
        # These have an ID but openlibrary_key is None
        if author.openlibrary_key is None:
            # Use Calibre ID from mapping if available, otherwise fallback to metadata ID
            key = f"local-{author.id}"

            # Try to find the associated Calibre ID via mappings
            # Ensure mappings are loaded if not present
            if not getattr(author, "mappings", None):
                author.mappings = list(
                    self._session.exec(
                        select(AuthorMapping).where(
                            AuthorMapping.author_metadata_id == author.id
                        )
                    ).all()
                )

            if getattr(author, "mappings", None):
                # Use the first mapping's calibre_author_id
                # In practice, there should be one per library
                calibre_id = author.mappings[0].calibre_author_id
                key = f"calibre-{calibre_id}"

            # Ensure relationships are loaded (even for unmatched, we might have local data later)
            self._ensure_relationships_loaded(author)

            # Load user photos if not already loaded
            if not hasattr(author, "user_photos") or author.user_photos is None:
                author.user_photos = list(
                    self._session.exec(
                        select(AuthorUserPhoto).where(
                            AuthorUserPhoto.author_metadata_id == author.id
                        )
                    ).all()
                )

            # Build component dictionaries and lists
            remote_ids = self._build_remote_ids_dict(author)
            photos = self._build_photos_list(author)
            alternate_names = [alt_name.name for alt_name in author.alternate_names]
            links = self._build_links_list(author)
            subjects = self._build_subjects_list(author)
            bio = self._build_bio_dict(author.biography)

            # Build author object matching OpenLibrary format but for local author
            author_data: dict[str, object] = {
                "name": author.name,
                "key": key,
                "calibre_id": calibre_id,
                "is_unmatched": True,
                "location": author.location or "Local Library (Unmatched)",
            }

            # Add optional fields
            self._add_optional_fields(
                author_data,
                author,
                bio,
                remote_ids,
                photos,
                alternate_names,
                links,
                subjects,
            )

            # Add user photos (if any)
            self._add_user_photos_field(author_data, author)

            return author_data

        # Ensure relationships are loaded
        self._ensure_relationships_loaded(author)

        # Load mappings to get calibre_id
        if not getattr(author, "mappings", None):
            author.mappings = list(
                self._session.exec(
                    select(AuthorMapping).where(
                        AuthorMapping.author_metadata_id == author.id
                    )
                ).all()
            )

        calibre_id = None
        if getattr(author, "mappings", None):
            calibre_id = author.mappings[0].calibre_author_id

        # Load user metadata if not already loaded
        if not hasattr(author, "user_metadata") or author.user_metadata is None:
            author.user_metadata = list(
                self._session.exec(
                    select(AuthorUserMetadata).where(
                        AuthorUserMetadata.author_metadata_id == author.id
                    )
                ).all()
            )

        # Load user photos if not already loaded
        if not hasattr(author, "user_photos") or author.user_photos is None:
            author.user_photos = list(
                self._session.exec(
                    select(AuthorUserPhoto).where(
                        AuthorUserPhoto.author_metadata_id == author.id
                    )
                ).all()
            )

        # Build component dictionaries and lists
        remote_ids = self._build_remote_ids_dict(author)
        photos = self._build_photos_list(author)
        alternate_names = [alt_name.name for alt_name in author.alternate_names]
        links = self._build_links_list(author)
        subjects = self._build_subjects_list(author)
        bio = self._build_bio_dict(author.biography)

        # Build author object matching OpenLibrary format
        author_data: dict[str, object] = {
            "name": author.name,
            "key": author.openlibrary_key,
            "calibre_id": calibre_id,
        }

        # Add optional fields
        self._add_optional_fields(
            author_data,
            author,
            bio,
            remote_ids,
            photos,
            alternate_names,
            links,
            subjects,
        )

        # Add user-defined metadata (overrides auto-populated)
        self._add_user_metadata_fields(author_data, author)

        # Add user photos (and possibly override photo_url)
        self._add_user_photos_field(author_data, author)

        return author_data

    def _add_optional_fields(
        self,
        author_data: dict[str, object],
        author: AuthorMetadata,
        bio: dict[str, str] | None,
        remote_ids: dict[str, str],
        photos: list[int],
        alternate_names: list[str],
        links: list[dict[str, str]],
        subjects: list[str],
    ) -> None:
        """Add optional fields to author data dictionary.

        Parameters
        ----------
        author_data : dict[str, object]
            Author data dictionary to update.
        author : AuthorMetadata
            Author metadata record.
        bio : dict[str, str] | None
            Bio dictionary.
        remote_ids : dict[str, str]
            Remote IDs dictionary.
        photos : list[int]
            Photos list.
        alternate_names : list[str]
            Alternate names list.
        links : list[dict[str, str]]
            Links list.
        subjects : list[str]
            Subjects list.
        """
        # Add author metadata fields
        self._add_author_metadata_fields(author_data, author)

        # Add relationship fields
        self._add_relationship_fields(
            author_data, bio, remote_ids, photos, alternate_names, links, subjects
        )

    def _add_author_metadata_fields(
        self, author_data: dict[str, object], author: AuthorMetadata
    ) -> None:
        """Add author metadata fields to dictionary.

        Parameters
        ----------
        author_data : dict[str, object]
            Author data dictionary to update.
        author : AuthorMetadata
            Author metadata record.
        """
        field_mapping = {
            "personal_name": author.personal_name,
            "fuller_name": author.fuller_name,
            "title": author.title,
            "entity_type": author.entity_type,
            "birth_date": author.birth_date,
            "death_date": author.death_date,
            "photo_url": author.photo_url,
            "location": author.location,
        }
        # Filter out None/empty values and update dictionary
        author_data.update({
            key: value for key, value in field_mapping.items() if value
        })

    def _add_relationship_fields(
        self,
        author_data: dict[str, object],
        bio: dict[str, str] | None,
        remote_ids: dict[str, str],
        photos: list[int],
        alternate_names: list[str],
        links: list[dict[str, str]],
        subjects: list[str],
    ) -> None:
        """Add relationship fields to dictionary.

        Parameters
        ----------
        author_data : dict[str, object]
            Author data dictionary to update.
        bio : dict[str, str] | None
            Bio dictionary.
        remote_ids : dict[str, str]
            Remote IDs dictionary.
        photos : list[int]
            Photos list.
        alternate_names : list[str]
            Alternate names list.
        links : list[dict[str, str]]
            Links list.
        subjects : list[str]
            Subjects list.
        """
        if bio:
            author_data["bio"] = bio
        if remote_ids:
            author_data["remote_ids"] = remote_ids
        if photos:
            author_data["photos"] = photos
        if alternate_names:
            author_data["alternate_names"] = alternate_names
        if links:
            author_data["links"] = links
        if subjects:
            author_data["genres"] = subjects

    def _add_user_metadata_fields(
        self,
        author_data: dict[str, object],
        author: AuthorMetadata,
    ) -> None:
        """Add user-defined metadata fields to dictionary.

        User-defined fields override auto-populated values.

        Parameters
        ----------
        author_data : dict[str, object]
            Author data dictionary to update.
        author : AuthorMetadata
            Author metadata record with user_metadata loaded.
        """
        if not hasattr(author, "user_metadata") or not author.user_metadata:
            return

        # Check for user-defined genres
        user_genres = next(
            (
                um.field_value
                for um in author.user_metadata
                if um.field_name == "genres" and um.is_user_defined
            ),
            None,
        )
        if user_genres and isinstance(user_genres, list):
            author_data["genres"] = user_genres

        # Check for user-defined styles
        user_styles = next(
            (
                um.field_value
                for um in author.user_metadata
                if um.field_name == "styles" and um.is_user_defined
            ),
            None,
        )
        if user_styles and isinstance(user_styles, list):
            author_data["styles"] = user_styles

        # Check for user-defined shelves
        user_shelves = next(
            (
                um.field_value
                for um in author.user_metadata
                if um.field_name == "shelves" and um.is_user_defined
            ),
            None,
        )
        if user_shelves and isinstance(user_shelves, list):
            author_data["shelves"] = user_shelves

        # Check for user-defined similar_authors
        # Note: similar_authors from relationships are added in get_author_by_id_or_key,
        # so we only override if user-defined exists
        user_similar = next(
            (
                um.field_value
                for um in author.user_metadata
                if um.field_name == "similar_authors" and um.is_user_defined
            ),
            None,
        )
        if user_similar is not None and isinstance(user_similar, list):
            # User has defined similar authors - use them
            author_data["similar_authors"] = user_similar

    def _add_user_photos_field(
        self,
        author_data: dict[str, object],
        author: AuthorMetadata,
    ) -> None:
        """Add user-uploaded photos to author data.

        Parameters
        ----------
        author_data : dict[str, object]
            Author data dictionary to update.
        author : AuthorMetadata
            Author metadata record with user_photos loaded.
        """
        if not hasattr(author, "user_photos") or not author.user_photos:
            return

        photos_payload: list[dict[str, object]] = []
        for photo in author.user_photos:
            if photo.id is None:
                continue

            photo_url = f"/api/authors/{author.id}/photos/{photo.id}"
            photos_payload.append(
                {
                    "id": photo.id,
                    "photo_url": photo_url,
                    "file_name": photo.file_name,
                    "file_path": photo.file_path,
                    "is_primary": photo.is_primary,
                    "order": photo.order,
                    "created_at": photo.created_at.isoformat(),
                },
            )

        if photos_payload:
            author_data["user_photos"] = photos_payload

        # Ensure primary user photo becomes the main photo_url if not already set
        if "photo_url" not in author_data:
            primary_photo = next(
                (up for up in author.user_photos if up.is_primary),
                None,
            )
            if primary_photo and primary_photo.id is not None:
                author_data["photo_url"] = (
                    f"/api/authors/{author.id}/photos/{primary_photo.id}"
                )

    def _ensure_relationships_loaded(
        self,
        author: AuthorMetadata,
    ) -> None:
        """Ensure all relationships are loaded for an author.

        Parameters
        ----------
        author : AuthorMetadata
            Author metadata record.
        """
        if not author.remote_ids:
            author.remote_ids = list(
                self._session.exec(
                    select(AuthorRemoteId).where(
                        AuthorRemoteId.author_metadata_id == author.id
                    )
                ).all()
            )
        if not author.photos:
            author.photos = list(
                self._session.exec(
                    select(AuthorPhoto).where(
                        AuthorPhoto.author_metadata_id == author.id
                    )
                ).all()
            )
        if not author.alternate_names:
            author.alternate_names = list(
                self._session.exec(
                    select(AuthorAlternateName).where(
                        AuthorAlternateName.author_metadata_id == author.id
                    )
                ).all()
            )
        if not author.links:
            author.links = list(
                self._session.exec(
                    select(AuthorLink).where(AuthorLink.author_metadata_id == author.id)
                ).all()
            )
        if not author.works:
            # Load works with subjects
            works = list(
                self._session.exec(
                    select(AuthorWork)
                    .where(AuthorWork.author_metadata_id == author.id)
                    .options(selectinload(AuthorWork.subjects))
                ).all()
            )
            author.works = works

    def update_author(
        self,
        author_id: str,
        update: dict[str, object],
    ) -> dict[str, object]:
        """Update author metadata and user-defined fields.

        Parameters
        ----------
        author_id : str
            Author ID (numeric) or OpenLibrary key (e.g., "OL23919A").
        update : dict[str, object]
            Update payload with fields to update.

        Returns
        -------
        dict[str, object]
            Updated author data dictionary.

        Raises
        ------
        ValueError
            If author is not found or no active library exists.
        """
        # Get active library
        active_library = self._library_service.get_active_library()
        if not active_library or active_library.id is None:
            msg = "No active library found"
            raise ValueError(msg)

        # Get author
        author = self._lookup_author(author_id, active_library.id)
        if not author or author.id is None:
            msg = f"Author not found: {author_id}"
            raise ValueError(msg)

        # Update AuthorMetadata fields
        self._update_author_metadata_fields(author, update)

        # Save user-defined metadata fields
        self._update_user_metadata_fields(author.id, update)

        # Handle photo_url update
        self._handle_photo_url_update(author_id, author, update)

        self._session.add(author)
        self._session.commit()
        self._session.refresh(author)

        # Return updated author dict
        return self._build_author_dict(author)

    def _update_author_metadata_fields(
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

    def _update_user_metadata_fields(
        self, author_id: int, update: dict[str, object]
    ) -> None:
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

    def _handle_photo_url_update(
        self, author_id: str, author: AuthorMetadata, update: dict[str, object]
    ) -> None:
        """Handle photo_url update by setting selected photo as primary.

        Parameters
        ----------
        author_id : str
            Author ID (numeric) or OpenLibrary key.
        author : AuthorMetadata
            Author metadata object.
        update : dict[str, object]
            Update payload with fields to update.
        """
        if not update.get("photo_url"):
            return

        photo_url = str(update["photo_url"])
        # Extract photo_id from URL format: /api/authors/{author_id}/photos/{photo_id}
        match = re.search(r"/photos/(\d+)$", photo_url)
        if not match:
            return

        photo_id = int(match.group(1))
        # Verify photo belongs to this author
        photo = self.get_author_photo_by_id(author_id, photo_id)
        if photo:
            # Set this photo as primary (will unset others)
            with contextlib.suppress(ValueError):
                self.set_primary_photo(author_id, photo_id)
                # Expire user_photos relationship so it reloads with updated primary status
                self._session.expire(author, ["user_photos"])

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

    def _get_user_metadata(
        self,
        author_metadata_id: int,
        field_name: str,
    ) -> list[str] | dict[str, object] | str | None:
        """Get user-defined metadata field value.

        Parameters
        ----------
        author_metadata_id : int
            Author metadata ID.
        field_name : str
            Field name to retrieve.

        Returns
        -------
        list[str] | dict[str, object] | str | None
            Field value if user-defined, None otherwise.
        """
        user_metadata = self._session.exec(
            select(AuthorUserMetadata).where(
                AuthorUserMetadata.author_metadata_id == author_metadata_id,
                AuthorUserMetadata.field_name == field_name,
                AuthorUserMetadata.is_user_defined == True,  # noqa: E712
            )
        ).first()

        if user_metadata and user_metadata.field_value is not None:
            return user_metadata.field_value
        return None

    def _get_author_photos_dir(self, author_metadata_id: int) -> Path:
        """Get directory path for author photos.

        Parameters
        ----------
        author_metadata_id : int
            Author metadata ID.

        Returns
        -------
        Path
            Path to author photos directory.
        """
        photos_dir = self._data_directory / "authors" / str(author_metadata_id)
        photos_dir.mkdir(parents=True, exist_ok=True)
        return photos_dir

    def upload_author_photo(
        self,
        author_id: str,
        file_content: bytes,
        filename: str,
        set_as_primary: bool = False,
    ) -> AuthorUserPhoto:
        """Upload and save an author photo from file.

        Parameters
        ----------
        author_id : str
            Author ID (numeric) or OpenLibrary key.
        file_content : bytes
            File content to save.
        filename : str
            Original filename.
        set_as_primary : bool
            Whether to set this photo as primary (default: False).

        Returns
        -------
        AuthorUserPhoto
            Created photo record.

        Raises
        ------
        ValueError
            If author not found or invalid file type.
        """
        # Get active library
        active_library = self._library_service.get_active_library()
        if not active_library or active_library.id is None:
            msg = "No active library found"
            raise ValueError(msg)

        # Get author
        author = self._lookup_author(author_id, active_library.id)
        if not author or author.id is None:
            msg = f"Author not found: {author_id}"
            raise ValueError(msg)

        # Validate file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
            msg = "invalid_file_type"
            raise ValueError(msg)

        # Get photos directory
        photos_dir = self._get_author_photos_dir(author.id)

        # Generate unique filename (use timestamp + hash to avoid collisions)
        from datetime import UTC, datetime
        from hashlib import sha256

        content_hash = sha256(file_content).hexdigest()[:8]
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{content_hash}{file_ext}"
        photo_path = photos_dir / safe_filename

        # Save file
        try:
            photo_path.write_bytes(file_content)
        except OSError as exc:
            msg = f"failed_to_save_file: {exc!s}"
            raise ValueError(msg) from exc

        # Get MIME type
        mime_type_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        mime_type = mime_type_map.get(file_ext, "image/jpeg")

        # If setting as primary, unset other primary photos
        if set_as_primary:
            existing_primary = self._session.exec(
                select(AuthorUserPhoto).where(
                    AuthorUserPhoto.author_metadata_id == author.id,
                    AuthorUserPhoto.is_primary == True,  # noqa: E712
                )
            ).all()
            for photo in existing_primary:
                photo.is_primary = False
                self._session.add(photo)

        # Create photo record
        relative_path = photo_path.relative_to(self._data_directory)
        user_photo = AuthorUserPhoto(
            author_metadata_id=author.id,
            file_path=str(relative_path),
            file_name=filename,
            file_size=len(file_content),
            mime_type=mime_type,
            is_primary=set_as_primary,
            order=0,
        )
        self._session.add(user_photo)
        self._session.commit()
        self._session.refresh(user_photo)

        return user_photo

    def upload_photo_from_url(
        self,
        author_id: str,
        url: str,
        set_as_primary: bool = False,
    ) -> AuthorUserPhoto:
        """Upload and save an author photo from URL.

        Parameters
        ----------
        author_id : str
            Author ID (numeric) or OpenLibrary key.
        url : str
            URL of the image to download.
        set_as_primary : bool
            Whether to set this photo as primary (default: False).

        Returns
        -------
        AuthorUserPhoto
            Created photo record.

        Raises
        ------
        ValueError
            If author not found, download fails, or invalid image.
        """
        # Download image
        import io

        import httpx
        from PIL import Image

        content_type = "image/jpeg"  # Default fallback
        try:
            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                response = client.get(url)
                response.raise_for_status()

                content_type = response.headers.get("content-type", "").lower()
                if not content_type.startswith("image/"):
                    msg = "url_not_an_image"
                    raise ValueError(msg)

                try:
                    image = Image.open(io.BytesIO(response.content))
                    image.verify()
                except Exception as exc:
                    msg = "invalid_image_format"
                    raise ValueError(msg) from exc
                else:
                    # Reopen image after verify() closes it
                    image = Image.open(io.BytesIO(response.content))
                    file_content = response.content
        except httpx.HTTPError as exc:
            msg = f"failed_to_download_image: {exc!s}"
            raise ValueError(msg) from exc

        # Determine filename from URL or content type
        # Always normalize extension based on content_type to ensure valid file type
        from urllib.parse import unquote, urlparse

        ext_map = {
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp",
        }
        # Extract base filename from URL (remove query params, fragments)
        parsed_url = urlparse(url)
        url_path = unquote(parsed_url.path)
        base_filename = Path(url_path).name or "photo"

        # Remove any existing extension and add correct one based on content_type
        base_name = Path(base_filename).stem
        ext = ext_map.get(
            content_type.split(";")[0].strip(), ".jpg"
        )  # Handle "image/jpeg; charset=utf-8"
        filename = f"{base_name}{ext}"

        # Upload using file upload method, then update source_url
        user_photo = self.upload_author_photo(
            author_id=author_id,
            file_content=file_content,
            filename=filename,
            set_as_primary=set_as_primary,
        )
        # Update source_url to track original URL
        user_photo.source_url = url
        self._session.add(user_photo)
        self._session.commit()
        self._session.refresh(user_photo)
        return user_photo

    def get_author_photos(self, author_id: str) -> list[AuthorUserPhoto]:
        """Get all user-uploaded photos for an author.

        Parameters
        ----------
        author_id : str
            Author ID (numeric) or OpenLibrary key.

        Returns
        -------
        list[AuthorUserPhoto]
            List of photo records.

        Raises
        ------
        ValueError
            If author not found.
        """
        # Get active library
        active_library = self._library_service.get_active_library()
        if not active_library or active_library.id is None:
            msg = "No active library found"
            raise ValueError(msg)

        # Get author
        author = self._lookup_author(author_id, active_library.id)
        if not author or author.id is None:
            msg = f"Author not found: {author_id}"
            raise ValueError(msg)

        photos = self._session.exec(
            select(AuthorUserPhoto)
            .where(AuthorUserPhoto.author_metadata_id == author.id)
            .order_by(
                desc(AuthorUserPhoto.is_primary),
                AuthorUserPhoto.order,
                AuthorUserPhoto.created_at,
            )
        ).all()

        return list(photos)

    def get_author_photo_by_id(
        self, author_id: str, photo_id: int
    ) -> AuthorUserPhoto | None:
        """Get a specific photo by ID for an author.

        Parameters
        ----------
        author_id : str
            Author ID (numeric) or OpenLibrary key.
        photo_id : int
            Photo ID to retrieve.

        Returns
        -------
        AuthorUserPhoto | None
            Photo record if found and belongs to author, None otherwise.
        """
        # Get active library
        active_library = self._library_service.get_active_library()
        if not active_library or active_library.id is None:
            return None

        # Get author
        author = self._lookup_author(author_id, active_library.id)
        if not author or author.id is None:
            return None

        # Get photo and verify it belongs to author
        return self._session.exec(
            select(AuthorUserPhoto).where(
                AuthorUserPhoto.id == photo_id,
                AuthorUserPhoto.author_metadata_id == author.id,
            )
        ).first()

    def set_primary_photo(self, author_id: str, photo_id: int) -> AuthorUserPhoto:
        """Set a photo as the primary photo for an author.

        Parameters
        ----------
        author_id : str
            Author ID (numeric) or OpenLibrary key.
        photo_id : int
            Photo ID to set as primary.

        Returns
        -------
        AuthorUserPhoto
            Updated photo record.

        Raises
        ------
        ValueError
            If author or photo not found.
        """
        # Get active library
        active_library = self._library_service.get_active_library()
        if not active_library or active_library.id is None:
            msg = "No active library found"
            raise ValueError(msg)

        # Get author
        author = self._lookup_author(author_id, active_library.id)
        if not author or author.id is None:
            msg = f"Author not found: {author_id}"
            raise ValueError(msg)

        # Get photo
        photo = self._session.exec(
            select(AuthorUserPhoto).where(
                AuthorUserPhoto.id == photo_id,
                AuthorUserPhoto.author_metadata_id == author.id,
            )
        ).first()

        if not photo:
            msg = f"Photo not found: {photo_id}"
            raise ValueError(msg)

        # Unset other primary photos
        existing_primary = self._session.exec(
            select(AuthorUserPhoto).where(
                AuthorUserPhoto.author_metadata_id == author.id,
                AuthorUserPhoto.is_primary == True,  # noqa: E712
                AuthorUserPhoto.id != photo_id,
            )
        ).all()
        for existing in existing_primary:
            existing.is_primary = False
            self._session.add(existing)

        # Set this photo as primary
        photo.is_primary = True
        self._session.add(photo)
        self._session.commit()
        self._session.refresh(photo)

        return photo

    def delete_photo(self, author_id: str, photo_id: int) -> None:
        """Delete an author photo and its file.

        Parameters
        ----------
        author_id : str
            Author ID (numeric) or OpenLibrary key.
        photo_id : int
            Photo ID to delete.

        Raises
        ------
        ValueError
            If author or photo not found.
        """
        # Get active library
        active_library = self._library_service.get_active_library()
        if not active_library or active_library.id is None:
            msg = "No active library found"
            raise ValueError(msg)

        # Get author
        author = self._lookup_author(author_id, active_library.id)
        if not author or author.id is None:
            msg = f"Author not found: {author_id}"
            raise ValueError(msg)

        # Get photo
        photo = self._session.exec(
            select(AuthorUserPhoto).where(
                AuthorUserPhoto.id == photo_id,
                AuthorUserPhoto.author_metadata_id == author.id,
            )
        ).first()

        if not photo:
            msg = f"Photo not found: {photo_id}"
            raise ValueError(msg)

        # Store file path before deletion
        photo_path = self._data_directory / photo.file_path

        # Delete record first (atomic DB operation)
        self._session.delete(photo)
        self._session.commit()

        # Delete file after successful DB deletion (best effort)
        if photo_path.exists():
            from contextlib import suppress

            with suppress(OSError):
                photo_path.unlink()
