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

"""Duplicate detection strategies for books.

Uses Strategy pattern for pluggable detection algorithms.
Follows SRP, IOC, and SOC principles.
"""

import hashlib
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

from sqlmodel import Session, select

from bookcard.models.core import Author, Book, BookAuthorLink
from bookcard.models.media import Data
from bookcard.repositories.filename_utils import (
    calculate_book_path,
    sanitize_filename,
)
from bookcard.services.library_scanning.matching.exact import normalize_name
from bookcard.services.library_scanning.matching.fuzzy import (
    levenshtein_distance,
)

if TYPE_CHECKING:
    from bookcard.models.config import Library

logger = logging.getLogger(__name__)


class DuplicateDetectionStrategy(ABC):
    """Abstract base class for duplicate detection strategies.

    Follows Strategy pattern for pluggable algorithms.
    Each strategy implements a different method for detecting duplicates.
    """

    @abstractmethod
    def find_duplicate(
        self,
        session: Session,
        library: "Library",
        file_path: Path,
        title: str | None,
        author_name: str | None,
        file_format: str,
    ) -> int | None:
        """Find duplicate book ID if one exists.

        Parameters
        ----------
        session : Session
            Database session.
        library : Library
            Library configuration.
        file_path : Path
            Path to the book file being checked.
        title : str | None
            Book title.
        author_name : str | None
            Author name.
        file_format : str
            File format extension.

        Returns
        -------
        int | None
            Book ID of duplicate if found, None otherwise.
        """


