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

from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from fundamental.models.author_metadata import (
    AuthorMapping,
    AuthorMetadata,
    AuthorSimilarity,
    AuthorWork,
)
from fundamental.repositories.base import Repository


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

        Returns
        -------
        tuple[list[AuthorMetadata], int]
            Authors mapped to the library (ordered by name) and total count.
        """
        # Base query for counting - count distinct author IDs directly
        from sqlalchemy import func

        count_stmt = (
            select(func.count(func.distinct(AuthorMetadata.id)))
            .join(AuthorMapping, AuthorMetadata.id == AuthorMapping.author_metadata_id)
            .where(AuthorMapping.library_id == library_id)
        )
        total = self._session.exec(count_stmt).one() or 0

        # Base query for fetching
        base_stmt = (
            select(AuthorMetadata)
            .join(AuthorMapping, AuthorMetadata.id == AuthorMapping.author_metadata_id)
            .where(AuthorMapping.library_id == library_id)
            .distinct()
        )

        # Paginated query
        offset = (page - 1) * page_size
        stmt = (
            base_stmt.options(
                selectinload(AuthorMetadata.remote_ids),
                selectinload(AuthorMetadata.photos),
                selectinload(AuthorMetadata.alternate_names),
                selectinload(AuthorMetadata.links),
                selectinload(AuthorMetadata.works).selectinload(AuthorWork.subjects),
            )
            .order_by(AuthorMetadata.name)
            .offset(offset)
            .limit(page_size)
        )
        authors = list(self._session.exec(stmt).all())
        return authors, total

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

        Parameters
        ----------
        openlibrary_key : str
            OpenLibrary author key (e.g., "OL23919A").
        library_id : int
            Library identifier.

        Returns
        -------
        AuthorMetadata | None
            Author if found and mapped to library, None otherwise.
        """
        stmt = (
            select(AuthorMetadata)
            .where(AuthorMetadata.openlibrary_key == openlibrary_key)
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
