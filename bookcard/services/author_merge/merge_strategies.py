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

"""Merge strategies for different author merge scenarios.

Follows OCP by using strategy pattern to allow extension without
modifying existing code.
"""

import logging
from typing import Protocol

from sqlmodel import Session

from bookcard.services.author_merge.author_relationship_repository import (
    AuthorRelationshipRepository,
)
from bookcard.services.author_merge.calibre_author_service import (
    CalibreAuthorService,
)
from bookcard.services.author_merge.value_objects import MergeContext

logger = logging.getLogger(__name__)


class MergeStrategy(Protocol):
    """Protocol for merge strategies.

    Defines the interface that all merge strategies must implement.
    """

    def can_handle(self, merge_context: MergeContext) -> bool:
        """Check if this strategy can handle the merge context.

        Parameters
        ----------
        merge_context : MergeContext
            Merge context to evaluate.

        Returns
        -------
        bool
            True if this strategy can handle the merge, False otherwise.
        """
        ...

    def execute(self, merge_context: MergeContext) -> None:
        """Execute the merge strategy.

        Parameters
        ----------
        merge_context : MergeContext
            Merge context containing authors and mappings.
        """
        ...


class ZeroBooksMergeStrategy:
    """Strategy for merging author with zero books into author with books.

    This strategy handles the case where the merge author has no books,
    so we can simply delete the Calibre author and mapping.
    """

    def __init__(
        self,
        session: Session,
        calibre_author_service: CalibreAuthorService,
        relationship_repo: AuthorRelationshipRepository,
        data_directory: str | None = None,
    ) -> None:
        """Initialize zero books merge strategy.

        Parameters
        ----------
        session : Session
            Database session.
        calibre_author_service : CalibreAuthorService
            Service for Calibre author operations.
        relationship_repo : AuthorRelationshipRepository
            Repository for relationship operations.
        data_directory : str | None
            Data directory path for file operations.
        """
        self._session = session
        self._calibre_author_service = calibre_author_service
        self._relationship_repo = relationship_repo
        self._data_directory = data_directory

    def can_handle(self, merge_context: MergeContext) -> bool:
        """Check if merge author has zero books.

        Parameters
        ----------
        merge_context : MergeContext
            Merge context to evaluate.

        Returns
        -------
        bool
            True if merge author has zero books, False otherwise.
        """
        merge_book_count = self._calibre_author_service.get_book_count(
            merge_context.merge_mapping.calibre_author_id
        )
        return merge_book_count == 0

    def execute(self, merge_context: MergeContext) -> None:
        """Execute zero books merge strategy.

        Parameters
        ----------
        merge_context : MergeContext
            Merge context containing authors and mappings.
        """
        logger.info(
            "Merging author with zero books: merge_calibre_id=%s",
            merge_context.merge_mapping.calibre_author_id,
        )

        merge_author = merge_context.merge_author
        merge_calibre_id = merge_context.merge_mapping.calibre_author_id

        # Delete Calibre author and cascade relationships
        self._calibre_author_service.delete_author(merge_calibre_id)

        # Delete author mapping
        self._session.delete(merge_context.merge_mapping)
        self._session.flush()

        # Handle AuthorWork records, user photos, user metadata, and similarities
        # before deleting merge_author
        if merge_author.id:
            self._relationship_repo.delete_author_works(merge_author.id)
            self._relationship_repo.delete_author_user_photos(
                merge_author.id, self._data_directory
            )
            self._relationship_repo.delete_author_user_metadata(merge_author.id)
            self._relationship_repo.cleanup_remaining_similarities(merge_author.id)

        # Delete author metadata (cascade will handle related tables)
        self._session.delete(merge_author)
        self._session.flush()


