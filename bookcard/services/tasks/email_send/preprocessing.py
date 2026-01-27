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

"""Preprocessing pipeline for email send task.

Implements Strategy pattern and Chain of Responsibility to make
preprocessing extensible (Open/Closed Principle).
"""

import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass

from sqlmodel import Session, select

from bookcard.models.config import EPUBFixerConfig, Library
from bookcard.models.core import Book
from bookcard.models.media import Data
from bookcard.repositories import BookWithFullRelations
from bookcard.repositories.calibre_book_repository import CalibreBookRepository
from bookcard.services.epub_fixer_service import EPUBFixerService
from bookcard.services.metadata_enforcement_trigger_service import (
    MetadataEnforcementTriggerService,
)
from bookcard.services.tasks.post_processors import LibraryPathResolver

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PreprocessingContext:
    """Context for preprocessing operations.

    Bundles all parameters needed for preprocessing steps.
    """

    session: Session
    library: Library
    book_with_rels: BookWithFullRelations
    book_id: int
    user_id: int
    resolved_format: str | None
    check_cancellation: Callable[[], None]


class PreprocessingStep(ABC):
    """Abstract base class for preprocessing steps.

    Follows Strategy pattern to allow extensible preprocessing pipeline.
    """

    is_critical: bool = False
    """Whether this step is critical (failures should abort the task)."""

    @abstractmethod
    def should_run(self, context: PreprocessingContext) -> bool:
        """Check if this step should run.

        Parameters
        ----------
        context : PreprocessingContext
            Preprocessing context.

        Returns
        -------
        bool
            True if step should run, False otherwise.
        """

    @abstractmethod
    def process(self, context: PreprocessingContext) -> None:
        """Execute the preprocessing step.

        Parameters
        ----------
        context : PreprocessingContext
            Preprocessing context.

        Raises
        ------
        Exception
            If step fails and is critical.
        """

    def safe_execute(self, context: PreprocessingContext) -> None:
        """Execute step with error handling.

        Parameters
        ----------
        context : PreprocessingContext
            Preprocessing context.

        Raises
        ------
        Exception
            If step fails and is critical.
        """
        if not self.should_run(context):
            return

        try:
            self.process(context)
        except Exception:
            logger.exception("%s failed", self.__class__.__name__)
            if self.is_critical:
                raise


class EPUBFixStep(PreprocessingStep):
    """Preprocessing step for EPUB fixing."""

    def should_run(self, context: PreprocessingContext) -> bool:
        """Check if EPUB fix should run.

        Parameters
        ----------
        context : PreprocessingContext
            Preprocessing context.

        Returns
        -------
        bool
            True if format is EPUB and fixer is enabled.
        """
        if not context.resolved_format or context.resolved_format.upper() != "EPUB":
            return False

        # Check EPUB fixer is enabled globally
        stmt = select(EPUBFixerConfig).limit(1)
        epub_config = context.session.exec(stmt).first()
        return epub_config is not None and epub_config.enabled

    def process(self, context: PreprocessingContext) -> None:
        """Run EPUB fix.

        Parameters
        ----------
        context : PreprocessingContext
            Preprocessing context.
        """
        # Resolve EPUB file path
        calibre_repo = CalibreBookRepository(str(context.library.calibre_db_path))
        with calibre_repo.get_session() as calibre_session:
            stmt = (
                select(Book, Data)
                .join(Data)
                .where(Book.id == context.book_id)
                .where(Data.format == "EPUB")
            )
            result = calibre_session.exec(stmt).first()

        if not result:
            logger.debug("EPUB format not found for book %d", context.book_id)
            return

        book, data = result

        path_resolver = LibraryPathResolver(context.library)
        file_path = path_resolver.get_book_file_path(book, data)

        if not file_path:
            logger.warning("EPUB file path not found for book %d", context.book_id)
            return

        # Execute fix
        logger.info("Running EPUB fix for book %d", context.book_id)
        fixer_service = EPUBFixerService(context.session)
        fix_run = fixer_service.process_epub_file(
            file_path=file_path,
            book_id=context.book_id,
            book_title=context.book_with_rels.book.title,
            user_id=context.user_id,
            library_id=context.library.id,
            manually_triggered=False,
        )

        if fix_run.id:
            logger.info("EPUB fix completed for book %d", context.book_id)


class MetadataEnforcementStep(PreprocessingStep):
    """Preprocessing step for metadata enforcement."""

    def should_run(self, context: PreprocessingContext) -> bool:
        """Check if metadata enforcement should run.

        Parameters
        ----------
        context : PreprocessingContext
            Preprocessing context.

        Returns
        -------
        bool
            True if metadata enforcement is enabled for the library.
        """
        return context.library.auto_metadata_enforcement

    def process(self, context: PreprocessingContext) -> None:
        """Run metadata enforcement.

        Parameters
        ----------
        context : PreprocessingContext
            Preprocessing context.
        """
        logger.info("Running metadata enforcement for book %d", context.book_id)
        trigger_service = MetadataEnforcementTriggerService(context.session)
        trigger_service.trigger_enforcement_if_enabled(
            book_id=context.book_id,
            book_with_rels=context.book_with_rels,
            user_id=context.user_id,
        )


class PreprocessingPipeline:
    """Pipeline for executing preprocessing steps.

    Follows Chain of Responsibility pattern to make pipeline extensible.
    """

    def __init__(self) -> None:
        """Initialize empty pipeline."""
        self.steps: list[PreprocessingStep] = []

    def add_step(self, step: PreprocessingStep) -> "PreprocessingPipeline":
        """Add a preprocessing step to the pipeline.

        Parameters
        ----------
        step : PreprocessingStep
            Step to add.

        Returns
        -------
        PreprocessingPipeline
            Self for method chaining.
        """
        self.steps.append(step)
        return self

    def execute(self, context: PreprocessingContext) -> None:
        """Execute all steps in the pipeline.

        Parameters
        ----------
        context : PreprocessingContext
            Preprocessing context.

        Raises
        ------
        Exception
            If a critical step fails.
        """
        for step in self.steps:
            context.check_cancellation()
            step.safe_execute(context)

    @classmethod
    def default(cls) -> "PreprocessingPipeline":
        """Create default preprocessing pipeline.

        Returns
        -------
        PreprocessingPipeline
            Pipeline with EPUB fix and metadata enforcement steps.
        """
        return cls().add_step(EPUBFixStep()).add_step(MetadataEnforcementStep())