class TitleAuthorLevenshteinDuplicateStrategy(DuplicateDetectionStrategy):
    """Detect duplicates using title and author with Levenshtein distance.

    Compares normalized title+author combination against existing books.
    Uses Levenshtein distance for fuzzy matching.
    """

    def __init__(self, min_similarity: float = 0.85) -> None:
        """Initialize strategy.

        Parameters
        ----------
        min_similarity : float
            Minimum similarity threshold (0.0-1.0, default: 0.85).
        """
        self._min_similarity = min_similarity

    def find_duplicate(
        self,
        session: Session,
        library: "Library",  # noqa: ARG002
        file_path: Path,  # noqa: ARG002
        title: str | None,
        author_name: str | None,
        file_format: str,  # noqa: ARG002
    ) -> int | None:
        """Find duplicate using title+author Levenshtein similarity.

        Parameters
        ----------
        session : Session
            Database session.
        library : Library
            Library configuration (required by interface).
        file_path : Path
            File path (required by interface).
        title : str | None
            Book title.
        author_name : str | None
            Author name.
        file_format : str
            File format (required by interface).

        Returns
        -------
        int | None
            Book ID of duplicate if found, None otherwise.
        """
        if not title:
            return None

        # Normalize title and author
        normalized_title = normalize_name(title)
        normalized_author = normalize_name(author_name) if author_name else ""

        # Build search key: title + author
        search_key = f"{normalized_title} {normalized_author}".strip()

        # Query books with authors
        stmt = (
            select(Book, Author.name.label("author_name"))  # type: ignore[attr-defined]
            .outerjoin(BookAuthorLink, Book.id == BookAuthorLink.book)
            .outerjoin(Author, BookAuthorLink.author == Author.id)
            .where(Book.title != None)  # noqa: E711
        )

        books_with_authors = session.exec(stmt).all()

        # Check each book for similarity
        for book, db_author_name in books_with_authors:
            if not book.title:
                continue

            db_title = normalize_name(book.title)
            db_author = normalize_name(db_author_name) if db_author_name else ""
            db_search_key = f"{db_title} {db_author}".strip()

            # Calculate similarity
            similarity = self._calculate_similarity(search_key, db_search_key)

            if similarity >= self._min_similarity:
                logger.debug(
                    "Duplicate found via title+author Levenshtein: "
                    "book_id=%d, similarity=%.3f, new='%s', existing='%s'",
                    book.id,
                    similarity,
                    search_key,
                    db_search_key,
                )
                return book.id

        return None

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate Levenshtein-based similarity between two strings.

        Parameters
        ----------
        str1 : str
            First string.
        str2 : str
            Second string.

        Returns
        -------
        float
            Similarity score (0.0-1.0).
        """
        if not str1 or not str2:
            return 0.0

        max_len = max(len(str1), len(str2))
        if max_len == 0:
            return 1.0

        distance = levenshtein_distance(str1, str2)
        return 1.0 - (distance / max_len)


class FilenameDuplicateStrategy(DuplicateDetectionStrategy):
    """Detect duplicates by checking if file with same name would exist.

    Uses the same file naming logic as the repository and file_manager
    to determine what the filename would be, then checks if that file
    already exists in the library filesystem.
    """

    def _get_library_path(self, library: "Library") -> Path:
        """Get library root path.

        Parameters
        ----------
        library : Library
            Library configuration.

        Returns
        -------
        Path
            Library root path.
        """
        lib_root = getattr(library, "library_root", None)
        if lib_root:
            return Path(lib_root)
        return Path(library.calibre_db_path)

    def _calculate_expected_file_path(
        self,
        library: "Library",
        title: str,
        author_name: str | None,
        file_format: str,
    ) -> Path | None:
        """Calculate expected file path using same logic as repository and file_manager.

        Uses the same sanitization and path calculation logic as CalibreBookRepository
        and CalibreFileManager to determine where the file would be saved.

        Parameters
        ----------
        library : Library
            Library configuration.
        title : str
            Book title.
        author_name : str | None
            Author name.
        file_format : str
            File format extension.

        Returns
        -------
        Path | None
            Expected file path if title is available, None otherwise.
        """
        if not title:
            return None

        # Use shared utility functions (same as repository)
        book_path_str = calculate_book_path(author_name, title)
        if not book_path_str:
            return None

        # Get library path
        library_path = self._get_library_path(library)

        # Calculate expected file path using same logic as file_manager.save_book_file
        # Pattern: library_path / book_path_str / title_dir.file_format  # noqa: ERA001
        title_dir = sanitize_filename(title)
        book_dir = library_path / book_path_str
        expected_filename = f"{title_dir}.{file_format.lower()}"
        return book_dir / expected_filename

    def find_duplicate(
        self,
        session: Session,
        library: "Library",
        file_path: Path,  # noqa: ARG002
        title: str | None,
        author_name: str | None,
        file_format: str,
    ) -> int | None:
        """Find duplicate by checking if expected file path already exists.

        Uses the same file naming logic as the repository to determine what
        the filename would be, then checks if that file already exists in
        the library filesystem.

        Parameters
        ----------
        session : Session
            Database session.
        library : Library
            Library configuration.
        file_path : Path
            Path to the book file (unused, but required by interface).
        title : str | None
            Book title.
        author_name : str | None
            Author name.
        file_format : str
            File format extension.

        Returns
        -------
        int | None
            Book ID of duplicate if found, None otherwise.
        """
        if not title:
            return None

        # Calculate expected file path using same logic as repository
        expected_path = self._calculate_expected_file_path(
            library, title, author_name, file_format
        )
        if not expected_path:
            return None

        # Check if file exists
        if not expected_path.exists():
            return None

        # File exists - find the book that owns it by matching the path
        # The book.path should match the book_path_str we calculated
        expected_book_path = calculate_book_path(author_name, title)
        if not expected_book_path:
            return None

        stmt = select(Book).where(Book.path == expected_book_path)
        book = session.exec(stmt).first()

        if book:
            logger.debug(
                "Duplicate found via filename: book_id=%d, path='%s', file='%s'",
                book.id,
                expected_book_path,
                expected_path.name,
            )
            return book.id

        return None


class FullFileHashDuplicateStrategy(DuplicateDetectionStrategy):
    """Detect duplicates by computing full file hash.

    Most accurate but slower strategy. Computes SHA-256 hash of entire file.
    """

    def __init__(self, chunk_size: int = 8192) -> None:
        """Initialize strategy.

        Parameters
        ----------
        chunk_size : int
            Chunk size for reading file (default: 8192 bytes).
        """
        self._chunk_size = chunk_size

    def find_duplicate(
        self,
        session: Session,
        library: "Library",
        file_path: Path,
        title: str | None,  # noqa: ARG002
        author_name: str | None,  # noqa: ARG002
        file_format: str,
    ) -> int | None:
        """Find duplicate using full file hash.

        Computes SHA-256 hash of the new file and compares it against
        all existing book files with the same format. This is the most
        accurate but slowest duplicate detection method.

        Parameters
        ----------
        session : Session
            Database session.
        library : Library
            Library configuration.
        file_path : Path
            Path to the book file.
        title : str | None
            Book title (required by interface, unused here).
        author_name : str | None
            Author name (required by interface, unused here).
        file_format : str
            File format extension.

        Returns
        -------
        int | None
            Book ID of duplicate if found, None otherwise.
        """
        if not file_path.exists():
            return None

        try:
            # Compute hash of the new file
            new_file_hash = self._compute_file_hash(file_path)
            logger.debug(
                "Computed hash for new file: %s (first 16 chars: %s)",
                file_path,
                new_file_hash[:16],
            )

            # Get library root path
            library_path = self._get_library_path(library)

            # Query all books with the matching format
            format_upper = file_format.upper()
            stmt = (
                select(Book, Data)
                .join(Data, Book.id == Data.book)  # type: ignore[invalid-argument-type]
                .where(Data.format == format_upper)
            )

            books_with_data = session.exec(stmt).all()

            # Check each book's file hash
            for book, data in books_with_data:
                if not book.id:
                    continue

                # Construct file path for this book's format
                book_file_path = self._get_book_file_path(
                    library_path, book, data, book.id
                )

                if book_file_path is None or not book_file_path.exists():
                    continue

                try:
                    # Compute hash of existing file
                    existing_file_hash = self._compute_file_hash(book_file_path)

                    # Compare hashes
                    if existing_file_hash == new_file_hash:
                        logger.debug(
                            "Duplicate found via full file hash: "
                            "book_id=%d, hash=%s, new_file='%s', existing_file='%s'",
                            book.id,
                            new_file_hash[:16],
                            file_path,
                            book_file_path,
                        )
                        return book.id
                except OSError as exc:
                    logger.warning(
                        "Failed to compute hash for book_id=%d, file='%s': %s",
                        book.id,
                        book_file_path,
                        exc,
                    )
                    continue

        except OSError as exc:
            logger.warning("Failed to compute file hash for '%s': %s", file_path, exc)
            return None

        return None

    def _get_library_path(self, library: "Library") -> Path:
        """Get library root path.

        Parameters
        ----------
        library : Library
            Library configuration.

        Returns
        -------
        Path
            Library root path.
        """
        lib_root = getattr(library, "library_root", None)
        if lib_root:
            return Path(lib_root)
        library_db_path = Path(library.calibre_db_path)
        if library_db_path.is_dir():
            return library_db_path
        return library_db_path.parent

    def _get_book_file_path(
        self,
        library_path: Path,
        book: Book,
        data: Data,
        book_id: int,
    ) -> Path | None:
        """Get file path for a book format.

        Tries multiple filename patterns to locate the actual file.

        Parameters
        ----------
        library_path : Path
            Library root path.
        book : Book
            Book model.
        data : Data
            Data record for the format.
        book_id : int
            Book ID.

        Returns
        -------
        Path | None
            Path to the book file if found, None otherwise.
        """
        book_dir = library_path / book.path

        # Primary path: {name}.{format}
        file_name = data.name or str(book_id)
        primary = book_dir / f"{file_name}.{data.format.lower()}"
        if primary.exists():
            return primary

        # Alternative path: {book_id}.{format}
        alt = book_dir / f"{book_id}.{data.format.lower()}"
        if alt.exists():
            return alt

        return None

    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA-256 hash of file.

        Parameters
        ----------
        file_path : Path
            Path to file.

        Returns
        -------
        str
            Hexadecimal hash string.
        """
        sha256 = hashlib.sha256()
        with file_path.open("rb") as f:
            while chunk := f.read(self._chunk_size):
                sha256.update(chunk)
        return sha256.hexdigest()


