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

"""Components for the ingest stage pipeline.

Separates concerns following SOLID principles:
- Data fetching (AuthorDataFetcher)
- URL building (PhotoUrlBuilder)
- Repositories (data access)
- Services (business logic)
- Strategies (subject fetching)
- Deduplication
- Progress tracking
"""

import logging
from abc import ABC, abstractmethod
from collections.abc import Sequence
from contextlib import suppress
from datetime import UTC, datetime

from sqlmodel import Session, select

from fundamental.models.author_metadata import (
    AuthorAlternateName,
    AuthorLink,
    AuthorMetadata,
    AuthorPhoto,
    AuthorRemoteId,
    AuthorWork,
    WorkSubject,
)
from fundamental.services.library_scanning.data_sources.base import (
    BaseDataSource,
    DataSourceError,
    DataSourceNetworkError,
    DataSourceNotFoundError,
    DataSourceRateLimitError,
)
from fundamental.services.library_scanning.data_sources.types import (
    AuthorData,
    BookData,
)
from fundamental.services.library_scanning.matching.types import MatchResult

logger = logging.getLogger(__name__)

# OpenLibrary covers base URL
OPENLIBRARY_COVERS_BASE = "https://covers.openlibrary.org"


# ============================================================================
# Data Fetching Components
# ============================================================================


class AuthorDataFetcher:
    """Handles fetching author and work data from external sources.

    Encapsulates data source interactions with proper error handling.
    """

    def __init__(self, data_source: BaseDataSource) -> None:
        """Initialize author data fetcher.

        Parameters
        ----------
        data_source : BaseDataSource
            External data source for fetching author data.
        """
        self.data_source = data_source

    def fetch_author(self, author_key: str) -> AuthorData | None:
        """Fetch author data with error handling.

        Parameters
        ----------
        author_key : str
            Author key identifier.

        Returns
        -------
        AuthorData | None
            Author data if found, None otherwise.

        Raises
        ------
        DataSourceNetworkError
            If network request fails.
        DataSourceRateLimitError
            If rate limit is exceeded.
        """
        try:
            return self.data_source.get_author(author_key)
        except (DataSourceNetworkError, DataSourceRateLimitError) as e:
            logger.warning("Network error fetching author %s: %s", author_key, e)
            raise
        except DataSourceNotFoundError:
            logger.warning("Author not found: %s", author_key)
            return None

    def fetch_author_works(
        self, author_key: str, limit: int | None = None
    ) -> Sequence[str]:
        """Fetch work keys for an author.

        Parameters
        ----------
        author_key : str
            Author key identifier.
        limit : int | None
            Maximum number of work keys to return (None = fetch all).

        Returns
        -------
        Sequence[str]
            Sequence of work keys.
        """
        get_author_works = getattr(self.data_source, "get_author_works", None)
        if get_author_works and callable(get_author_works):
            return get_author_works(author_key, limit=limit)
        return []

    def fetch_work(self, work_key: str) -> BookData | None:
        """Fetch work data with subjects.

        Parameters
        ----------
        work_key : str
            Work key identifier.

        Returns
        -------
        BookData | None
            Book data if found, None otherwise.
        """
        try:
            return self.data_source.get_book(work_key, skip_authors=True)
        except DataSourceError as e:
            logger.warning("Error fetching work %s: %s", work_key, e)
            return None


# ============================================================================
# Photo URL Building
# ============================================================================


class PhotoUrlBuilder:
    """Builds photo URLs from photo IDs."""

    def __init__(self, base_url: str = OPENLIBRARY_COVERS_BASE) -> None:
        """Initialize photo URL builder.

        Parameters
        ----------
        base_url : str
            Base URL for photo service (default: OpenLibrary covers).
        """
        self.base_url = base_url

    def build_url(self, photo_id: int, size: str = "L") -> str:
        """Build photo URL from ID.

        Parameters
        ----------
        photo_id : int
            Photo ID from external source.
        size : str
            Photo size suffix (default: "L" for large).

        Returns
        -------
        str
            Complete photo URL.
        """
        return f"{self.base_url}/a/id/{photo_id}-{size}.jpg"


# ============================================================================
# Repository Interfaces and Implementations
# ============================================================================


