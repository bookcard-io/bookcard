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

"""Components for author listing operations.

Follows SRP by separating query building, data fetching, and result hydration.
Uses IOC by accepting dependencies through constructor injection.
"""

import logging
from collections.abc import Sequence
from typing import Protocol

from sqlalchemy import func, literal
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import Select
from sqlmodel import Session, select

from fundamental.models.author_metadata import (
    AuthorMapping,
    AuthorMetadata,
    AuthorWork,
)
from fundamental.models.core import Author
from fundamental.repositories.calibre_book_repository import CalibreBookRepository

logger = logging.getLogger(__name__)


class AuthorResultRow(Protocol):
    """Protocol for author result rows."""

    name: str
    type: str
    id: int


class UnmatchedAuthorRow:
    """Row-like object for unmatched authors."""

    def __init__(self, name: str, author_id: int) -> None:
        """Initialize unmatched author row.

        Parameters
        ----------
        name : str
            Author name.
        author_id : int
            Calibre author ID.
        """
        self.name = name
        self.type = "unmatched"
        self.id = author_id


class MatchedAuthorQueryBuilder:
    """Builds queries for matched authors.

    Follows SRP by focusing solely on query construction.
    """

    @staticmethod
    def build_query(library_id: int) -> Select[tuple]:
        """Build query for matched authors.

        Parameters
        ----------
        library_id : int
            Library identifier.

        Returns
        -------
        select
            SQLModel select statement for matched authors.
        """
        return (
            select(
                AuthorMetadata.name.label("name"),  # type: ignore
                literal("matched").label("type"),
                AuthorMetadata.id.label("id"),  # type: ignore
            )
            .join(AuthorMapping, AuthorMetadata.id == AuthorMapping.author_metadata_id)
            .where(AuthorMapping.library_id == library_id)
        )

    @staticmethod
    def build_count_query(library_id: int) -> Select[tuple]:
        """Build count query for matched authors.

        Parameters
        ----------
        library_id : int
            Library identifier.

        Returns
        -------
        select
            SQLModel select statement for counting matched authors.
        """
        return (
            select(func.count(AuthorMetadata.id))  # type: ignore
            .join(AuthorMapping, AuthorMetadata.id == AuthorMapping.author_metadata_id)
            .where(AuthorMapping.library_id == library_id)
        )


class MappedIdsFetcher:
    """Fetches mapped Calibre author IDs for a library.

    Follows SRP by focusing solely on ID retrieval.
    """

    def __init__(self, session: Session) -> None:
        """Initialize mapped IDs fetcher.

        Parameters
        ----------
        session : Session
            Database session.
        """
        self._session = session

    def get_mapped_ids(self, library_id: int) -> set[int]:
        """Get set of mapped Calibre author IDs.

        Parameters
        ----------
        library_id : int
            Library identifier.

        Returns
        -------
        set[int]
            Set of mapped Calibre author IDs.
        """
        stmt = select(AuthorMapping.calibre_author_id).where(
            AuthorMapping.library_id == library_id
        )
        return {row for row in self._session.exec(stmt).all() if row is not None}


class UnmatchedAuthorFetcher:
    """Fetches unmatched authors from Calibre database.

    Follows SRP by focusing solely on unmatched author retrieval.
    Uses IOC by accepting CalibreBookRepository factory.
    """

    def __init__(
        self,
        session: Session,
        calibre_repo_factory: type[CalibreBookRepository] = CalibreBookRepository,
    ) -> None:
        """Initialize unmatched author fetcher.

        Parameters
        ----------
        session : Session
            Database session (for consistency, though not used directly).
        calibre_repo_factory : type[CalibreBookRepository]
            Factory for creating CalibreBookRepository instances.
        """
        self._session = session
        self._calibre_repo_factory = calibre_repo_factory

    def fetch_unmatched(
        self,
        mapped_ids: set[int],
        calibre_db_path: str | None,
        calibre_db_file: str,
    ) -> list[Author]:
        """Fetch unmatched authors from Calibre database.

        Parameters
        ----------
        mapped_ids : set[int]
            Set of already mapped Calibre author IDs.
        calibre_db_path : str | None
            Path to Calibre database directory.
        calibre_db_file : str
            Calibre database filename.

        Returns
        -------
        list[Author]
            List of unmatched authors.
        """
        if not calibre_db_path:
            return []

        try:
            calibre_repo = self._calibre_repo_factory(calibre_db_path, calibre_db_file)
            with calibre_repo.get_session() as calibre_session:
                all_authors_stmt = select(Author)
                all_authors = list(calibre_session.exec(all_authors_stmt).all())
                return [
                    author
                    for author in all_authors
                    if author.id is not None and author.id not in mapped_ids
                ]
        except Exception:
            logger.exception(
                "Could not access Calibre database at %s",
                calibre_db_path,
            )
            return []


