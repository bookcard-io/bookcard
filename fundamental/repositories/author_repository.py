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
    MatchedAuthorQueryBuilder,
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
        page: int = 1,
        page_size: int = 20,
        **_kwargs: object,  # Allow unused kwargs for backward compatibility
    ) -> tuple[list[AuthorMetadata], int]:
        """List authors mapped to a specific library with pagination.

        Parameters
        ----------
        library_id : int
            Library identifier.
        page : int
            Page number (1-indexed, default: 1).
        page_size : int
            Number of items per page (default: 20).
        **_kwargs
            Unused kwargs (calibre_db_path, calibre_db_file) for backward compatibility.

        Returns
        -------
        tuple[list[AuthorMetadata], int]
            Authors (ordered by name) and total count.
        """
        # Initialize components (IOC - dependency injection)
        query_builder = MatchedAuthorQueryBuilder()

        # Count total authors (only matched authors now)
        total = self._count_matched(query_builder, library_id)

        # Fetch paginated results
        paginated_results = self._fetch_matched_results(
            query_builder, library_id, page, page_size
        )

        # Hydrate full objects
        hydrator = AuthorHydrator(self._session)
        final_results = self._hydrate_results(paginated_results, hydrator)

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
        self,
        query_builder: MatchedAuthorQueryBuilder,
        library_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> list:
        """Fetch matched author results.

        Parameters
        ----------
        query_builder : MatchedAuthorQueryBuilder
            Query builder instance.
        library_id : int
            Library identifier.
        page : int
            Page number (1-indexed, default: 1).
        page_size : int
            Number of items per page (default: 20).

        Returns
        -------
        list
            List of matched author result rows.
        """
        try:
            matched_query = query_builder.build_query(library_id)

            # Apply pagination
            matched_query = matched_query.offset((page - 1) * page_size).limit(
                page_size
            )

            # Add ordering
            matched_query = matched_query.order_by(AuthorMetadata.name)  # type: ignore

            return list(self._session.exec(matched_query).all())  # type: ignore[no-matching-overload]
        except Exception:
            logger.exception("Error fetching matched authors")
            raise

    def _hydrate_results(
        self,
        paginated_results: Sequence,
        hydrator: AuthorHydrator,
    ) -> list[AuthorMetadata]:
        """Hydrate full AuthorMetadata objects from result rows.

        Parameters
        ----------
        paginated_results : list
            Paginated result rows.
        hydrator : AuthorHydrator
            Author hydrator instance.

        Returns
        -------
        list[AuthorMetadata]
            List of hydrated AuthorMetadata objects.
        """
        # We only have matched authors now, but method might be extended
        matched_ids = [r.id for r in paginated_results]
        matched_objs = hydrator.hydrate_matched(matched_ids)

        # Build final result list in the same order as paginated_results
        return [
            matched_objs[row.id] for row in paginated_results if row.id in matched_objs
        ]

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

    def get_by_calibre_id_and_library(
        self,
        calibre_author_id: int,
        library_id: int,
    ) -> AuthorMetadata | None:
        """Get author by Calibre author ID and library.

        Parameters
        ----------
        calibre_author_id : int
            Calibre author identifier.
        library_id : int
            Library identifier.

        Returns
        -------
        AuthorMetadata | None
            Author if found and mapped, None otherwise.
        """
        stmt = (
            select(AuthorMetadata)
            .join(AuthorMapping, AuthorMetadata.id == AuthorMapping.author_metadata_id)
            .where(
                AuthorMapping.calibre_author_id == calibre_author_id,
                AuthorMapping.library_id == library_id,
            )
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

        Optimized to use a single query with OR condition and CASE expression.

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
        from sqlalchemy import case

        # Single query using OR to get similarities in both directions
        # Use CASE to extract the "other" author ID
        stmt = (
            select(
                case(
                    (
                        AuthorSimilarity.author1_id == author_id,
                        AuthorSimilarity.author2_id,
                    ),  # type: ignore[attr-defined]
                    else_=AuthorSimilarity.author1_id,  # type: ignore[attr-defined]
                ).label("similar_author_id"),  # type: ignore[attr-defined]
                AuthorSimilarity.similarity_score,  # type: ignore[attr-defined]
            )
            .where(
                (AuthorSimilarity.author1_id == author_id)
                | (AuthorSimilarity.author2_id == author_id)
            )
            .order_by(AuthorSimilarity.similarity_score.desc())  # type: ignore[attr-defined]
            .limit(limit * 2)  # Get more than needed to handle potential duplicates
        )

        # Execute and deduplicate
        results = list(self._session.exec(stmt).all())
        seen_ids: set[int] = set()
        similar_author_ids: list[int] = []
        for similar_id, _score in results:
            if similar_id and similar_id not in seen_ids:
                seen_ids.add(similar_id)
                similar_author_ids.append(similar_id)
                if len(similar_author_ids) >= limit:
                    break

        return similar_author_ids

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

    def get_similar_authors_in_library(
        self,
        author_id: int,
        library_id: int,
        limit: int = 6,
    ) -> list[AuthorMetadata]:
        """Get similar authors that are in a specific library.

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
        list[AuthorMetadata]
            List of similar authors in the library, ordered by similarity score.
        """
        # Get similar author IDs
        similar_author_ids = self.get_similar_author_ids(author_id, limit=limit * 2)

        if not similar_author_ids:
            return []

        # Batch fetch authors with library filtering in a single query
        # Join with AuthorMapping to ensure authors are in the library
        stmt = (
            select(AuthorMetadata)
            .join(
                AuthorMapping,
                AuthorMetadata.id == AuthorMapping.author_metadata_id,
            )
            .where(
                AuthorMapping.library_id == library_id,
                AuthorMetadata.id.in_(similar_author_ids),  # type: ignore[attr-defined]
            )
            .options(
                selectinload(AuthorMetadata.remote_ids),
                selectinload(AuthorMetadata.photos),
                selectinload(AuthorMetadata.alternate_names),
                selectinload(AuthorMetadata.links),
                selectinload(AuthorMetadata.works).selectinload(AuthorWork.subjects),
            )
            .distinct()
            .limit(limit)
        )

        authors = list(self._session.exec(stmt).all())

        # Sort by original similarity order (preserve order from get_similar_author_ids)
        author_map = {author.id: author for author in authors}
        return [
            author_map[similar_id]
            for similar_id in similar_author_ids
            if similar_id in author_map
        ][:limit]

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