class AuthorMetadataRepository:
    """Repository for AuthorMetadata operations."""

    def __init__(self, session: Session) -> None:
        """Initialize repository.

        Parameters
        ----------
        session : Session
            Database session.
        """
        self.session = session

    def find_by_openlibrary_key(self, key: str) -> AuthorMetadata | None:
        """Find author metadata by OpenLibrary key.

        Parameters
        ----------
        key : str
            OpenLibrary author key.

        Returns
        -------
        AuthorMetadata | None
            Author metadata if found, None otherwise.
        """
        stmt = select(AuthorMetadata).where(AuthorMetadata.openlibrary_key == key)
        return self.session.exec(stmt).first()

    def create(
        self, author_data: AuthorData, photo_url: str | None = None
    ) -> AuthorMetadata:
        """Create new author metadata record.

        Parameters
        ----------
        author_data : AuthorData
            Author data from external source.
        photo_url : str | None
            Primary photo URL if available.

        Returns
        -------
        AuthorMetadata
            Created author metadata record.
        """
        author = AuthorMetadata(
            openlibrary_key=author_data.key,
            name=author_data.name,
            personal_name=author_data.personal_name,
            fuller_name=author_data.fuller_name,
            title=author_data.title,
            birth_date=author_data.birth_date,
            death_date=author_data.death_date,
            entity_type=author_data.entity_type,
            biography=author_data.biography,
            location=author_data.location,
            photo_url=photo_url,
            work_count=author_data.work_count,
            ratings_average=author_data.ratings_average,
            ratings_count=author_data.ratings_count,
            top_work=author_data.top_work,
            last_synced_at=datetime.now(UTC),
        )
        self.session.add(author)
        self.session.flush()
        return author

    def update(
        self,
        existing: AuthorMetadata,
        author_data: AuthorData,
        photo_url: str | None = None,
    ) -> AuthorMetadata:
        """Update existing author metadata record.

        Parameters
        ----------
        existing : AuthorMetadata
            Existing author metadata record.
        author_data : AuthorData
            Updated author data.
        photo_url : str | None
            Primary photo URL if available.

        Returns
        -------
        AuthorMetadata
            Updated author metadata record.
        """
        existing.name = author_data.name
        existing.personal_name = author_data.personal_name
        existing.fuller_name = author_data.fuller_name
        existing.title = author_data.title
        existing.birth_date = author_data.birth_date
        existing.death_date = author_data.death_date
        existing.entity_type = author_data.entity_type
        existing.biography = author_data.biography
        existing.location = author_data.location
        existing.work_count = author_data.work_count
        existing.ratings_average = author_data.ratings_average
        existing.ratings_count = author_data.ratings_count
        existing.top_work = author_data.top_work
        existing.last_synced_at = datetime.now(UTC)
        existing.updated_at = datetime.now(UTC)
        if photo_url:
            existing.photo_url = photo_url
        return existing


class AuthorPhotoRepository:
    """Repository for AuthorPhoto operations."""

    def __init__(self, session: Session) -> None:
        """Initialize repository.

        Parameters
        ----------
        session : Session
            Database session.
        """
        self.session = session

    def exists(self, author_id: int, photo_id: int) -> bool:
        """Check if photo exists for author.

        Parameters
        ----------
        author_id : int
            Author metadata ID.
        photo_id : int
            OpenLibrary photo ID.

        Returns
        -------
        bool
            True if photo exists, False otherwise.
        """
        stmt = select(AuthorPhoto).where(
            AuthorPhoto.author_metadata_id == author_id,
            AuthorPhoto.openlibrary_photo_id == photo_id,
        )
        return self.session.exec(stmt).first() is not None

    def create(self, photo: AuthorPhoto) -> AuthorPhoto:
        """Create new photo record.

        Parameters
        ----------
        photo : AuthorPhoto
            Photo record to create.

        Returns
        -------
        AuthorPhoto
            Created photo record.
        """
        self.session.add(photo)
        return photo


