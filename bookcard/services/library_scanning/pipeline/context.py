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

"""Pipeline context for sharing state between stages."""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from sqlmodel import Session

from bookcard.models.config import Library
from bookcard.models.core import Author, Book
from bookcard.services.library_scanning.data_sources.base import BaseDataSource
from bookcard.services.library_scanning.matching.types import MatchResult


@dataclass
class PipelineContext:
    """Context shared between pipeline stages.

    Attributes
    ----------
    library_id : int
        ID of the library being scanned.
    library : Library
        Library configuration.
    session : Session
        Database session for Bookcard database.
    data_source : BaseDataSource
        External data source for matching and ingestion.
    progress_callback : Callable[[float], None] | None
        Optional callback for reporting progress (0.0 to 1.0).
    cancelled : bool
        Flag to check if pipeline has been cancelled.
    """

    library_id: int
    library: Library
    session: Session
    data_source: BaseDataSource
    progress_callback: Callable[[float, dict[str, Any] | None], None] | None = None
    cancelled: bool = False
    target_author_metadata_id: int | None = None
    single_author_mode: bool = False

    # Stage results (populated as stages execute)
    crawled_authors: list[Author] = field(default_factory=list)
    crawled_books: list[Book] = field(default_factory=list)
    match_results: list[MatchResult] = field(default_factory=list)
    unmatched_authors: list[Author] = field(default_factory=list)

    def check_cancelled(self) -> bool:
        """Check if pipeline has been cancelled.

        Returns
        -------
        bool
            True if cancelled, False otherwise.
        """
        return self.cancelled

    def update_progress(
        self,
        progress: float,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Update progress via callback if available.

        Parameters
        ----------
        progress : float
            Progress value between 0.0 and 1.0.
        metadata : dict[str, Any] | None
            Optional metadata (stage, current_item, counts, etc.).
        """
        if self.progress_callback:
            self.progress_callback(progress, metadata)
