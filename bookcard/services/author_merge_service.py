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

"""Author merge service for consolidating duplicate author records.

Follows SRP by focusing solely on author merge orchestration.
Uses IOC by accepting repositories and services as dependencies.
"""

import logging

from sqlmodel import Session, select

from bookcard.models.author_metadata import (
    AuthorMapping,
    AuthorMetadata,
    AuthorUserPhoto,
)
from bookcard.repositories.author_repository import AuthorRepository
from bookcard.repositories.config_repository import LibraryRepository
from bookcard.services.author_merge.author_recommendation_service import (
    AuthorRecommendationService,
)
from bookcard.services.author_merge.author_relationship_repository import (
    AuthorRelationshipRepository,
)
from bookcard.services.author_merge.calibre_author_service import (
    CalibreAuthorService,
)
from bookcard.services.author_merge.calibre_repository_factory import (
    CalibreRepositoryFactory,
)
from bookcard.services.author_merge.merge_strategies import MergeStrategyFactory
from bookcard.services.author_merge.value_objects import MergeContext
from bookcard.services.config_service import LibraryService

logger = logging.getLogger(__name__)


class AuthorMergeService:
    """Service for merging duplicate author records.

    Handles orchestration of author merge operations, delegating
    specific concerns to specialized services and repositories.
    """

    def __init__(
        self,
        session: Session,
        author_repo: AuthorRepository | None = None,
        library_service: LibraryService | None = None,
        library_repo: LibraryRepository | None = None,
        data_directory: str | None = None,
    ) -> None:
        """Initialize author merge service.

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
        data_directory : str | None
            Data directory path for file operations. If None, defaults to "/data".
        """
        self._session = session
        self._author_repo = author_repo or AuthorRepository(session)

        if library_service is None:
            lib_repo = library_repo or LibraryRepository(session)
            self._library_service = LibraryService(session, lib_repo)
        else:
            self._library_service = library_service

        # Initialize repositories and services
        self._relationship_repo = AuthorRelationshipRepository(session)
        self._data_directory = data_directory or "/data"

        # Calibre services will be created on-demand per library
        self._calibre_repo_factory = CalibreRepositoryFactory()

    def recommend_keep_author(
        self,
        author_ids: list[str],
    ) -> dict[str, object]:
        """Recommend which author to keep when merging.

        Parameters
        ----------
        author_ids : list[str]
            List of author IDs (author_metadata IDs or OpenLibrary keys).

        Returns
        -------
        dict[str, object]
            Dictionary with:
            - recommended_keep_id: Recommended author ID to keep
            - authors: List of author details for modal display

        Raises
        ------
        ValueError
            If less than 2 authors provided, authors not found, or not in same library.
        """
        if len(author_ids) < 2:
            msg = "At least 2 authors required for merge"
            raise ValueError(msg)

        active_library = self._library_service.get_active_library()
        if not active_library or active_library.id is None:
            msg = "No active library found"
            raise ValueError(msg)

        # Resolve all authors
        authors = []
        for author_id in author_ids:
            author = self._lookup_author(author_id, active_library.id)
            if not author:
                msg = f"Author not found: {author_id}"
                raise ValueError(msg)
            authors.append(author)

        # Validate all authors are in the same library
        self._validate_same_library(authors)

        # Initialize Calibre service for book counts
        calibre_repo = self._calibre_repo_factory.create(active_library)
        if not calibre_repo:
            msg = "Cannot access Calibre database"
            raise ValueError(msg)
        calibre_author_service = CalibreAuthorService(calibre_repo)

        # Initialize recommendation service
        recommendation_service = AuthorRecommendationService(
            self._relationship_repo, calibre_author_service
        )

        # Determine best author
        def get_book_count_wrapper(author: AuthorMetadata, library_id: int) -> int:
            return self._get_book_count_for_author(
                author, library_id, calibre_author_service
            )

        best_author = recommendation_service.determine_best_author(
            authors,
            active_library.id,
            get_mapping=self._get_mapping_for_author,
            get_book_count=get_book_count_wrapper,
        )

        # Build author details for modal
        author_details = []
        for author in authors:
            book_count = self._get_book_count_for_author(
                author,
                active_library.id,
                calibre_author_service,
            )
            mapping = self._get_mapping_for_author(author.id, active_library.id)
            photo_url = self._get_photo_url_for_author(author)
            relationship_counts = (
                self._relationship_repo.get_relationship_counts(author.id)
                if author.id
                else None
            )

            author_details.append({
                "id": str(author.id) if author.id else None,
                "key": author.openlibrary_key,
                "name": author.name,
                "book_count": book_count,
                "is_verified": mapping.is_verified if mapping else False,
                "metadata_score": recommendation_service.calculate_metadata_score(
                    author
                ),
                "photo_url": photo_url,
                "relationship_counts": relationship_counts.__dict__
                if relationship_counts
                else {},
            })

        return {
            "recommended_keep_id": str(best_author.id) if best_author.id else None,
            "authors": author_details,
        }

    def merge_authors(
        self,
        author_ids: list[str],
        keep_author_id: str,
    ) -> dict[str, object]:
        """Merge multiple authors into one.

        Parameters
        ----------
        author_ids : list[str]
            List of author IDs to merge (author_metadata IDs or OpenLibrary keys).
        keep_author_id : str
            Author ID to keep (others will be merged into this one).

        Returns
        -------
        dict[str, object]
            Dictionary with merged author details.

        Raises
        ------
        ValueError
            If less than 2 authors provided, authors not found, or not in same library.
        """
        if len(author_ids) < 2:
            msg = "At least 2 authors required for merge"
            raise ValueError(msg)

        active_library = self._library_service.get_active_library()
        if not active_library or active_library.id is None:
            msg = "No active library found"
            raise ValueError(msg)

        # Resolve and validate authors
        authors = self._resolve_authors(author_ids, active_library.id)
        keep_author = self._resolve_keep_author(
            keep_author_id,
            authors,
            active_library.id,
        )
        merge_authors_list = self._get_merge_authors(authors, keep_author)

        # Validate all authors are in the same library
        self._validate_same_library(authors)

        # Initialize Calibre service
        calibre_repo = self._calibre_repo_factory.create(active_library)
        if not calibre_repo:
            msg = "Cannot access Calibre database for merge"
            raise ValueError(msg)
        calibre_author_service = CalibreAuthorService(calibre_repo)

        # Initialize strategy factory
        strategy_factory = MergeStrategyFactory(
            self._session,
            calibre_author_service,
            self._relationship_repo,
            self._data_directory,
        )

        # Perform merge for each author to merge
        for merge_author in merge_authors_list:
            if not merge_author.id or not keep_author.id:
                continue

            # Get mappings
            keep_mapping = self._get_mapping_for_author(
                keep_author.id, active_library.id
            )
            merge_mapping = self._get_mapping_for_author(
                merge_author.id, active_library.id
            )

            if not keep_mapping or not merge_mapping:
                logger.warning(
                    "Missing mappings for merge: keep=%s, merge=%s",
                    keep_author.id,
                    merge_author.id,
                )
                continue

            # Create merge context
            merge_context = MergeContext(
                keep_author=keep_author,
                merge_author=merge_author,
                library_id=active_library.id,
                keep_mapping=keep_mapping,
                merge_mapping=merge_mapping,
            )

            # Update similarities before merge
            self._relationship_repo.update_similarities_for_merge(
                keep_author.id, merge_author.id
            )

            # Get and execute appropriate strategy
            strategy = strategy_factory.get_strategy(merge_context)
            strategy.execute(merge_context)

        # Commit transaction
        self._session.commit()

        # Return merged author details
        return {
            "id": str(keep_author.id) if keep_author.id else None,
            "key": keep_author.openlibrary_key,
            "name": keep_author.name,
        }

    def _resolve_authors(
        self,
        author_ids: list[str],
        library_id: int,
    ) -> list[AuthorMetadata]:
        """Resolve all author IDs to AuthorMetadata objects.

        Parameters
        ----------
        author_ids : list[str]
            List of author IDs to resolve.
        library_id : int
            Library ID.

        Returns
        -------
        list[AuthorMetadata]
            List of resolved authors.

        Raises
        ------
        ValueError
            If any author is not found.
        """
        authors = []
        for author_id in author_ids:
            author = self._lookup_author(author_id, library_id)
            if not author:
                msg = f"Author not found: {author_id}"
                raise ValueError(msg)
            authors.append(author)
        return authors

    def _resolve_keep_author(
        self,
        keep_author_id: str,
        authors: list[AuthorMetadata],
        library_id: int,
    ) -> AuthorMetadata:
        """Resolve and validate the keep author.

        Parameters
        ----------
        keep_author_id : str
            Author ID to keep.
        authors : list[AuthorMetadata]
            List of all authors being merged.
        library_id : int
            Library ID.

        Returns
        -------
        AuthorMetadata
            Keep author.

        Raises
        ------
        ValueError
            If keep author is not found or not in the merge list.
        """
        keep_author = self._lookup_author(keep_author_id, library_id)
        if not keep_author:
            msg = f"Keep author not found: {keep_author_id}"
            raise ValueError(msg)

        if keep_author.id not in {a.id for a in authors if a.id}:
            msg = "Keep author must be one of the authors to merge"
            raise ValueError(msg)

        return keep_author

    def _get_merge_authors(
        self,
        authors: list[AuthorMetadata],
        keep_author: AuthorMetadata,
    ) -> list[AuthorMetadata]:
        """Get list of authors to merge (excluding keep author).

        Parameters
        ----------
        authors : list[AuthorMetadata]
            All authors in the merge.
        keep_author : AuthorMetadata
            Author to keep.

        Returns
        -------
        list[AuthorMetadata]
            Authors to merge.
        """
        return [a for a in authors if a.id != keep_author.id]

    def _validate_same_library(self, authors: list[AuthorMetadata]) -> None:
        """Validate all authors belong to the same library.

        Parameters
        ----------
        authors : list[AuthorMetadata]
            Authors to validate.

        Raises
        ------
        ValueError
            If authors belong to different libraries.
        """
        library_ids = set()
        for author in authors:
            if author.id:
                mapping = self._session.exec(
                    select(AuthorMapping).where(
                        AuthorMapping.author_metadata_id == author.id,
                    )
                ).first()
                if mapping:
                    library_ids.add(mapping.library_id)

        if len(library_ids) > 1:
            msg = "All authors must belong to the same library"
            raise ValueError(msg)

    def _get_mapping_for_author(
        self,
        author_metadata_id: int | None,
        library_id: int,
    ) -> AuthorMapping | None:
        """Get author mapping for an author.

        Parameters
        ----------
        author_metadata_id : int | None
            Author metadata ID.
        library_id : int
            Library ID.

        Returns
        -------
        AuthorMapping | None
            Author mapping if found, None otherwise.
        """
        if not author_metadata_id:
            return None

        return self._session.exec(
            select(AuthorMapping).where(
                AuthorMapping.author_metadata_id == author_metadata_id,
                AuthorMapping.library_id == library_id,
            )
        ).first()

    def _lookup_author(
        self,
        author_id: str,
        library_id: int,
    ) -> AuthorMetadata | None:
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

    def _get_photo_url_for_author(
        self,
        author: AuthorMetadata,
    ) -> str | None:
        """Get photo URL for an author.

        Parameters
        ----------
        author : AuthorMetadata
            Author metadata.

        Returns
        -------
        str | None
            Photo URL if available, None otherwise.
        """
        # Get photo URL from author model
        # Note: photo_url may be from OpenLibrary or set from user_photos
        photo_url = author.photo_url

        # If no photo_url but we have user_photos, try to get primary photo
        if not photo_url and author.id:
            # Load user_photos if not already loaded
            user_photos_stmt = select(AuthorUserPhoto).where(
                AuthorUserPhoto.author_metadata_id == author.id
            )
            user_photos = list(self._session.exec(user_photos_stmt).all())

            if user_photos:
                # Check for primary photo
                primary_photo = next(
                    (up for up in user_photos if up.is_primary),
                    None,
                )
                if primary_photo and primary_photo.id:
                    photo_url = f"/api/authors/{author.id}/photos/{primary_photo.id}"
                elif user_photos[0].id:
                    # Use first photo if no primary
                    photo_url = f"/api/authors/{author.id}/photos/{user_photos[0].id}"

        return photo_url

    def _get_book_count_for_author(
        self,
        author: AuthorMetadata,
        library_id: int,
        calibre_author_service: CalibreAuthorService | None = None,
    ) -> int:
        """Get book count for an author.

        Parameters
        ----------
        author : AuthorMetadata
            Author metadata.
        library_id : int
            Library ID.
        calibre_author_service : CalibreAuthorService | None
            Optional Calibre author service. If None, creates one.

        Returns
        -------
        int
            Number of books mapped to this author.
        """
        mapping = self._get_mapping_for_author(author.id, library_id)
        if not mapping:
            return 0

        # Use provided service or create one
        if calibre_author_service:
            return calibre_author_service.get_book_count(mapping.calibre_author_id)

        # Fallback: create service on demand
        active_library = self._library_service.get_active_library()
        if not active_library:
            return 0

        calibre_repo = self._calibre_repo_factory.create(active_library)
        if not calibre_repo:
            return 0

        service = CalibreAuthorService(calibre_repo)
        return service.get_book_count(mapping.calibre_author_id)