class AuthorRemoteIdRepository:
    """Repository for AuthorRemoteId operations."""

    def __init__(self, session: Session) -> None:
        """Initialize repository.

        Parameters
        ----------
        session : Session
            Database session.
        """
        self.session = session

    def find_by_type(
        self, author_id: int, identifier_type: str
    ) -> AuthorRemoteId | None:
        """Find remote ID by type.

        Parameters
        ----------
        author_id : int
            Author metadata ID.
        identifier_type : str
            Identifier type (e.g., "viaf", "goodreads").

        Returns
        -------
        AuthorRemoteId | None
            Remote ID if found, None otherwise.
        """
        stmt = select(AuthorRemoteId).where(
            AuthorRemoteId.author_metadata_id == author_id,
            AuthorRemoteId.identifier_type == identifier_type,
        )
        return self.session.exec(stmt).first()

    def create(self, remote_id: AuthorRemoteId) -> AuthorRemoteId:
        """Create new remote ID record.

        Parameters
        ----------
        remote_id : AuthorRemoteId
            Remote ID record to create.

        Returns
        -------
        AuthorRemoteId
            Created remote ID record.
        """
        self.session.add(remote_id)
        return remote_id

    def update(self, existing: AuthorRemoteId, identifier_value: str) -> AuthorRemoteId:
        """Update existing remote ID.

        Parameters
        ----------
        existing : AuthorRemoteId
            Existing remote ID record.
        identifier_value : str
            New identifier value.

        Returns
        -------
        AuthorRemoteId
            Updated remote ID record.
        """
        existing.identifier_value = identifier_value
        return existing


class AuthorAlternateNameRepository:
    """Repository for AuthorAlternateName operations."""

    def __init__(self, session: Session) -> None:
        """Initialize repository.

        Parameters
        ----------
        session : Session
            Database session.
        """
        self.session = session

    def exists(self, author_id: int, name: str) -> bool:
        """Check if alternate name exists.

        Parameters
        ----------
        author_id : int
            Author metadata ID.
        name : str
            Alternate name.

        Returns
        -------
        bool
            True if name exists, False otherwise.
        """
        stmt = select(AuthorAlternateName).where(
            AuthorAlternateName.author_metadata_id == author_id,
            AuthorAlternateName.name == name,
        )
        return self.session.exec(stmt).first() is not None

    def create(self, alt_name: AuthorAlternateName) -> AuthorAlternateName:
        """Create new alternate name record.

        Parameters
        ----------
        alt_name : AuthorAlternateName
            Alternate name record to create.

        Returns
        -------
        AuthorAlternateName
            Created alternate name record.
        """
        self.session.add(alt_name)
        return alt_name


class AuthorLinkRepository:
    """Repository for AuthorLink operations."""

    def __init__(self, session: Session) -> None:
        """Initialize repository.

        Parameters
        ----------
        session : Session
            Database session.
        """
        self.session = session

    def exists_by_url(self, author_id: int, url: str) -> bool:
        """Check if link exists by URL.

        Parameters
        ----------
        author_id : int
            Author metadata ID.
        url : str
            Link URL.

        Returns
        -------
        bool
            True if link exists, False otherwise.
        """
        stmt = select(AuthorLink).where(
            AuthorLink.author_metadata_id == author_id,
            AuthorLink.url == url,
        )
        return self.session.exec(stmt).first() is not None

    def create(self, link: AuthorLink) -> AuthorLink:
        """Create new link record.

        Parameters
        ----------
        link : AuthorLink
            Link record to create.

        Returns
        -------
        AuthorLink
            Created link record.
        """
        self.session.add(link)
        return link


class AuthorWorkRepository:
    """Repository for AuthorWork operations."""

    def __init__(self, session: Session) -> None:
        """Initialize repository.

        Parameters
        ----------
        session : Session
            Database session.
        """
        self.session = session

    def find_by_author_id(self, author_id: int) -> Sequence[AuthorWork]:
        """Find all works for an author.

        Parameters
        ----------
        author_id : int
            Author metadata ID.

        Returns
        -------
        Sequence[AuthorWork]
            Sequence of author work records.
        """
        stmt = select(AuthorWork).where(AuthorWork.author_metadata_id == author_id)
        return self.session.exec(stmt).all()

    def find_by_work_key(self, work_key: str) -> AuthorWork | None:
        """Find work by work key.

        Parameters
        ----------
        work_key : str
            OpenLibrary work key.

        Returns
        -------
        AuthorWork | None
            Work record if found, None otherwise.
        """
        stmt = select(AuthorWork).where(AuthorWork.work_key == work_key)
        return self.session.exec(stmt).first()

    def create(self, work: AuthorWork) -> AuthorWork:
        """Create new work record.

        Parameters
        ----------
        work : AuthorWork
            Work record to create.

        Returns
        -------
        AuthorWork
            Created work record.
        """
        self.session.add(work)
        return work