class AuthorResultCombiner:
    """Combines and paginates author results.

    Follows SRP by focusing solely on result combination and pagination.
    """

    @staticmethod
    def combine_and_paginate(
        matched_results: list[AuthorResultRow],
        unmatched_authors: list[Author],
        page: int,
        page_size: int,
    ) -> Sequence[AuthorResultRow]:
        """Combine matched and unmatched results, then paginate.

        Parameters
        ----------
        matched_results : list[AuthorResultRow]
            Matched author results.
        unmatched_authors : list[Author]
            Unmatched authors from Calibre.
        page : int
            Page number (1-indexed).
        page_size : int
            Number of items per page.

        Returns
        -------
        Sequence[AuthorResultRow]
            Paginated and sorted results.
        """
        all_results: list[AuthorResultRow] = list(matched_results)  # type: ignore[arg-type]

        all_results.extend(
            UnmatchedAuthorRow(author.name, author.id)  # type: ignore[arg-type]
            for author in unmatched_authors
            if author.id is not None
        )

        all_results.sort(key=lambda r: r.name)

        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        return all_results[start_idx:end_idx]


class AuthorHydrator:
    """Hydrates full AuthorMetadata objects from result rows.

    Follows SRP by focusing solely on object hydration.
    """

    def __init__(self, session: Session) -> None:
        """Initialize author hydrator.

        Parameters
        ----------
        session : Session
            Database session.
        """
        self._session = session

    def hydrate_matched(self, matched_ids: list[int]) -> dict[int, AuthorMetadata]:
        """Hydrate matched author objects.

        Parameters
        ----------
        matched_ids : list[int]
            List of matched author metadata IDs.

        Returns
        -------
        dict[int, AuthorMetadata]
            Dictionary mapping ID to AuthorMetadata object.
        """
        if not matched_ids:
            return {}

        try:
            stmt = (
                select(AuthorMetadata)
                .where(AuthorMetadata.id.in_(matched_ids))  # type: ignore
                .options(
                    selectinload(AuthorMetadata.remote_ids),
                    selectinload(AuthorMetadata.photos),
                    selectinload(AuthorMetadata.alternate_names),
                    selectinload(AuthorMetadata.links),
                    selectinload(AuthorMetadata.works).selectinload(
                        AuthorWork.subjects
                    ),
                )
            )
            return {a.id: a for a in self._session.exec(stmt).all()}
        except Exception:
            logger.exception("Error hydrating matched authors")
            raise

    def create_unmatched_metadata(
        self, unmatched_ids: list[int], calibre_db_path: str, calibre_db_file: str
    ) -> dict[int, AuthorMetadata]:
        """Create transient AuthorMetadata objects for unmatched authors.

        Parameters
        ----------
        unmatched_ids : list[int]
            List of unmatched Calibre author IDs.
        calibre_db_path : str
            Path to Calibre database directory.
        calibre_db_file : str
            Calibre database filename.

        Returns
        -------
        dict[int, AuthorMetadata]
            Dictionary mapping Calibre ID to transient AuthorMetadata object.
        """
        if not unmatched_ids:
            return {}

        try:
            calibre_repo = CalibreBookRepository(calibre_db_path, calibre_db_file)
            with calibre_repo.get_session() as calibre_session:
                stmt = select(Author).where(Author.id.in_(unmatched_ids))  # type: ignore
                calibre_authors = calibre_session.exec(stmt).all()

                result = {}
                for author in calibre_authors:
                    if author.id is not None:
                        # Create transient AuthorMetadata object
                        metadata = AuthorMetadata(
                            name=author.name,
                            is_unmatched=True,
                            openlibrary_key=f"calibre-{author.id}",  # Placeholder key
                            id=None,  # Not persisted - this is a transient object
                        )
                        # Store Calibre ID as a private attribute for service layer access
                        object.__setattr__(metadata, "_calibre_id", author.id)
                        result[author.id] = metadata

                return result
        except Exception:
            logger.exception("Error creating unmatched author metadata")
            raise
