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

"""Book path and filename helpers for Calibre repositories."""

from __future__ import annotations

import logging
import uuid

from sqlmodel import Session, select

from fundamental.models.core import Book
from fundamental.repositories.filename_utils import (
    calculate_book_path,
    sanitize_filename,
)

logger = logging.getLogger(__name__)


class BookPathService:
    """Book path/filename decisions (normalized title/author, uniqueness, sanitization)."""

    def normalize_title_and_author(
        self,
        *,
        title: str | None,
        author_name: str | None,
        metadata: object,
    ) -> tuple[str, str]:
        """Normalize title and author with fallbacks.

        Parameters
        ----------
        title : str | None
            Provided title.
        author_name : str | None
            Provided author name.
        metadata : object
            Metadata object with title/author attributes.

        Returns
        -------
        tuple[str, str]
            Normalized `(title, author_name)` tuple.
        """
        if title is None:
            title = getattr(metadata, "title", None)
        if not title or title.strip() == "":
            title = "Unknown"

        if author_name is None or author_name.strip() == "":
            author_name = getattr(metadata, "author", None)
        if not author_name or author_name.strip() == "":
            author_name = "Unknown"

        return title, author_name

    def sanitize_title_dir(self, title: str, *, max_length: int = 96) -> str:
        """Sanitize a title into a safe directory name."""
        return sanitize_filename(title, max_length)

    def calculate_book_path(
        self, *, author_names: list[str] | None, title: str | None
    ) -> str | None:
        """Calculate book path from author names and title."""
        if not author_names or not title:
            return None
        author_name = author_names[0] if author_names else "Unknown"
        return calculate_book_path(author_name, title)

    def prepare_book_path_and_format(
        self,
        *,
        session: Session | None,
        title: str,
        author_name: str,
        file_format: str,
    ) -> tuple[str, str, str]:
        """Prepare book path, title directory, and normalized format.

        Parameters
        ----------
        session : Session | None
            Optional session used to ensure the generated path is unique.
        title : str
            Book title.
        author_name : str
            Author name.
        file_format : str
            File format extension.

        Returns
        -------
        tuple[str, str, str]
            Tuple `(book_path_str, title_dir, file_format_upper)`.

        Raises
        ------
        ValueError
            If book path cannot be calculated.
        """
        file_format_upper = file_format.upper().lstrip(".")
        base_book_path_str = calculate_book_path(author_name, title)
        if not base_book_path_str:
            msg = "Cannot calculate book path: title is required"
            raise ValueError(msg)

        book_path_str = base_book_path_str
        unique_title = title
        if session is not None:
            book_path_str, unique_title = self.make_path_unique(
                session=session,
                base_path=base_book_path_str,
                base_title=title,
                author_name=author_name,
            )

        title_dir = self.sanitize_title_dir(unique_title)
        return book_path_str, title_dir, file_format_upper

    def make_path_unique(
        self,
        *,
        session: Session,
        base_path: str,
        base_title: str,
        author_name: str,
    ) -> tuple[str, str]:
        """Make book path unique by appending a number if it already exists."""
        stmt = select(Book).where(Book.path == base_path)
        existing_book = session.exec(stmt).first()
        if existing_book is None:
            return base_path, base_title

        counter = 2
        while True:
            unique_title = f"{base_title} ({counter})"
            unique_path = (
                calculate_book_path(author_name, unique_title)
                or f"{base_path} ({counter})"
            )

            stmt = select(Book).where(Book.path == unique_path)
            if session.exec(stmt).first() is None:
                logger.debug(
                    "Made path unique: %s -> %s (title: %s -> %s)",
                    base_path,
                    unique_path,
                    base_title,
                    unique_title,
                )
                return unique_path, unique_title

            counter += 1
            if counter > 1000:
                logger.warning(
                    "Could not find unique path after 1000 attempts for: %s",
                    base_path,
                )
                unique_suffix = str(uuid.uuid4())[:8]
                unique_title = f"{base_title} ({unique_suffix})"
                unique_path = (
                    calculate_book_path(author_name, unique_title)
                    or f"{base_path} ({unique_suffix})"
                )
                return unique_path, unique_title