class WorkSubjectRepository:
    """Repository for WorkSubject operations."""

    def __init__(self, session: Session) -> None:
        """Initialize repository.

        Parameters
        ----------
        session : Session
            Database session.
        """
        self.session = session

    def exists(self, work_id: int, subject_name: str) -> bool:
        """Check if subject exists for work.

        Parameters
        ----------
        work_id : int
            Author work ID.
        subject_name : str
            Subject name.

        Returns
        -------
        bool
            True if subject exists, False otherwise.
        """
        stmt = select(WorkSubject).where(
            WorkSubject.author_work_id == work_id,
            WorkSubject.subject_name == subject_name,
        )
        return self.session.exec(stmt).first() is not None

    def create(self, subject: WorkSubject) -> WorkSubject:
        """Create new subject record.

        Parameters
        ----------
        subject : WorkSubject
            Subject record to create.

        Returns
        -------
        WorkSubject
            Created subject record.
        """
        self.session.add(subject)
        return subject


# ============================================================================
# Service Layer
# ============================================================================


class AuthorPhotoService:
    """Service for managing author photos."""

    def __init__(
        self,
        photo_repo: AuthorPhotoRepository,
        url_builder: PhotoUrlBuilder,
    ) -> None:
        """Initialize photo service.

        Parameters
        ----------
        photo_repo : AuthorPhotoRepository
            Photo repository.
        url_builder : PhotoUrlBuilder
            Photo URL builder.
        """
        self.photo_repo = photo_repo
        self.url_builder = url_builder

    def update_photos(self, author_id: int, photo_ids: Sequence[int]) -> None:
        """Update author photos.

        Parameters
        ----------
        author_id : int
            Author metadata ID.
        photo_ids : Sequence[int]
            Sequence of photo IDs.
        """
        for idx, photo_id in enumerate(photo_ids):
            if not self.photo_repo.exists(author_id, photo_id):
                photo = AuthorPhoto(
                    author_metadata_id=author_id,
                    openlibrary_photo_id=photo_id,
                    photo_url=self.url_builder.build_url(photo_id),
                    is_primary=(idx == 0),
                    order=idx,
                )
                self.photo_repo.create(photo)


class RemoteIdService:
    """Service for managing remote identifiers."""

    def __init__(self, remote_id_repo: AuthorRemoteIdRepository) -> None:
        """Initialize remote ID service.

        Parameters
        ----------
        remote_id_repo : AuthorRemoteIdRepository
            Remote ID repository.
        """
        self.remote_id_repo = remote_id_repo

    def update_identifiers(
        self, author_id: int, identifiers_dict: dict[str, str]
    ) -> None:
        """Update remote identifiers for author.

        Parameters
        ----------
        author_id : int
            Author metadata ID.
        identifiers_dict : dict[str, str]
            Dictionary mapping identifier type to value.
        """
        for id_type, id_value in identifiers_dict.items():
            existing = self.remote_id_repo.find_by_type(author_id, id_type)
            if existing:
                self.remote_id_repo.update(existing, id_value)
            else:
                remote_id = AuthorRemoteId(
                    author_metadata_id=author_id,
                    identifier_type=id_type,
                    identifier_value=id_value,
                )
                self.remote_id_repo.create(remote_id)


