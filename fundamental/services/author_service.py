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

from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from fundamental.models.author_metadata import (
    AuthorAlternateName,
    AuthorLink,
    AuthorMetadata,
    AuthorPhoto,
    AuthorRemoteId,
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
        """
        self._session = session
        self._author_repo = author_repo or AuthorRepository(session)

        if library_service is None:
            from fundamental.repositories.config_repository import LibraryRepository
            from fundamental.services.config_service import LibraryService

            lib_repo = library_repo or LibraryRepository(session)
            self._library_service = LibraryService(session, lib_repo)
        else:
            self._library_service = library_service

    def list_authors_for_active_library(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict[str, object]], int]:
        """List authors for the active library with pagination.

        Parameters
        ----------
        page : int
            Page number (1-indexed, default: 1).
        page_size : int
            Number of items per page (default: 20).

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

        # Try to parse as integer ID first, otherwise treat as OpenLibrary key
        try:
            author_metadata_id = int(author_id)
            author = self._author_repo.get_by_id_and_library(
                author_metadata_id,
                active_library.id,
            )
        except ValueError:
            # Treat as OpenLibrary key
            author = self._author_repo.get_by_openlibrary_key_and_library(
                author_id,
                active_library.id,
            )

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
        similar_author_ids = self._author_repo.get_similar_author_ids(
            author_id,
            limit=limit,
        )

        similar_authors: list[dict[str, object]] = []
        for similar_author_id in similar_author_ids:
            # Check if this similar author is in the active library
            if not self._author_repo.is_author_in_library(
                similar_author_id,
                library_id,
            ):
                continue

            # Fetch the similar author
            similar_author = self._author_repo.get_by_id(similar_author_id)
            if similar_author:
                similar_authors.append(self._build_author_dict(similar_author))

        return similar_authors

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
                "is_unmatched": True,
                "location": "Local Library (Unmatched)",  # Placeholder
            }

        # Ensure relationships are loaded
        self._ensure_relationships_loaded(author)

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
