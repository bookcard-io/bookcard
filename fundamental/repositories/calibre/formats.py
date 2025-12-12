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

"""Format (Data table + filesystem) operations for the Calibre book repository."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast

from sqlmodel import Session, select

from fundamental.models.core import Book
from fundamental.models.media import Data

if TYPE_CHECKING:
    from pathlib import Path
    from typing import NoReturn

    from fundamental.repositories.interfaces import IFileManager, ISessionManager

    from .pathing import BookPathService
    from .retry import SQLiteRetryPolicy

logger = logging.getLogger(__name__)


class BookFormatOperations:
    """Add/delete format files and associated Data records."""

    def __init__(
        self,
        *,
        session_manager: ISessionManager,
        retry_policy: SQLiteRetryPolicy,
        file_manager: IFileManager,
        pathing: BookPathService,
        calibre_db_path: Path,
    ) -> None:
        self._session_manager = session_manager
        self._retry = retry_policy
        self._file_manager = file_manager
        self._pathing = pathing
        self._calibre_db_path = calibre_db_path

    def add_format(
        self,
        *,
        book_id: int,
        file_path: Path,
        file_format: str,
        replace: bool = False,
    ) -> None:
        """Add a format to an existing book.

        Parameters
        ----------
        book_id : int
            Book ID.
        file_path : Path
            Path to the file to add.
        file_format : str
            Format extension (e.g. 'epub').
        replace : bool
            Whether to replace existing format if it exists.
        """
        if not file_path.exists():
            msg = f"File not found: {file_path}"
            raise ValueError(msg)

        file_format_upper = file_format.upper().lstrip(".")

        with self._session_manager.get_session() as session:
            book: Book | None = session.exec(
                select(Book).where(Book.id == book_id)
            ).first()
            if book is None:
                self._raise_book_not_found()
            db_book = cast("Book", book)

            existing_data = session.exec(select(Data).where(Data.book == book_id)).all()
            existing_format_record = next(
                (d for d in existing_data if d.format == file_format_upper), None
            )
            if existing_format_record is not None and not replace:
                msg = f"Format {file_format_upper} already exists for book {book_id}"
                raise FileExistsError(msg)

            title_dir = (
                existing_data[0].name
                if existing_data
                else self._pathing.sanitize_title_dir(db_book.title)
            )

            library_path = self._get_library_path()
            self._file_manager.save_book_file(
                file_path,
                library_path,
                db_book.path,
                title_dir,
                file_format_upper,
            )

            file_size = file_path.stat().st_size
            if existing_format_record is not None:
                existing_format_record.uncompressed_size = file_size
                existing_format_record.name = title_dir
                session.add(existing_format_record)
            else:
                session.add(
                    Data(
                        book=book_id,
                        format=file_format_upper,
                        uncompressed_size=file_size,
                        name=title_dir,
                    )
                )

            db_book.last_modified = datetime.now(UTC)
            session.add(db_book)
            self._retry.commit(session)

    def delete_format(
        self,
        *,
        book_id: int,
        file_format: str,
        delete_file_from_drive: bool = True,
    ) -> None:
        """Delete a format from an existing book."""
        file_format_upper = file_format.upper().lstrip(".")

        with self._session_manager.get_session() as session:
            book: Book | None = session.exec(
                select(Book).where(Book.id == book_id)
            ).first()
            if book is None:
                self._raise_book_not_found()
            db_book = cast("Book", book)

            format_record = self._find_format_record(
                session=session, book_id=book_id, file_format_upper=file_format_upper
            )

            if delete_file_from_drive:
                self._delete_format_file(
                    book=db_book,
                    format_record=format_record,
                    file_format_upper=file_format_upper,
                )

            session.delete(format_record)
            db_book.last_modified = datetime.now(UTC)
            session.add(db_book)
            self._retry.commit(session)

    @staticmethod
    def _raise_book_not_found() -> NoReturn:
        msg = "book_not_found"
        raise ValueError(msg)

    def _find_format_record(
        self,
        *,
        session: Session,
        book_id: int,
        file_format_upper: str,
    ) -> Data:
        data_stmt = select(Data).where(
            Data.book == book_id, Data.format == file_format_upper
        )
        format_record = session.exec(data_stmt).first()
        if format_record is None:
            msg = f"Format {file_format_upper} not found for book {book_id}"
            raise ValueError(msg)
        return format_record

    def _delete_format_file(
        self,
        *,
        book: Book,
        format_record: Data,
        file_format_upper: str,
    ) -> None:
        if book.id is None:
            return
        library_path = self._get_library_path()
        book_dir = library_path / book.path
        if not book_dir.exists():
            return

        file_path = self._find_format_file_path(
            book_dir=book_dir,
            format_record=format_record,
            book_id=book.id,
            format_upper=file_format_upper,
        )
        if file_path and file_path.exists():
            try:
                file_path.unlink()
            except OSError as e:
                logger.warning("Failed to delete format file %s: %s", file_path, e)

    def _find_format_file_path(
        self,
        *,
        book_dir: Path,
        format_record: Data,
        book_id: int,
        format_upper: str,
    ) -> Path | None:
        file_name = format_record.name or f"{book_id}"
        format_lower = format_upper.lower()

        candidate = book_dir / f"{file_name}.{format_lower}"
        if candidate.exists():
            return candidate
        candidate = book_dir / f"{book_id}.{format_lower}"
        if candidate.exists():
            return candidate
        for file_in_dir in book_dir.iterdir():
            if (
                file_in_dir.is_file()
                and file_in_dir.suffix.lower() == f".{format_lower}"
            ):
                return file_in_dir
        return None

    def _get_library_path(self) -> Path:
        if self._calibre_db_path.is_dir():
            return self._calibre_db_path
        return self._calibre_db_path.parent