class AlternateNameService:
    """Service for managing alternate names."""

    def __init__(self, alt_name_repo: AuthorAlternateNameRepository) -> None:
        """Initialize alternate name service.

        Parameters
        ----------
        alt_name_repo : AuthorAlternateNameRepository
            Alternate name repository.
        """
        self.alt_name_repo = alt_name_repo

    def update_names(self, author_id: int, alternate_names: Sequence[str]) -> None:
        """Update alternate names for author.

        Parameters
        ----------
        author_id : int
            Author metadata ID.
        alternate_names : Sequence[str]
            Sequence of alternate names.
        """
        for alt_name in alternate_names:
            if not self.alt_name_repo.exists(author_id, alt_name):
                alt = AuthorAlternateName(
                    author_metadata_id=author_id,
                    name=alt_name,
                )
                self.alt_name_repo.create(alt)


class AuthorLinkService:
    """Service for managing author links."""

    def __init__(self, link_repo: AuthorLinkRepository) -> None:
        """Initialize link service.

        Parameters
        ----------
        link_repo : AuthorLinkRepository
            Link repository.
        """
        self.link_repo = link_repo

    def update_links(self, author_id: int, links: Sequence[dict[str, str]]) -> None:
        """Update links for author.

        Parameters
        ----------
        author_id : int
            Author metadata ID.
        links : Sequence[dict[str, str]]
            Sequence of link dictionaries.
        """
        for link_data in links:
            url = link_data.get("url", "")
            if url and not self.link_repo.exists_by_url(author_id, url):
                link = AuthorLink(
                    author_metadata_id=author_id,
                    title=link_data.get("title", ""),
                    url=url,
                    link_type=link_data.get("type"),
                )
                self.link_repo.create(link)


class AuthorMetadataService:
    """Service for managing author metadata and related entities."""

    def __init__(
        self,
        metadata_repo: AuthorMetadataRepository,
        photo_service: AuthorPhotoService,
        remote_id_service: RemoteIdService,
        alternate_name_service: AlternateNameService,
        link_service: AuthorLinkService,
        url_builder: PhotoUrlBuilder,
    ) -> None:
        """Initialize author metadata service.

        Parameters
        ----------
        metadata_repo : AuthorMetadataRepository
            Author metadata repository.
        photo_service : AuthorPhotoService
            Photo service.
        remote_id_service : RemoteIdService
            Remote ID service.
        alternate_name_service : AlternateNameService
            Alternate name service.
        link_service : AuthorLinkService
            Link service.
        url_builder : PhotoUrlBuilder
            Photo URL builder.
        """
        self.metadata_repo = metadata_repo
        self.photo_service = photo_service
        self.remote_id_service = remote_id_service
        self.alternate_name_service = alternate_name_service
        self.link_service = link_service
        self.url_builder = url_builder

    def upsert_author(self, author_data: AuthorData) -> AuthorMetadata:
        """Create or update author with all related data.

        Parameters
        ----------
        author_data : AuthorData
            Author data from external source.

        Returns
        -------
        AuthorMetadata
            Created or updated author metadata record.
        """
        existing = self.metadata_repo.find_by_openlibrary_key(author_data.key)

        # Build primary photo URL
        photo_url = None
        if author_data.photo_ids:
            primary_photo_id = author_data.photo_ids[0]
            photo_url = self.url_builder.build_url(primary_photo_id)

        if existing:
            logger.info(
                "Updating existing author metadata for %s (key: %s)",
                author_data.name,
                author_data.key,
            )
            author = self.metadata_repo.update(existing, author_data, photo_url)
        else:
            logger.info(
                "Creating new author metadata for %s (key: %s)",
                author_data.name,
                author_data.key,
            )
            author = self.metadata_repo.create(author_data, photo_url)

        # Delegate to specialized services
        # Note: author.id is guaranteed to be set after create/update due to flush()
        if not author.id:
            msg = "Author ID is None after create/update"
            raise RuntimeError(msg)

        if author_data.photo_ids:
            self.photo_service.update_photos(author.id, author_data.photo_ids)

        if author_data.identifiers:
            self.remote_id_service.update_identifiers(
                author.id,
                author_data.identifiers.to_dict(),
            )

        if author_data.alternate_names:
            self.alternate_name_service.update_names(
                author.id,
                author_data.alternate_names,
            )

        if author_data.links:
            self.link_service.update_links(author.id, author_data.links)

        return author


