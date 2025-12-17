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

"""Crawl stage for extracting authors and books from Calibre metadata.db."""

import logging

from sqlmodel import select

from bookcard.models.core import Author, Book, BookAuthorLink
from bookcard.repositories import CalibreBookRepository
from bookcard.services.library_scanning.pipeline.base import (
    PipelineStage,
    StageResult,
)
from bookcard.services.library_scanning.pipeline.context import PipelineContext

logger = logging.getLogger(__name__)


class CrawlStage(PipelineStage):
    """Stage that crawls Calibre metadata.db for authors and books.

    Extracts all authors and books from the Calibre library.
    Tracks new/existing/updated entities via last_modified timestamps.
    """

    def __init__(self, author_limit: int | None = None) -> None:
        """Initialize crawl stage.

        Parameters
        ----------
        author_limit : int | None
            Maximum number of authors to process (None = no limit).
            Used for testing to limit processing.
        """
        self._progress = 0.0
        self._total_authors = 0
        self._total_books = 0
        self._processed_authors = 0
        self._processed_books = 0
        self._author_limit = author_limit

    @property
    def name(self) -> str:
        """Get the name of this pipeline stage.

        Returns
        -------
        str
            Stage name.
        """
        return "crawl"

    def get_progress(self) -> float:
        """Get current progress of this stage.

        Returns
        -------
        float
            Progress value between 0.0 and 1.0.
        """
        return self._progress

    def execute(self, context: PipelineContext) -> StageResult:
        """Execute the crawl stage.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with library configuration.

        Returns
        -------
        StageResult
            Result with crawled authors and books.
        """
        if context.check_cancelled():
            return StageResult(success=False, message="Crawl cancelled")

        logger.info(
            "Starting crawl stage for library %d (path: %s)",
            context.library_id,
            context.library.calibre_db_path,
        )

        try:
            # Create Calibre repository
            calibre_repo = CalibreBookRepository(
                calibre_db_path=context.library.calibre_db_path,
                calibre_db_file=context.library.calibre_db_file,
            )

            context.update_progress(
                0.1,
                {
                    "current_stage": {
                        "name": "crawl",
                        "status": "in_progress",
                        "message": "Connecting to Calibre database...",
                    },
                },
            )

            # Get all authors from Calibre database
            with calibre_repo.get_session() as calibre_session:
                logger.debug("Fetching authors from Calibre database...")
                authors_stmt = select(Author)
                authors_result = calibre_session.exec(authors_stmt)
                authors = list(authors_result.all())

                # Apply author limit if set (for testing)
                if self._author_limit is not None and self._author_limit > 0:
                    authors = authors[: self._author_limit]
                    logger.info(
                        "Author limit applied: processing %d authors (limited from original count)",
                        len(authors),
                    )

                context.crawled_authors = authors
                self._total_authors = len(authors)
                self._processed_authors = len(authors)

                logger.debug(
                    "Found %d authors in Calibre database", self._total_authors
                )
                context.update_progress(
                    0.3,
                    {
                        "current_stage": {
                            "name": "crawl",
                            "status": "in_progress",
                            "message": f"Found {self._total_authors} authors, fetching books...",
                            "authors_found": self._total_authors,
                        },
                    },
                )

                # Get all books from Calibre database
                logger.debug("Fetching books from Calibre database...")
                books_stmt = select(Book)
                books_result = calibre_session.exec(books_stmt)
                books = list(books_result.all())

                context.crawled_books = books
                self._total_books = len(books)
                self._processed_books = len(books)

                logger.debug("Found %d books in Calibre database", self._total_books)
                context.update_progress(
                    0.5,
                    {
                        "current_stage": {
                            "name": "crawl",
                            "status": "in_progress",
                            "message": f"Found {self._total_books} books, fetching relationships...",
                            "authors_found": self._total_authors,
                            "books_found": self._total_books,
                        },
                    },
                )

                # Get book-author links to understand relationships
                # This will be used in LinkStage
                logger.debug("Fetching book-author relationships...")
                links_stmt = select(BookAuthorLink)
                links_result = calibre_session.exec(links_stmt)
                book_author_links = list(links_result.all())

                logger.debug(
                    "Found %d book-author relationships", len(book_author_links)
                )
                context.update_progress(
                    1.0,
                    {
                        "current_stage": {
                            "name": "crawl",
                            "status": "complete",
                            "message": f"Crawled {self._total_authors} authors and {self._total_books} books",
                            "authors_found": self._total_authors,
                            "books_found": self._total_books,
                        },
                    },
                )
                self._progress = 1.0

                stats = {
                    "authors_crawled": self._total_authors,
                    "books_crawled": self._total_books,
                    "book_author_links": len(book_author_links),
                }

                logger.info(
                    "Crawled %d authors and %d books from library %d",
                    self._total_authors,
                    self._total_books,
                    context.library_id,
                )

                return StageResult(
                    success=True,
                    message=f"Crawled {self._total_authors} authors and {self._total_books} books",
                    stats=stats,
                )

        except Exception as e:
            logger.exception("Error in crawl stage")
            return StageResult(
                success=False,
                message=f"Crawl failed: {e}",
            )
