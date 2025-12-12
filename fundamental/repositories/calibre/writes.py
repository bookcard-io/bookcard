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

"""Write operations for the Calibre book repository."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlmodel import Session, select

from fundamental.models.core import (
    Author,
    Book,
    BookAuthorLink,
    Comment,
)
from fundamental.models.media import Data

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path
    from typing import NoReturn

    from fundamental.repositories.interfaces import (
        IBookMetadataService,
        IBookRelationshipManager,
        IFileManager,
        ISessionManager,
    )
    from fundamental.repositories.models import BookWithFullRelations
    from fundamental.services.book_metadata import BookMetadata

    from .pathing import BookPathService
    from .retry import SQLiteRetryPolicy

logger = logging.getLogger(__name__)


class BookWriteOperations:
    """Write operations for `CalibreBookRepository` (add/update core book records)."""

    def __init__(
        self,
        *,
        session_manager: ISessionManager,
        retry_policy: SQLiteRetryPolicy,
        file_manager: IFileManager,
        relationship_manager: IBookRelationshipManager,
        metadata_service: IBookMetadataService,
        pathing: BookPathService,
        calibre_db_path: Path,
        get_book_full: Callable[[int], BookWithFullRelations | None],
    ) -> None:
        self._session_manager = session_manager
        self._retry = retry_policy
        self._file_manager = file_manager
        self._relationship_manager = relationship_manager
        self._metadata_service = metadata_service
        self._pathing = pathing
        self._calibre_db_path = calibre_db_path
        self._get_book_full = get_book_full

    def add_book(
        self,
        *,
        file_path: Path,
        file_format: str,
        title: str | None = None,
        author_name: str | None = None,
        pubdate: datetime | None = None,
        library_path: Path | None = None,
    ) -> int:
        """Add a book directly to the Calibre database.

        Parameters
        ----------
        file_path : Path
            Source file path.
        file_format : str
            File format extension.
        title : str | None
            Optional title override.
        author_name : str | None
            Optional author override.
        pubdate : datetime | None
            Optional pubdate override.
        library_path : Path | None
            Optional library root path override.

        Returns
        -------
        int
            Newly created book id.
        """
        if not file_path.exists():
            msg = f"File not found: {file_path}"
            raise ValueError(msg)

        if library_path is None:
            library_path = self._get_library_path()

        metadata, cover_data = self._metadata_service.extract_metadata(
            file_path, file_format
        )
        normalized_title, normalized_author = self._pathing.normalize_title_and_author(
            title=title, author_name=author_name, metadata=metadata
        )

        if pubdate is None:
            pubdate = getattr(metadata, "pubdate", None)

        with self._session_manager.get_session() as session:
            book_path_str, title_dir, file_format_upper = (
                self._pathing.prepare_book_path_and_format(
                    session=session,
                    title=normalized_title,
                    author_name=normalized_author,
                    file_format=file_format,
                )
            )
            file_size = file_path.stat().st_size
            db_book, book_id = self._create_book_database_records(
                session=session,
                title=normalized_title,
                author_name=normalized_author,
                book_path_str=book_path_str,
                metadata=metadata,
                file_format_upper=file_format_upper,
                title_dir=title_dir,
                file_size=file_size,
                pubdate=pubdate,
            )

            self._save_book_files_and_cover(
                session=session,
                db_book=db_book,
                file_path=file_path,
                library_path=library_path,
                book_path_str=book_path_str,
                title_dir=title_dir,
                file_format=file_format,
                cover_data=cover_data,
            )

            self._retry.commit(session)
            return book_id

    def update_book(
        self,
        *,
        book_id: int,
        title: str | None = None,
        pubdate: datetime | None = None,
        author_names: list[str] | None = None,
        series_name: str | None = None,
        series_id: int | None = None,
        series_index: float | None = None,
        tag_names: list[str] | None = None,
        identifiers: list[dict[str, str]] | None = None,
        description: str | None = None,
        publisher_name: str | None = None,
        publisher_id: int | None = None,
        language_codes: list[str] | None = None,
        language_ids: list[int] | None = None,
        rating_value: int | None = None,
        rating_id: int | None = None,
        author_sort: str | None = None,
        title_sort: str | None = None,
    ) -> BookWithFullRelations | None:
        """Update book metadata and return the updated record."""
        with self._session_manager.get_session() as session:
            with session.no_autoflush:
                book = session.exec(select(Book).where(Book.id == book_id)).first()
                if book is None:
                    return None

                old_path = book.path
                existing_title = book.title
                existing_authors = self._fetch_author_names(session, book_id=book_id)

                self._update_book_relationships(
                    session=session,
                    book_id=book_id,
                    author_names=author_names,
                    series_name=series_name,
                    series_id=series_id,
                    tag_names=tag_names,
                    identifiers=identifiers,
                    description=description,
                    publisher_name=publisher_name,
                    publisher_id=publisher_id,
                    language_codes=language_codes,
                    language_ids=language_ids,
                    rating_value=rating_value,
                    rating_id=rating_id,
                )

                updated_authors = self._fetch_author_names(session, book_id=book_id)
                final_authors = (
                    updated_authors if author_names is not None else existing_authors
                )
                final_title = title if title is not None else existing_title
                new_path = self._pathing.calculate_book_path(
                    author_names=final_authors,
                    title=final_title,
                )

                if new_path and new_path != old_path:
                    book.path = new_path
                    library_root = self._get_library_path()
                    try:
                        self._file_manager.move_book_directory(
                            old_book_path=old_path,
                            new_book_path=new_path,
                            library_path=library_root,
                        )
                    except OSError:
                        book.path = old_path
                        raise

                self._update_book_fields(
                    book=book,
                    title=title,
                    pubdate=pubdate,
                    series_index=series_index,
                    author_sort=author_sort,
                    title_sort=title_sort,
                )

            self._retry.commit(session)
            session.refresh(book)

        # Read back in a fresh session (simpler, consistent with existing code)
        return self._get_book_full(book_id)

    def _update_book_relationships(
        self,
        *,
        session: Session,
        book_id: int,
        author_names: list[str] | None = None,
        series_name: str | None = None,
        series_id: int | None = None,
        tag_names: list[str] | None = None,
        identifiers: list[dict[str, str]] | None = None,
        description: str | None = None,
        publisher_name: str | None = None,
        publisher_id: int | None = None,
        language_codes: list[str] | None = None,
        language_ids: list[int] | None = None,
        rating_value: int | None = None,
        rating_id: int | None = None,
    ) -> None:
        if author_names is not None:
            self._relationship_manager.update_authors(session, book_id, author_names)

        if series_name is not None or series_id is not None:
            self._relationship_manager.update_series(
                session, book_id, series_name, series_id
            )

        if tag_names is not None:
            self._relationship_manager.update_tags(session, book_id, tag_names)

        if identifiers is not None:
            self._relationship_manager.update_identifiers(session, book_id, identifiers)

        if description is not None:
            comment = session.exec(
                select(Comment).where(Comment.book == book_id)
            ).first()
            if comment is None:
                session.add(Comment(book=book_id, text=description))
            else:
                comment.text = description

        if publisher_id is not None or publisher_name is not None:
            self._relationship_manager.update_publisher(
                session, book_id, publisher_name, publisher_id
            )

        if language_ids is not None or language_codes is not None:
            self._relationship_manager.update_languages(
                session,
                book_id,
                language_codes=language_codes,
                language_ids=language_ids,
            )

        if rating_id is not None or rating_value is not None:
            self._relationship_manager.update_rating(
                session, book_id, rating_value, rating_id
            )

    def _update_book_fields(
        self,
        *,
        book: Book,
        title: str | None = None,
        pubdate: datetime | None = None,
        series_index: float | None = None,
        author_sort: str | None = None,
        title_sort: str | None = None,
    ) -> None:
        if title is not None:
            book.title = title
        if pubdate is not None:
            book.pubdate = pubdate
        if series_index is not None:
            book.series_index = series_index
        if author_sort is not None:
            book.author_sort = author_sort
        if title_sort is not None:
            book.sort = title_sort
        book.last_modified = datetime.now(UTC)

    def _get_or_create_author(self, *, session: Session, author_name: str) -> Author:
        author = session.exec(select(Author).where(Author.name == author_name)).first()
        if author is None:
            author = Author(name=author_name, sort=author_name)
            session.add(author)
            self._retry.flush(session)
        if author.id is None:
            self._raise_author_creation_failed()
        return author

    @staticmethod
    def _raise_author_creation_failed() -> NoReturn:
        msg = "Failed to create author"
        raise ValueError(msg)

    def _create_book_record(
        self,
        *,
        session: Session,
        title: str,
        author_name: str,
        book_path_str: str,
        pubdate: datetime | None = None,
        series_index: float | None = None,
    ) -> Book:
        now = datetime.now(UTC)
        db_book = Book(
            title=title,
            sort=title,
            author_sort=author_name,
            timestamp=now,
            pubdate=pubdate,
            series_index=series_index if series_index is not None else 1.0,
            flags=1,
            uuid=str(uuid4()),
            path=book_path_str,
            has_cover=False,
            last_modified=now,
        )
        session.add(db_book)
        self._retry.flush(session)
        if db_book.id is None:
            self._raise_book_creation_failed()
        return db_book

    @staticmethod
    def _raise_book_creation_failed() -> NoReturn:
        msg = "Failed to create book"
        raise ValueError(msg)

    def _create_book_database_records(
        self,
        *,
        session: Session,
        title: str,
        author_name: str,
        book_path_str: str,
        metadata: BookMetadata,
        file_format_upper: str,
        title_dir: str,
        file_size: int,
        pubdate: datetime | None = None,
    ) -> tuple[Book, int]:
        author = self._get_or_create_author(session=session, author_name=author_name)
        sort_title = metadata.sort_title or title
        final_pubdate = pubdate if pubdate is not None else metadata.pubdate

        db_book = self._create_book_record(
            session=session,
            title=title,
            author_name=author_name,
            book_path_str=book_path_str,
            pubdate=final_pubdate,
            series_index=metadata.series_index,
        )

        if metadata.sort_title and db_book.sort != sort_title:
            db_book.sort = sort_title

        if db_book.id is None:
            msg = "Book ID is None after creation"
            raise ValueError(msg)
        book_id = db_book.id

        session.add(BookAuthorLink(book=book_id, author=author.id))
        self._relationship_manager.add_metadata(session, book_id, metadata)
        session.add(
            Data(
                book=book_id,
                format=file_format_upper,
                uncompressed_size=file_size,
                name=title_dir,
            )
        )
        return db_book, book_id

    def _save_book_files_and_cover(
        self,
        *,
        session: Session,
        db_book: Book,
        file_path: Path,
        library_path: Path,
        book_path_str: str,
        title_dir: str,
        file_format: str,
        cover_data: bytes | None,
    ) -> None:
        self._file_manager.save_book_file(
            file_path, library_path, book_path_str, title_dir, file_format
        )
        if cover_data:
            cover_saved = self._file_manager.save_book_cover(
                cover_data, library_path, book_path_str
            )
            if cover_saved:
                db_book.has_cover = True
                session.add(db_book)

    def _fetch_author_names(self, session: Session, *, book_id: int) -> list[str]:
        stmt = (
            select(Author.name)
            .join(BookAuthorLink, Author.id == BookAuthorLink.author)
            .where(BookAuthorLink.book == book_id)
            .order_by(BookAuthorLink.id)
        )
        rows = session.exec(stmt).all()
        return [row[0] if isinstance(row, tuple) else row for row in rows]

    def _get_library_path(self) -> Path:
        if self._calibre_db_path.is_dir():
            return self._calibre_db_path
        return self._calibre_db_path.parent