class DirectTitleAuthorMatchStrategy(DuplicateDetectionStrategy):
    """Detect duplicates using direct database queries for title and author.

    Fastest strategy that uses SQL LIKE queries to find exact or partial
    matches in the database. More efficient than loading all books into memory.
    """

    def find_duplicate(
        self,
        session: Session,
        library: "Library",  # noqa: ARG002
        file_path: Path,  # noqa: ARG002
        title: str | None,
        author_name: str | None,
        file_format: str,  # noqa: ARG002
    ) -> int | None:
        """Find duplicate using direct database title and author matching.

        Uses SQL LIKE queries (case-insensitive) to find books with matching
        title and author. This is the fastest strategy as it leverages
        database indexes and avoids loading all books into memory.

        Parameters
        ----------
        session : Session
            Database session.
        library : Library
            Library configuration (required by interface, unused here).
        file_path : Path
            File path (required by interface, unused here).
        title : str | None
            Book title to match.
        author_name : str | None
            Author name to match.
        file_format : str
            File format (required by interface, unused here).

        Returns
        -------
        int | None
            Book ID of duplicate if found, None otherwise.
        """
        if not title:
            return None

        # Build query with joins
        stmt = (
            select(Book.id)
            .join(BookAuthorLink, Book.id == BookAuthorLink.book)  # type: ignore[invalid-argument-type]
            .join(Author, BookAuthorLink.author == Author.id)  # type: ignore[invalid-argument-type]
            .where(Book.title.isnot(None))  # type: ignore[attr-defined]
            .distinct()
        )

        # Add title match (case-insensitive)
        title_pattern = f"%{title}%"
        stmt = stmt.where(Book.title.ilike(title_pattern))  # type: ignore[attr-defined]

        # Add author match if provided (case-insensitive)
        if author_name:
            author_pattern = f"%{author_name}%"
            stmt = stmt.where(Author.name.ilike(author_pattern))  # type: ignore[attr-defined]

        # Get first match
        result = session.exec(stmt).first()

        if result:
            logger.debug(
                "Duplicate found via direct title/author match: "
                "book_id=%d, title='%s', author='%s'",
                result,
                title,
                author_name or "N/A",
            )
            return result

        return None
