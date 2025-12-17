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

"""Book deletion operations for the Calibre repository."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select

from bookcard.models.core import Book
from bookcard.repositories.command_executor import CommandExecutor
from bookcard.repositories.delete_commands import (
    DeleteBookAuthorLinksCommand,
    DeleteBookCommand,
    DeleteBookLanguageLinksCommand,
    DeleteBookPublisherLinksCommand,
    DeleteBookRatingLinksCommand,
    DeleteBookSeriesLinksCommand,
    DeleteBookShelfLinksCommand,
    DeleteBookTagLinksCommand,
    DeleteCommentCommand,
    DeleteDataRecordsCommand,
    DeleteDirectoryCommand,
    DeleteFileCommand,
    DeleteIdentifiersCommand,
)

if TYPE_CHECKING:
    from pathlib import Path
    from typing import NoReturn

    from bookcard.repositories.interfaces import IFileManager, ISessionManager

    from .retry import SQLiteRetryPolicy


class BookDeletionOperations:
    """Delete books and their related records/files."""

    def __init__(
        self,
        *,
        session_manager: ISessionManager,
        retry_policy: SQLiteRetryPolicy,
        file_manager: IFileManager,
    ) -> None:
        self._session_manager = session_manager
        self._retry = retry_policy
        self._file_manager = file_manager

    def delete_book(
        self,
        *,
        book_id: int,
        delete_files_from_drive: bool = False,
        library_path: Path | None = None,
    ) -> None:
        """Delete a book and all its related data.

        Parameters
        ----------
        book_id : int
            Book id.
        delete_files_from_drive : bool
            Whether to delete files from disk.
        library_path : Path | None
            Library root path (required if deleting from disk).
        """
        with self._session_manager.get_session() as session:
            try:
                book: Book | None = session.exec(
                    select(Book).where(Book.id == book_id)
                ).first()
                if book is None:
                    self._raise_book_not_found()
                db_book = cast("Book", book)

                filesystem_paths: list[Path] = []
                book_dir: Path | None = None
                if delete_files_from_drive and library_path and db_book.path:
                    filesystem_paths, book_dir = self._file_manager.collect_book_files(
                        session, book_id, db_book.path, library_path
                    )

                self._execute_database_deletion_commands(session, book_id, db_book)
                self._retry.commit(session)

                if delete_files_from_drive:
                    self._execute_filesystem_deletion_commands(
                        filesystem_paths=filesystem_paths,
                        book_dir=book_dir,
                    )
            except (SQLAlchemyError, OSError, ValueError):
                session.rollback()
                raise

    @staticmethod
    def _raise_book_not_found() -> NoReturn:
        """Raise a consistent 'book not found' exception."""
        msg = "book_not_found"
        raise ValueError(msg)

    def _execute_database_deletion_commands(
        self,
        session: Session,
        book_id: int,
        book: Book,
    ) -> None:
        executor = CommandExecutor()
        executor.execute(DeleteBookAuthorLinksCommand(session, book_id))
        executor.execute(DeleteBookTagLinksCommand(session, book_id))
        executor.execute(DeleteBookPublisherLinksCommand(session, book_id))
        executor.execute(DeleteBookLanguageLinksCommand(session, book_id))
        executor.execute(DeleteBookRatingLinksCommand(session, book_id))
        executor.execute(DeleteBookSeriesLinksCommand(session, book_id))
        executor.execute(DeleteBookShelfLinksCommand(session, book_id))
        executor.execute(DeleteCommentCommand(session, book_id))
        executor.execute(DeleteIdentifiersCommand(session, book_id))
        executor.execute(DeleteDataRecordsCommand(session, book_id))
        executor.execute(DeleteBookCommand(session, book))
        executor.clear()

    def _execute_filesystem_deletion_commands(
        self,
        *,
        filesystem_paths: list[Path],
        book_dir: Path | None,
    ) -> None:
        if not filesystem_paths:
            return

        fs_executor = CommandExecutor()
        for file_path in filesystem_paths:
            fs_executor.execute(DeleteFileCommand(file_path))

        if book_dir and book_dir.exists() and book_dir.is_dir():
            fs_executor.execute(DeleteDirectoryCommand(book_dir))