class AuthorWorkService:
    """Service for managing author works."""

    def __init__(
        self,
        work_repo: AuthorWorkRepository,
        subject_repo: WorkSubjectRepository,
    ) -> None:
        """Initialize work service.

        Parameters
        ----------
        work_repo : AuthorWorkRepository
            Work repository.
        subject_repo : WorkSubjectRepository
            Subject repository.
        """
        self.work_repo = work_repo
        self.subject_repo = subject_repo

    def persist_works(self, author_id: int, work_keys: Sequence[str]) -> int:
        """Persist work keys to database.

        Parameters
        ----------
        author_id : int
            Author metadata ID.
        work_keys : Sequence[str]
            Sequence of OpenLibrary work keys.

        Returns
        -------
        int
            Number of new works persisted.
        """
        if not work_keys:
            return 0

        # Get existing work keys
        existing_works = {
            work.work_key for work in self.work_repo.find_by_author_id(author_id)
        }

        # Add new work keys
        new_works_count = 0
        for rank, work_key in enumerate(work_keys):
            if work_key not in existing_works:
                work = AuthorWork(
                    author_metadata_id=author_id,
                    work_key=work_key,
                    rank=rank,
                )
                self.work_repo.create(work)
                new_works_count += 1

        if new_works_count > 0:
            logger.info(
                "Persisted %d new work keys for author %d (total: %d works)",
                new_works_count,
                author_id,
                len(work_keys),
            )

        return new_works_count

    def persist_work_subjects(self, work: AuthorWork, subjects: Sequence[str]) -> int:
        """Persist subjects for a work.

        Parameters
        ----------
        work : AuthorWork
            Work record.
        subjects : Sequence[str]
            Sequence of subject names.

        Returns
        -------
        int
            Number of new subjects persisted.
        """
        if not subjects or not work.id:
            return 0

        new_subjects_count = 0
        for rank, subject_name in enumerate(subjects):
            if not self.subject_repo.exists(work.id, subject_name):
                subject = WorkSubject(
                    author_work_id=work.id,
                    subject_name=subject_name,
                    rank=rank,
                )
                self.subject_repo.create(subject)
                new_subjects_count += 1

        if new_subjects_count > 0:
            logger.debug(
                "Persisted %d new subjects for work %s (total: %d subjects)",
                new_subjects_count,
                work.work_key,
                len(subjects),
            )

        return new_subjects_count


# ============================================================================
# Strategy Pattern for Subject Fetching
# ============================================================================


class SubjectFetchStrategy(ABC):
    """Abstract strategy for fetching subjects."""

    @abstractmethod
    def fetch_subjects(
        self,
        author_key: str,
        author_metadata: AuthorMetadata | None = None,
    ) -> list[str]:
        """Fetch subjects for an author.

        Parameters
        ----------
        author_key : str
            Author key identifier.
        author_metadata : AuthorMetadata | None
            Optional author metadata for strategies that need it.

        Returns
        -------
        list[str]
            List of subject names.
        """
        raise NotImplementedError


class DirectAuthorSubjectStrategy(SubjectFetchStrategy):
    """Fetch subjects directly from author data."""

    def __init__(self, data_fetcher: AuthorDataFetcher) -> None:
        """Initialize strategy.

        Parameters
        ----------
        data_fetcher : AuthorDataFetcher
            Author data fetcher.
        """
        self.data_fetcher = data_fetcher

    def fetch_subjects(self, author_key: str) -> list[str]:
        """Fetch subjects from author data.

        Parameters
        ----------
        author_key : str
            Author key identifier.

        Returns
        -------
        list[str]
            List of subject names.
        """
        author_data = self.data_fetcher.fetch_author(author_key)
        return (
            list(author_data.subjects) if author_data and author_data.subjects else []
        )


