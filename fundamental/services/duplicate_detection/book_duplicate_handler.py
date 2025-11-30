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

"""Book duplicate handler service.

Orchestrates duplicate detection and handling based on library configuration.
Follows SRP, IOC, and SOC principles.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from fundamental.models.config import DuplicateHandling
from fundamental.repositories import CalibreBookRepository
from fundamental.services.duplicate_detection.strategies import (
    DirectTitleAuthorMatchStrategy,
    DuplicateDetectionStrategy,
    FilenameDuplicateStrategy,
    TitleAuthorLevenshteinDuplicateStrategy,
)

if TYPE_CHECKING:
    from fundamental.models.config import Library

logger = logging.getLogger(__name__)


@dataclass
class DuplicateCheckResult:
    """Result of duplicate check.

    Attributes
    ----------
    is_duplicate : bool
        Whether a duplicate was found.
    duplicate_book_id : int | None
        ID of duplicate book if found.
    should_skip : bool
        Whether the book should be skipped (IGNORE mode).
    should_overwrite : bool
        Whether the book should overwrite existing (OVERWRITE mode).
    """

    is_duplicate: bool
    duplicate_book_id: int | None
    should_skip: bool
    should_overwrite: bool


class BookDuplicateHandler:
    """Service for handling book duplicates during upload/ingest.

    Uses Strategy pattern for pluggable detection algorithms.
    Handles IGNORE, OVERWRITE, and CREATE_NEW modes.
    """

    def __init__(
        self,
        strategies: list[DuplicateDetectionStrategy] | None = None,
    ) -> None:
        """Initialize duplicate handler.

        Parameters
        ----------
        strategies : list[DuplicateDetectionStrategy] | None
            List of detection strategies to use. If None, uses default strategies.
        """
        self._strategies = strategies or self._get_default_strategies()

    def _get_default_strategies(self) -> list[DuplicateDetectionStrategy]:
        """Get default detection strategies.

        Returns
        -------
        list[DuplicateDetectionStrategy]
            List of default strategies in priority order.
        """
        return [
            DirectTitleAuthorMatchStrategy(),
            TitleAuthorLevenshteinDuplicateStrategy(min_similarity=0.85),
            FilenameDuplicateStrategy(),
            # FullFileHashDuplicateStrategy(), # - disabled by default (expensive)  # noqa: ERA001
        ]

    def check_duplicate(
        self,
        library: "Library",
        file_path: Path,
        title: str | None,
        author_name: str | None,
        file_format: str,
    ) -> DuplicateCheckResult:
        """Check for duplicate and determine action based on library settings.

        Parameters
        ----------
        library : Library
            Library configuration with duplicate_handling setting.
        file_path : Path
            Path to the book file.
        title : str | None
            Book title.
        author_name : str | None
            Author name.
        file_format : str
            File format extension.

        Returns
        -------
        DuplicateCheckResult
            Result indicating if duplicate found and what action to take.
        """
        duplicate_handling = DuplicateHandling(library.duplicate_handling)

        # Create Calibre repository to get Calibre database session
        calibre_repo = CalibreBookRepository(
            calibre_db_path=library.calibre_db_path,
            calibre_db_file=library.calibre_db_file,
        )

        # Try each strategy until we find a duplicate
        duplicate_book_id = None
        with calibre_repo.get_session() as calibre_session:
            for strategy in self._strategies:
                duplicate_book_id = strategy.find_duplicate(
                    session=calibre_session,
                    library=library,
                    file_path=file_path,
                    title=title,
                    author_name=author_name,
                    file_format=file_format,
                )
                if duplicate_book_id is not None:
                    logger.info(
                        "Duplicate detected: book_id=%d, strategy=%s, handling=%s",
                        duplicate_book_id,
                        strategy.__class__.__name__,
                        duplicate_handling.value,
                    )
                    break

        is_duplicate = duplicate_book_id is not None

        # Determine action based on duplicate_handling setting
        if not is_duplicate:
            return DuplicateCheckResult(
                is_duplicate=False,
                duplicate_book_id=None,
                should_skip=False,
                should_overwrite=False,
            )

        # Duplicate found - determine action
        if duplicate_handling == DuplicateHandling.IGNORE:
            return DuplicateCheckResult(
                is_duplicate=True,
                duplicate_book_id=duplicate_book_id,
                should_skip=True,
                should_overwrite=False,
            )
        if duplicate_handling == DuplicateHandling.OVERWRITE:
            return DuplicateCheckResult(
                is_duplicate=True,
                duplicate_book_id=duplicate_book_id,
                should_skip=False,
                should_overwrite=True,
            )
        # CREATE_NEW
        return DuplicateCheckResult(
            is_duplicate=True,
            duplicate_book_id=duplicate_book_id,
            should_skip=False,
            should_overwrite=False,
        )