class BothHaveBooksMergeStrategy:
    """Strategy for merging authors where both have books.

    This strategy handles the case where both authors have books,
    requiring book reassignment before deletion.
    """

    def __init__(
        self,
        session: Session,
        calibre_author_service: CalibreAuthorService,
        relationship_repo: AuthorRelationshipRepository,
        data_directory: str | None = None,
    ) -> None:
        """Initialize both have books merge strategy.

        Parameters
        ----------
        session : Session
            Database session.
        calibre_author_service : CalibreAuthorService
            Service for Calibre author operations.
        relationship_repo : AuthorRelationshipRepository
            Repository for relationship operations.
        data_directory : str | None
            Data directory path for file operations.
        """
        self._session = session
        self._calibre_author_service = calibre_author_service
        self._relationship_repo = relationship_repo
        self._data_directory = data_directory

    def can_handle(self, merge_context: MergeContext) -> bool:
        """Check if both authors have books.

        Parameters
        ----------
        merge_context : MergeContext
            Merge context to evaluate.

        Returns
        -------
        bool
            True if both authors have books, False otherwise.
        """
        merge_book_count = self._calibre_author_service.get_book_count(
            merge_context.merge_mapping.calibre_author_id
        )
        return merge_book_count > 0

    def execute(self, merge_context: MergeContext) -> None:
        """Execute both have books merge strategy.

        Parameters
        ----------
        merge_context : MergeContext
            Merge context containing authors and mappings.
        """
        logger.info(
            "Merging authors with books: merge_calibre_id=%s -> keep_calibre_id=%s",
            merge_context.merge_mapping.calibre_author_id,
            merge_context.keep_mapping.calibre_author_id,
        )

        merge_author = merge_context.merge_author
        keep_calibre_id = merge_context.keep_mapping.calibre_author_id
        merge_calibre_id = merge_context.merge_mapping.calibre_author_id

        # Re-map books from merge author to keep author
        self._calibre_author_service.reassign_books(merge_calibre_id, keep_calibre_id)

        # Delete Calibre author (cascade will handle remaining links)
        self._calibre_author_service.delete_author(merge_calibre_id)

        # Delete author mapping
        self._session.delete(merge_context.merge_mapping)
        self._session.flush()

        # Handle AuthorWork records, user photos, user metadata, and similarities
        # before deleting merge_author
        if merge_author.id:
            self._relationship_repo.delete_author_works(merge_author.id)
            self._relationship_repo.delete_author_user_photos(
                merge_author.id, self._data_directory
            )
            self._relationship_repo.delete_author_user_metadata(merge_author.id)
            self._relationship_repo.cleanup_remaining_similarities(merge_author.id)

        # Delete author metadata (cascade will handle related tables)
        self._session.delete(merge_author)
        self._session.flush()


class MergeStrategyFactory:
    """Factory for creating merge strategies.

    Determines which strategy to use based on the merge context.
    """

    def __init__(
        self,
        session: Session,
        calibre_author_service: CalibreAuthorService,
        relationship_repo: AuthorRelationshipRepository,
        data_directory: str | None = None,
    ) -> None:
        """Initialize strategy factory.

        Parameters
        ----------
        session : Session
            Database session.
        calibre_author_service : CalibreAuthorService
            Service for Calibre author operations.
        relationship_repo : AuthorRelationshipRepository
            Repository for relationship operations.
        data_directory : str | None
            Data directory path for file operations.
        """
        self._strategies = [
            ZeroBooksMergeStrategy(
                session, calibre_author_service, relationship_repo, data_directory
            ),
            BothHaveBooksMergeStrategy(
                session, calibre_author_service, relationship_repo, data_directory
            ),
        ]

    def get_strategy(self, merge_context: MergeContext) -> MergeStrategy:
        """Get the appropriate strategy for the merge context.

        Parameters
        ----------
        merge_context : MergeContext
            Merge context to evaluate.

        Returns
        -------
        MergeStrategy
            Strategy that can handle the merge.

        Raises
        ------
        ValueError
            If no strategy can handle the merge context.
        """
        for strategy in self._strategies:
            if strategy.can_handle(merge_context):
                return strategy

        msg = "No strategy found to handle merge context"
        raise ValueError(msg)