class WorkBasedSubjectStrategy(SubjectFetchStrategy):
    """Fetch subjects from author's works."""

    def __init__(
        self,
        data_fetcher: AuthorDataFetcher,
        work_service: AuthorWorkService,
        work_repo: AuthorWorkRepository,
        subject_repo: WorkSubjectRepository,
        max_works_per_author: int | None = None,
    ) -> None:
        """Initialize strategy.

        Parameters
        ----------
        data_fetcher : AuthorDataFetcher
            Author data fetcher.
        work_service : AuthorWorkService
            Work service for persisting works.
        work_repo : AuthorWorkRepository
            Work repository.
        subject_repo : WorkSubjectRepository
            Subject repository.
        max_works_per_author : int | None
            Maximum number of work keys to fetch per author (None = no limit).
            Also limits how many works to fetch metadata for to extract subjects.
        """
        self.data_fetcher = data_fetcher
        self.work_service = work_service
        self.work_repo = work_repo
        self.subject_repo = subject_repo
        self.max_works_per_author = max_works_per_author

    def fetch_subjects(
        self,
        author_key: str,
        author_metadata: AuthorMetadata | None = None,
    ) -> list[str]:
        """Fetch subjects from author's works.

        Parameters
        ----------
        author_key : str
            Author key identifier.
        author_metadata : AuthorMetadata | None
            Optional author metadata for persisting works.

        Returns
        -------
        list[str]
            List of unique subject names from works.
        """
        subjects: set[str] = set()

        with suppress(
            DataSourceNetworkError,
            DataSourceRateLimitError,
            DataSourceNotFoundError,
            DataSourceError,
        ):
            # Fetch work keys with a reasonable maximum limit to prevent excessive pagination
            # for prolific authors (e.g., Cervantes has 3000+ works)
            # We only need a small subset for subjects, but persist more for completeness
            max_works_to_fetch = self.max_works_per_author
            work_keys = self.data_fetcher.fetch_author_works(
                author_key, limit=max_works_to_fetch
            )
            logger.info(
                "Fetched %d work keys for author %s", len(work_keys), author_key
            )

            # Persist work keys if author metadata is provided
            if author_metadata and author_metadata.id:
                self.work_service.persist_works(author_metadata.id, work_keys)

            # Use all fetched work keys for metadata fetching (already limited by max_works_per_author)
            works_to_fetch = work_keys

            # Fetch each work and extract subjects
            for idx, work_key in enumerate(works_to_fetch, start=1):
                work_data = self.data_fetcher.fetch_work(work_key)
                if work_data and work_data.subjects:
                    subjects.update(work_data.subjects)

                    # Persist subjects to the work if work exists in DB
                    work = self.work_repo.find_by_work_key(work_key)
                    if work and work.id:
                        self.work_service.persist_work_subjects(
                            work, work_data.subjects
                        )

                    logger.info(
                        "Fetched work %s for author %s (%d/%d, %d unique subjects)",
                        work_key,
                        author_key,
                        idx,
                        len(works_to_fetch),
                        len(subjects),
                    )

        return list(subjects)


class HybridSubjectStrategy(SubjectFetchStrategy):
    """Try direct first, fall back to works."""

    def __init__(
        self,
        direct_strategy: SubjectFetchStrategy,
        work_strategy: SubjectFetchStrategy,
    ) -> None:
        """Initialize strategy.

        Parameters
        ----------
        direct_strategy : SubjectFetchStrategy
            Strategy for direct author subject fetching.
        work_strategy : SubjectFetchStrategy
            Strategy for work-based subject fetching.
        """
        self.direct_strategy = direct_strategy
        self.work_strategy = work_strategy

    def fetch_subjects(
        self,
        author_key: str,
        author_metadata: AuthorMetadata | None = None,
    ) -> list[str]:
        """Fetch subjects using hybrid approach.

        Parameters
        ----------
        author_key : str
            Author key identifier.
        author_metadata : AuthorMetadata | None
            Optional author metadata for work-based strategy.

        Returns
        -------
        list[str]
            List of subject names.
        """
        subjects = self.direct_strategy.fetch_subjects(author_key)
        if not subjects:
            logger.debug("No direct subjects for %s, fetching from works", author_key)
            # Check if work strategy supports author_metadata parameter
            if hasattr(self.work_strategy, "fetch_subjects"):
                work_subjects = self.work_strategy.fetch_subjects(
                    author_key, author_metadata
                )
                subjects = work_subjects
        return subjects


# ============================================================================
# Deduplication
# ============================================================================


