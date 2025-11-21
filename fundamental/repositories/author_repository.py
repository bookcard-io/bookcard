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

"""Author repository for database operations.

Follows SRP by focusing solely on data access.
Uses IOC by accepting session as dependency.
"""

import logging
from collections.abc import Sequence

from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from fundamental.models.author_metadata import (
    AuthorMapping,
    AuthorMetadata,
    AuthorSimilarity,
    AuthorWork,
)
from fundamental.repositories.author_listing_components import (
    AuthorHydrator,
    AuthorResultCombiner,
    MappedIdsFetcher,
    MatchedAuthorQueryBuilder,
    UnmatchedAuthorFetcher,
)
from fundamental.repositories.base import Repository

logger = logging.getLogger(__name__)


class AuthorRepository(Repository[AuthorMetadata]):
    """Repository for AuthorMetadata entities.

    Provides methods for querying authors with their relationships.
    """

    def __init__(self, session: Session) -> None:
        """Initialize author repository.

        Parameters
        ----------
        session : Session
            Database session.
        """
        super().__init__(session, AuthorMetadata)

    def list_by_library(
        self,
        library_id: int,
        calibre_db_path: str | None = None,
        calibre_db_file: str = "metadata.db",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AuthorMetadata], int]:
        """List authors mapped to a specific library with pagination.

        Includes both matched authors (AuthorMetadata) and unmatched authors (Author).
        Unmatched authors are returned as transient AuthorMetadata objects with
        is_unmatched=True.

        Parameters
        ----------
        library_id : int
            Library identifier.
        calibre_db_path : str | None
            Path to Calibre database directory. If None, unmatched authors
            will not be included.
        calibre_db_file : str
            Calibre database filename (default: 'metadata.db').
        page : int
            Page number (1-indexed, default: 1).
        page_size : int
            Number of items per page (default: 20).

        Returns
        -------
        tuple[list[AuthorMetadata], int]
            Authors (ordered by name) and total count.
        """
        # Initialize components (IOC - dependency injection)
        query_builder = MatchedAuthorQueryBuilder()
        ids_fetcher = MappedIdsFetcher(self._session)
        unmatched_fetcher = UnmatchedAuthorFetcher(self._session)
        combiner = AuthorResultCombiner()
        hydrator = AuthorHydrator(self._session)

        # 1. Get mapped IDs
        mapped_ids = ids_fetcher.get_mapped_ids(library_id)

        # 2. Fetch unmatched authors
        unmatched_authors = unmatched_fetcher.fetch_unmatched(
            mapped_ids, calibre_db_path, calibre_db_file
        )

        # 3. Count matched authors
        count_matched = self._count_matched(query_builder, library_id)
        count_unmatched = len(unmatched_authors)
        total = count_matched + count_unmatched

        # 4. Fetch matched results
        matched_results = self._fetch_matched_results(query_builder, library_id)

        # 5. Combine and paginate
        paginated_results = combiner.combine_and_paginate(
            matched_results, unmatched_authors, page, page_size
        )

        # 6. Hydrate full objects
        final_results = self._hydrate_results(
            paginated_results, hydrator, calibre_db_path, calibre_db_file
        )

        return final_results, total

    def _count_matched(
        self, query_builder: MatchedAuthorQueryBuilder, library_id: int
    ) -> int:
        """Count matched authors.

        Parameters
        ----------
        query_builder : MatchedAuthorQueryBuilder
            Query builder instance.
        library_id : int
            Library identifier.

        Returns
        -------
        int
            Count of matched authors.
        """
        try:
            count_query = query_builder.build_count_query(library_id)
            return self._session.exec(count_query).one()  # type: ignore[no-matching-overload]
        except Exception:
            logger.exception("Error counting matched authors")
            raise

    def _fetch_matched_results(
        self, query_builder: MatchedAuthorQueryBuilder, library_id: int
    ) -> list:
        """Fetch matched author results.

        Parameters
        ----------
        query_builder : MatchedAuthorQueryBuilder
            Query builder instance.
        library_id : int
            Library identifier.

        Returns
        -------
        list
            List of matched author result rows.
        """
        try:
            matched_query = query_builder.build_query(library_id)
            return list(self._session.exec(matched_query).all())  # type: ignore[no-matching-overload]
        except Exception:
            logger.exception("Error fetching matched authors")
            raise

    def _hydrate_results(
        self,
        paginated_results: Sequence,
        hydrator: AuthorHydrator,
        calibre_db_path: str | None,
        calibre_db_file: str,
    ) -> list[AuthorMetadata]:
        """Hydrate full AuthorMetadata objects from result rows.

        Parameters
        ----------
        paginated_results : list
            Paginated result rows.
        hydrator : AuthorHydrator
            Author hydrator instance.
        calibre_db_path : str | None
            Path to Calibre database directory.
        calibre_db_file : str
            Calibre database filename.

        Returns
        -------
        list[AuthorMetadata]
            List of hydrated AuthorMetadata objects.
        """
        matched_ids = [r.id for r in paginated_results if r.type == "matched"]
        unmatched_ids = [r.id for r in paginated_results if r.type == "unmatched"]

        matched_objs = hydrator.hydrate_matched(matched_ids)

        unmatched_objs = {}
        if unmatched_ids and calibre_db_path:
            unmatched_objs = hydrator.create_unmatched_metadata(
                unmatched_ids, calibre_db_path, calibre_db_file
            )

        # Build final result list in the same order as paginated_results
        final_results: list[AuthorMetadata] = []
        for row in paginated_results:
            if row.type == "matched" and row.id in matched_objs:
                final_results.append(matched_objs[row.id])
            elif row.type == "unmatched" and row.id in unmatched_objs:
                final_results.append(unmatched_objs[row.id])

        return final_results

    def get_by_id_and_library(
        self,
        author_id: int,
        library_id: int,
    ) -> AuthorMetadata | None:
        """Get an author by ID, ensuring it's mapped to the library.

        Parameters
        ----------
        author_id : int
            Author metadata identifier.
        library_id : int
            Library identifier.

        Returns
        -------
        AuthorMetadata | None
            Author if found and mapped to library, None otherwise.
        """
        stmt = (
            select(AuthorMetadata)
            .where(AuthorMetadata.id == author_id)
            .join(AuthorMapping, AuthorMetadata.id == AuthorMapping.author_metadata_id)
            .where(AuthorMapping.library_id == library_id)
            .options(
                selectinload(AuthorMetadata.remote_ids),
                selectinload(AuthorMetadata.photos),
                selectinload(AuthorMetadata.alternate_names),
                selectinload(AuthorMetadata.links),
                selectinload(AuthorMetadata.works).selectinload(AuthorWork.subjects),
                selectinload(AuthorMetadata.similar_to),
                selectinload(AuthorMetadata.similar_from),
            )
        )
        return self._session.exec(stmt).first()

    def get_by_openlibrary_key_and_library(
        self,
        openlibrary_key: str,
        library_id: int,
    ) -> AuthorMetadata | None:
        """Get an author by OpenLibrary key, ensuring it's mapped to the library.

        Normalizes the key to OpenLibrary convention: "/authors/OL19981A".

        Parameters
        ----------
        openlibrary_key : str
            OpenLibrary author key (e.g., "OL23919A" or "/authors/OL23919A").
        library_id : int
            Library identifier.

        Returns
        -------
        AuthorMetadata | None
            Author if found and mapped to library, None otherwise.
        """
        # Normalize key to OpenLibrary convention: ensure /authors/ prefix
        if not openlibrary_key.startswith("/authors/"):
            normalized_key = f"/authors/{openlibrary_key.replace('authors/', '')}"
        else:
            normalized_key = openlibrary_key

        stmt = (
            select(AuthorMetadata)
            .where(AuthorMetadata.openlibrary_key == normalized_key)
            .join(AuthorMapping, AuthorMetadata.id == AuthorMapping.author_metadata_id)
            .where(AuthorMapping.library_id == library_id)
            .options(
                selectinload(AuthorMetadata.remote_ids),
                selectinload(AuthorMetadata.photos),
                selectinload(AuthorMetadata.alternate_names),
                selectinload(AuthorMetadata.links),
                selectinload(AuthorMetadata.works).selectinload(AuthorWork.subjects),
                selectinload(AuthorMetadata.similar_to),
                selectinload(AuthorMetadata.similar_from),
            )
        )
        return self._session.exec(stmt).first()

    def get_similar_author_ids(
        self,
        author_id: int,
        limit: int = 6,
    ) -> list[int]:
        """Get IDs of similar authors ordered by similarity score.

        Parameters
        ----------
        author_id : int
            Author identifier.
        limit : int
            Maximum number of similar authors to return (default: 6).

        Returns
        -------
        list[int]
            List of similar author IDs, ordered by similarity score (descending).
        """
        # Get similarities where this author is author1 (similar_author is author2)
        similar_stmt1 = (
            select(AuthorSimilarity)
            .where(AuthorSimilarity.author1_id == author_id)
            .order_by(AuthorSimilarity.similarity_score.desc())  # type: ignore[attr-defined]
            .limit(limit)
        )

        # Get similarities where this author is author2 (similar_author is author1)
        similar_stmt2 = (
            select(AuthorSimilarity)
            .where(AuthorSimilarity.author2_id == author_id)
            .order_by(AuthorSimilarity.similarity_score.desc())  # type: ignore[attr-defined]
            .limit(limit)
        )

        # Collect similar authors with their similarity scores
        similar_author_scores: list[tuple[int, float]] = [
            (similarity.author2_id, similarity.similarity_score)
            for similarity in self._session.exec(similar_stmt1).all()
            if similarity.author2_id
        ]
        similar_author_scores.extend(
            (similarity.author1_id, similarity.similarity_score)
            for similarity in self._session.exec(similar_stmt2).all()
            if similarity.author1_id
        )

        # Sort by similarity score (descending) and get unique author IDs
        similar_author_scores.sort(key=lambda x: x[1], reverse=True)
        seen_ids: set[int] = set()
        similar_author_ids: list[int] = []
        for similar_id, _score in similar_author_scores:
            if similar_id not in seen_ids:
                seen_ids.add(similar_id)
                similar_author_ids.append(similar_id)

        return similar_author_ids[:limit]

    def is_author_in_library(
        self,
        author_id: int,
        library_id: int,
    ) -> bool:
        """Check if an author is mapped to a library.

        Parameters
        ----------
        author_id : int
            Author metadata identifier.
        library_id : int
            Library identifier.

        Returns
        -------
        bool
            True if author is mapped to library, False otherwise.
        """
        mapping_check = select(AuthorMapping).where(
            AuthorMapping.author_metadata_id == author_id,
            AuthorMapping.library_id == library_id,
        )
        return self._session.exec(mapping_check).first() is not None

    def get_by_id(
        self,
        author_id: int,
    ) -> AuthorMetadata | None:
        """Get an author by ID without library filtering.

        Parameters
        ----------
        author_id : int
            Author metadata identifier.

        Returns
        -------
        AuthorMetadata | None
            Author if found, None otherwise.
        """
        stmt = select(AuthorMetadata).where(AuthorMetadata.id == author_id)
        return self._session.exec(stmt).first()