class MatchResultDeduplicator:
    """Handle deduplication of match results."""

    def deduplicate_by_key(
        self, match_results: Sequence[MatchResult]
    ) -> tuple[list[MatchResult], int]:
        """Remove duplicate author keys from match results.

        Parameters
        ----------
        match_results : Sequence[MatchResult]
            Sequence of match results.

        Returns
        -------
        tuple[list[MatchResult], int]
            Tuple of (unique_results, duplicate_count).
        """
        seen_keys: set[str] = set()
        unique_results: list[MatchResult] = []

        for result in match_results:
            key = result.matched_entity.key
            if key not in seen_keys:
                seen_keys.add(key)
                unique_results.append(result)
            else:
                logger.debug("Skipping duplicate author key %s", key)

        duplicate_count = len(match_results) - len(unique_results)

        if duplicate_count > 0:
            logger.info(
                "Deduplicated: %d unique authors from %d match results",
                len(unique_results),
                len(match_results),
            )

        return unique_results, duplicate_count


# ============================================================================
# Progress Tracking
# ============================================================================


class ProgressTracker:
    """Tracks progress through a sequence of items."""

    def __init__(self) -> None:
        """Initialize progress tracker."""
        self._progress = 0.0
        self._total = 0
        self._current = 0

    def reset(self, total: int) -> None:
        """Reset tracker with new total.

        Parameters
        ----------
        total : int
            Total number of items.
        """
        self._total = total
        self._current = 0
        self._progress = 0.0

    def update(self) -> None:
        """Update progress by one item."""
        self._current += 1
        if self._total > 0:
            self._progress = self._current / self._total
        else:
            self._progress = 0.0

    @property
    def progress(self) -> float:
        """Get current progress.

        Returns
        -------
        float
            Progress value between 0.0 and 1.0.
        """
        return self._progress

    @property
    def current(self) -> int:
        """Get current index.

        Returns
        -------
        int
            Current item index (1-based).
        """
        return self._current


# ============================================================================
# Unit of Work
# ============================================================================


class AuthorIngestionUnitOfWork:
    """Encapsulate a complete author ingestion transaction."""

    def __init__(
        self,
        session: Session,
        author_service: AuthorMetadataService,
        work_service: AuthorWorkService,
        subject_strategy: SubjectFetchStrategy | None = None,
        data_fetcher: AuthorDataFetcher | None = None,
        max_works_per_author: int | None = None,
    ) -> None:
        """Initialize unit of work.

        Parameters
        ----------
        session : Session
            Database session.
        author_service : AuthorMetadataService
            Author metadata service.
        work_service : AuthorWorkService
            Work service.
        subject_strategy : SubjectFetchStrategy | None
            Optional subject fetching strategy.
        data_fetcher : AuthorDataFetcher | None
            Optional data fetcher for works.
        max_works_per_author : int | None
            Maximum number of works to fetch per author when persisting works
            (None = no limit).
        """
        self.session = session
        self.author_service = author_service
        self.work_service = work_service
        self.subject_strategy = subject_strategy
        self.data_fetcher = data_fetcher
        self.max_works_per_author = max_works_per_author

    def ingest_author(
        self,
        match_result: MatchResult,
        author_data: AuthorData,
    ) -> AuthorMetadata:
        """Ingest a single author as a unit of work.

        Parameters
        ----------
        match_result : MatchResult
            Match result containing author information.
        author_data : AuthorData
            Author data from external source.

        Returns
        -------
        AuthorMetadata
            Created or updated author metadata.

        Raises
        ------
        Exception
            If ingestion fails.
        """
        try:
            # Create/update author metadata
            author = self.author_service.upsert_author(author_data)

            # Fetch and persist works if data fetcher is available
            if self.data_fetcher and author.id:
                work_keys = self.data_fetcher.fetch_author_works(
                    author_data.key,
                    limit=self.max_works_per_author,
                )
                if work_keys:
                    self.work_service.persist_works(author.id, work_keys)

                    # Fetch subjects from works if strategy is provided
                    if self.subject_strategy:
                        # Note: This will also persist subjects to works
                        # Pass author metadata for work-based strategies
                        self.subject_strategy.fetch_subjects(author_data.key, author)

            self.session.flush()
        except Exception:
            logger.exception(
                "Failed to ingest author %s: %s", match_result.matched_entity.key
            )
            self.session.rollback()
            raise
        else:
            return author
