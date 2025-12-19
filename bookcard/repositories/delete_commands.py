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

"""Commands for deleting book-related database records and filesystem items."""

import logging
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import inspect
from sqlmodel import Session, select

from bookcard.models.auth import (
    RefreshToken,
    User,
    UserRole,
    UserSetting,
)
from bookcard.models.core import (
    Book,
    BookAuthorLink,
    BookLanguageLink,
    BookPublisherLink,
    BookRatingLink,
    BookSeriesLink,
    BookTagLink,
    Comment,
    Identifier,
)
from bookcard.models.media import Data
from bookcard.models.reading import (
    Annotation,
    ReadingProgress,
    ReadingSession,
    ReadStatus,
)
from bookcard.repositories.ereader_repository import EReaderRepository

if TYPE_CHECKING:
    from bookcard.repositories.role_repository import UserRoleRepository

logger = logging.getLogger(__name__)


class DeleteCommand(ABC):
    """Base command interface for deletion operations.

    Follows Command pattern with undo capability.
    Each command encapsulates a single deletion operation.
    """

    @abstractmethod
    def execute(self) -> None:
        """Execute the deletion operation.

        Performs the actual deletion of the target entity or entities.
        Should store necessary state for potential undo operations.

        Raises
        ------
        Exception
            If execution fails. The specific exception type depends on
            the implementation.
        """

    @abstractmethod
    def undo(self) -> None:
        """Undo the deletion operation.

        Restores the state before execute() was called. This method
        should be idempotent and safe to call multiple times.

        Notes
        -----
        If execute() was never called or failed, undo() should have
        no effect.
        """


class DeleteBookAuthorLinksCommand(DeleteCommand):
    """Command to delete book-author links."""

    def __init__(self, session: Session, book_id: int) -> None:
        """Initialize command to delete book-author links.

        Parameters
        ----------
        session : Session
            Database session for executing the deletion.
        book_id : int
            ID of the book whose author links should be deleted.
        """
        self._session = session
        self._book_id = book_id
        self._deleted_links: list[BookAuthorLink] = []

    def execute(self) -> None:
        """Execute deletion of all book-author links.

        Finds and deletes all BookAuthorLink records associated with
        the book ID. Stores deleted links for potential undo.
        """
        stmt = select(BookAuthorLink).where(BookAuthorLink.book == self._book_id)
        self._deleted_links = list(self._session.exec(stmt).all())
        logger.debug(
            "Deleting %d book-author links for book_id=%d",
            len(self._deleted_links),
            self._book_id,
        )
        for link in self._deleted_links:
            self._session.delete(link)

    def undo(self) -> None:
        """Restore all deleted book-author links.

        Re-adds all previously deleted BookAuthorLink records to the
        session. Idempotent operation.
        """
        if self._deleted_links:
            logger.debug(
                "Undoing deletion of %d book-author links for book_id=%d",
                len(self._deleted_links),
                self._book_id,
            )
            for link in self._deleted_links:
                self._session.add(link)


class DeleteBookTagLinksCommand(DeleteCommand):
    """Command to delete book-tag links."""

    def __init__(self, session: Session, book_id: int) -> None:
        """Initialize command to delete book-tag links.

        Parameters
        ----------
        session : Session
            Database session for executing the deletion.
        book_id : int
            ID of the book whose tag links should be deleted.
        """
        self._session = session
        self._book_id = book_id
        self._deleted_links: list[BookTagLink] = []

    def execute(self) -> None:
        """Execute deletion of all book-tag links.

        Finds and deletes all BookTagLink records associated with
        the book ID. Stores deleted links for potential undo.
        """
        stmt = select(BookTagLink).where(BookTagLink.book == self._book_id)
        self._deleted_links = list(self._session.exec(stmt).all())
        logger.debug(
            "Deleting %d book-tag links for book_id=%d",
            len(self._deleted_links),
            self._book_id,
        )
        for link in self._deleted_links:
            self._session.delete(link)

    def undo(self) -> None:
        """Restore all deleted book-tag links.

        Re-adds all previously deleted BookTagLink records to the
        session. Idempotent operation.
        """
        if self._deleted_links:
            logger.debug(
                "Undoing deletion of %d book-tag links for book_id=%d",
                len(self._deleted_links),
                self._book_id,
            )
            for link in self._deleted_links:
                self._session.add(link)


class DeleteBookPublisherLinksCommand(DeleteCommand):
    """Command to delete book-publisher links."""

    def __init__(self, session: Session, book_id: int) -> None:
        """Initialize command to delete book-publisher links.

        Parameters
        ----------
        session : Session
            Database session for executing the deletion.
        book_id : int
            ID of the book whose publisher links should be deleted.
        """
        self._session = session
        self._book_id = book_id
        self._deleted_links: list[BookPublisherLink] = []

    def execute(self) -> None:
        """Execute deletion of all book-publisher links.

        Finds and deletes all BookPublisherLink records associated with
        the book ID. Stores deleted links for potential undo.
        """
        stmt = select(BookPublisherLink).where(BookPublisherLink.book == self._book_id)
        self._deleted_links = list(self._session.exec(stmt).all())
        logger.debug(
            "Deleting %d book-publisher links for book_id=%d",
            len(self._deleted_links),
            self._book_id,
        )
        for link in self._deleted_links:
            self._session.delete(link)

    def undo(self) -> None:
        """Restore all deleted book-publisher links.

        Re-adds all previously deleted BookPublisherLink records to the
        session. Idempotent operation.
        """
        if self._deleted_links:
            logger.debug(
                "Undoing deletion of %d book-publisher links for book_id=%d",
                len(self._deleted_links),
                self._book_id,
            )
            for link in self._deleted_links:
                self._session.add(link)


class DeleteBookLanguageLinksCommand(DeleteCommand):
    """Command to delete book-language links."""

    def __init__(self, session: Session, book_id: int) -> None:
        """Initialize command to delete book-language links.

        Parameters
        ----------
        session : Session
            Database session for executing the deletion.
        book_id : int
            ID of the book whose language links should be deleted.
        """
        self._session = session
        self._book_id = book_id
        self._deleted_links: list[BookLanguageLink] = []

    def execute(self) -> None:
        """Execute deletion of all book-language links.

        Finds and deletes all BookLanguageLink records associated with
        the book ID. Stores deleted links for potential undo.
        """
        stmt = select(BookLanguageLink).where(BookLanguageLink.book == self._book_id)
        self._deleted_links = list(self._session.exec(stmt).all())
        logger.debug(
            "Deleting %d book-language links for book_id=%d",
            len(self._deleted_links),
            self._book_id,
        )
        for link in self._deleted_links:
            self._session.delete(link)

    def undo(self) -> None:
        """Restore all deleted book-language links.

        Re-adds all previously deleted BookLanguageLink records to the
        session. Idempotent operation.
        """
        if self._deleted_links:
            logger.debug(
                "Undoing deletion of %d book-language links for book_id=%d",
                len(self._deleted_links),
                self._book_id,
            )
            for link in self._deleted_links:
                self._session.add(link)


class DeleteBookRatingLinksCommand(DeleteCommand):
    """Command to delete book-rating links."""

    def __init__(self, session: Session, book_id: int) -> None:
        """Initialize command to delete book-rating links.

        Parameters
        ----------
        session : Session
            Database session for executing the deletion.
        book_id : int
            ID of the book whose rating links should be deleted.
        """
        self._session = session
        self._book_id = book_id
        self._deleted_links: list[BookRatingLink] = []

    def execute(self) -> None:
        """Execute deletion of all book-rating links.

        Finds and deletes all BookRatingLink records associated with
        the book ID. Stores deleted links for potential undo.
        """
        stmt = select(BookRatingLink).where(BookRatingLink.book == self._book_id)
        self._deleted_links = list(self._session.exec(stmt).all())
        logger.debug(
            "Deleting %d book-rating links for book_id=%d",
            len(self._deleted_links),
            self._book_id,
        )
        for link in self._deleted_links:
            self._session.delete(link)

    def undo(self) -> None:
        """Restore all deleted book-rating links.

        Re-adds all previously deleted BookRatingLink records to the
        session. Idempotent operation.
        """
        if self._deleted_links:
            logger.debug(
                "Undoing deletion of %d book-rating links for book_id=%d",
                len(self._deleted_links),
                self._book_id,
            )
            for link in self._deleted_links:
                self._session.add(link)


class DeleteBookSeriesLinksCommand(DeleteCommand):
    """Command to delete book-series links."""

    def __init__(self, session: Session, book_id: int) -> None:
        """Initialize command to delete book-series links.

        Parameters
        ----------
        session : Session
            Database session for executing the deletion.
        book_id : int
            ID of the book whose series links should be deleted.
        """
        self._session = session
        self._book_id = book_id
        self._deleted_links: list[BookSeriesLink] = []

    def execute(self) -> None:
        """Execute deletion of all book-series links.

        Finds and deletes all BookSeriesLink records associated with
        the book ID. Stores deleted links for potential undo.
        """
        stmt = select(BookSeriesLink).where(BookSeriesLink.book == self._book_id)
        self._deleted_links = list(self._session.exec(stmt).all())
        logger.debug(
            "Deleting %d book-series links for book_id=%d",
            len(self._deleted_links),
            self._book_id,
        )
        for link in self._deleted_links:
            self._session.delete(link)

    def undo(self) -> None:
        """Restore all deleted book-series links.

        Re-adds all previously deleted BookSeriesLink records to the
        session. Idempotent operation.
        """
        if self._deleted_links:
            logger.debug(
                "Undoing deletion of %d book-series links for book_id=%d",
                len(self._deleted_links),
                self._book_id,
            )
            for link in self._deleted_links:
                self._session.add(link)


class DeleteBookShelfLinksCommand(DeleteCommand):
    """Command to delete book-shelf links.

    Currently a no-op as shelves are not yet implemented.
    """

    def __init__(self, session: Session, book_id: int) -> None:
        """Initialize command to delete book-shelf links.

        Parameters
        ----------
        session : Session
            Database session for executing the deletion.
        book_id : int
            ID of the book whose shelf links should be deleted.
        """
        self._session = session
        self._book_id = book_id

    def execute(self) -> None:
        """Execute deletion of all book-shelf links.

        Currently a no-op as shelves are not yet implemented.
        Logs an info message indicating that shelf link deletion is skipped.
        """
        logger.info(
            "Skipping book-shelf links deletion for book_id=%d (shelves not yet implemented)",
            self._book_id,
        )

    def undo(self) -> None:
        """Restore all deleted book-shelf links.

        Currently a no-op as shelves are not yet implemented.
        This method has no effect.
        """
        # No-op: shelves not yet implemented


class DeleteCommentCommand(DeleteCommand):
    """Command to delete book comment."""

    def __init__(self, session: Session, book_id: int) -> None:
        """Initialize command to delete book comment.

        Parameters
        ----------
        session : Session
            Database session for executing the deletion.
        book_id : int
            ID of the book whose comment should be deleted.
        """
        self._session = session
        self._book_id = book_id
        self._deleted_comment: Comment | None = None

    def execute(self) -> None:
        """Execute deletion of the book comment.

        Finds and deletes the Comment record associated with the book ID.
        Stores the deleted comment for potential undo. If no comment exists,
        the operation has no effect.
        """
        stmt = select(Comment).where(Comment.book == self._book_id)
        self._deleted_comment = self._session.exec(stmt).first()
        if self._deleted_comment is not None:
            logger.debug("Deleting comment for book_id=%d", self._book_id)
            self._session.delete(self._deleted_comment)

    def undo(self) -> None:
        """Restore the deleted book comment.

        Re-adds the previously deleted Comment record to the session
        if one existed. Idempotent operation.
        """
        if self._deleted_comment is not None:
            logger.debug("Undoing deletion of comment for book_id=%d", self._book_id)
            self._session.add(self._deleted_comment)


class DeleteIdentifiersCommand(DeleteCommand):
    """Command to delete book identifiers."""

    def __init__(self, session: Session, book_id: int) -> None:
        """Initialize command to delete book identifiers.

        Parameters
        ----------
        session : Session
            Database session for executing the deletion.
        book_id : int
            ID of the book whose identifiers should be deleted.
        """
        self._session = session
        self._book_id = book_id
        self._deleted_identifiers: list[Identifier] = []

    def execute(self) -> None:
        """Execute deletion of all book identifiers.

        Finds and deletes all Identifier records associated with the book ID.
        Stores deleted identifiers for potential undo.
        """
        stmt = select(Identifier).where(Identifier.book == self._book_id)
        self._deleted_identifiers = list(self._session.exec(stmt).all())
        logger.debug(
            "Deleting %d identifiers for book_id=%d",
            len(self._deleted_identifiers),
            self._book_id,
        )
        for identifier in self._deleted_identifiers:
            self._session.delete(identifier)

    def undo(self) -> None:
        """Restore all deleted book identifiers.

        Re-adds all previously deleted Identifier records to the session.
        Idempotent operation.
        """
        if self._deleted_identifiers:
            logger.debug(
                "Undoing deletion of %d identifiers for book_id=%d",
                len(self._deleted_identifiers),
                self._book_id,
            )
            for identifier in self._deleted_identifiers:
                self._session.add(identifier)


class DeleteDataRecordsCommand(DeleteCommand):
    """Command to delete book data records."""

    def __init__(self, session: Session, book_id: int) -> None:
        """Initialize command to delete book data records.

        Parameters
        ----------
        session : Session
            Database session for executing the deletion.
        book_id : int
            ID of the book whose data records should be deleted.
        """
        self._session = session
        self._book_id = book_id
        self._deleted_data: list[Data] = []

    def execute(self) -> None:
        """Execute deletion of all book data records.

        Finds and deletes all Data records (file format entries) associated
        with the book ID. Stores deleted records for potential undo.
        Only deletes records that are still persistent in the session to
        avoid SQLAlchemy warnings about mismatched row counts.
        """
        stmt = select(Data).where(Data.book == self._book_id)
        all_records = list(self._session.exec(stmt).all())

        # Only track and delete records that are still persistent
        # (not already deleted by cascade or other means)
        skipped_count = 0
        for data_record in all_records:
            obj_state = inspect(data_record)
            if obj_state.persistent:
                self._deleted_data.append(data_record)
                self._session.delete(data_record)
            else:
                skipped_count += 1

        logger.debug(
            "Deleting %d data records for book_id=%d (skipped %d non-persistent)",
            len(self._deleted_data),
            self._book_id,
            skipped_count,
        )

    def undo(self) -> None:
        """Restore all deleted book data records.

        Re-adds all previously deleted Data records to the session.
        Idempotent operation.
        """
        if self._deleted_data:
            logger.debug(
                "Undoing deletion of %d data records for book_id=%d",
                len(self._deleted_data),
                self._book_id,
            )
            for data_record in self._deleted_data:
                self._session.add(data_record)


class DeleteBookCommand(DeleteCommand):
    """Command to delete the book record itself."""

    def __init__(self, session: Session, book: Book) -> None:
        """Initialize command to delete the book record.

        Parameters
        ----------
        session : Session
            Database session for executing the deletion.
        book : Book
            Book instance to delete.
        """
        self._session = session
        self._book = book
        self._book_snapshot: dict | None = None

    def execute(self) -> None:
        """Execute deletion of the book record.

        Creates a snapshot of essential book fields for potential undo,
        then deletes the book record from the session.
        """
        # Create snapshot for undo
        self._book_snapshot = {
            "id": self._book.id,
            "title": self._book.title,
            "path": self._book.path,
            "uuid": self._book.uuid,
            "has_cover": self._book.has_cover,
        }
        logger.debug(
            "Deleting book record: id=%d, title=%r",
            self._book.id,
            self._book.title,
        )
        self._session.delete(self._book)

    def undo(self) -> None:
        """Restore the deleted book record.

        Recreates the book record from the stored snapshot and adds it
        to the session. Idempotent operation.

        Notes
        -----
        Only essential fields are restored. Other fields will use their
        default values.
        """
        if self._book_snapshot is not None:
            logger.debug(
                "Undoing deletion of book record: id=%d, title=%r",
                self._book_snapshot["id"],
                self._book_snapshot["title"],
            )
            # Recreate book from snapshot
            restored_book = Book(
                id=self._book_snapshot["id"],
                title=self._book_snapshot["title"],
                path=self._book_snapshot["path"],
                uuid=self._book_snapshot["uuid"],
                has_cover=self._book_snapshot["has_cover"],
            )
            self._session.add(restored_book)


class DeleteFileCommand(DeleteCommand):
    """Command to delete a single file from filesystem."""

    def __init__(self, file_path: Path) -> None:
        """Initialize command to delete a filesystem file.

        Parameters
        ----------
        file_path : Path
            Path to the file to delete.
        """
        self._file_path = file_path
        self._file_backup: bytes | None = None
        self._file_existed = False

    def execute(self) -> None:
        """Execute deletion of the filesystem file.

        If the file exists, reads its content into memory for potential
        undo, then deletes the file from the filesystem.

        Notes
        -----
        If the file does not exist, the operation has no effect.
        """
        if self._file_path.exists() and self._file_path.is_file():
            self._file_existed = True
            file_size = self._file_path.stat().st_size
            logger.debug(
                "Deleting file: %r (size=%d bytes)",
                self._file_path,
                file_size,
            )
            # Read file content for undo
            self._file_backup = self._file_path.read_bytes()
            self._file_path.unlink()
        else:
            logger.debug("File does not exist, skipping: %r", self._file_path)

    def undo(self) -> None:
        """Restore the deleted filesystem file.

        Recreates the file from the stored backup content. Creates parent
        directories if necessary. Idempotent operation.

        Notes
        -----
        Only restores the file if it was successfully deleted during
        execute(). If the file did not exist originally, undo() has no effect.
        """
        if self._file_existed and self._file_backup is not None:
            logger.debug(
                "Restoring file: %r (size=%d bytes)",
                self._file_path,
                len(self._file_backup),
            )
            # Restore file from backup
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
            self._file_path.write_bytes(self._file_backup)


class DeleteDirectoryCommand(DeleteCommand):
    """Command to delete a directory if empty."""

    def __init__(self, dir_path: Path) -> None:
        """Initialize command to delete an empty directory.

        Parameters
        ----------
        dir_path : Path
            Path to the directory to delete.
        """
        self._dir_path = dir_path
        self._dir_existed = False

    def execute(self) -> None:
        """Execute deletion of the directory if empty.

        Checks if the directory exists and is empty (excluding . and ..),
        then deletes it. Only deletes if the directory is completely empty.

        Notes
        -----
        If the directory does not exist or contains files, the operation
        has no effect.
        """
        if self._dir_path.exists() and self._dir_path.is_dir():
            # Check if directory is empty (excluding . and ..)
            remaining_items = [
                item
                for item in self._dir_path.iterdir()
                if item.name not in (".", "..")
            ]
            if not remaining_items:
                self._dir_existed = True
                logger.debug("Deleting empty directory: %r", self._dir_path)
                self._dir_path.rmdir()
            else:
                logger.debug(
                    "Directory not empty, skipping deletion: %r (%d items remaining)",
                    self._dir_path,
                    len(remaining_items),
                )
        else:
            logger.debug("Directory does not exist, skipping: %r", self._dir_path)

    def undo(self) -> None:
        """Restore the deleted directory.

        Recreates the directory if it was successfully deleted during
        execute(). Creates parent directories if necessary. Idempotent
        operation.

        Notes
        -----
        Only recreates the directory if it was successfully deleted.
        The restored directory will be empty.
        """
        if self._dir_existed:
            logger.debug("Restoring directory: %r", self._dir_path)
            # Recreate directory
            self._dir_path.mkdir(parents=True, exist_ok=True)


class DeleteUserDevicesCommand(DeleteCommand):
    """Command to delete all e-reader devices for a user."""

    def __init__(
        self,
        session: Session,
        user_id: int,
        device_repo: EReaderRepository,
    ) -> None:
        """Initialize command to delete user devices.

        Parameters
        ----------
        session : Session
            Database session for executing the deletion.
        user_id : int
            User identifier.
        device_repo : EReaderRepository
            E-reader repository for finding and deleting devices.
        """
        self._session = session
        self._user_id = user_id
        self._device_repo = device_repo
        self._deleted_devices: list = []

    def execute(self) -> None:
        """Execute deletion of all user devices.

        Finds and deletes all EReaderDevice records for the user.
        Stores deleted devices for potential undo.
        """
        devices = list(self._device_repo.find_by_user(self._user_id))
        self._deleted_devices = devices.copy()
        for device in devices:
            self._device_repo.delete(device)
        if devices:
            logger.debug(
                "Deleted %d device(s) for user %d",
                len(devices),
                self._user_id,
            )

    def undo(self) -> None:
        """Restore all deleted user devices.

        Re-adds all previously deleted devices to the session.
        """
        if self._deleted_devices:
            logger.debug(
                "Restoring %d device(s) for user %d",
                len(self._deleted_devices),
                self._user_id,
            )
            for device in self._deleted_devices:
                self._session.add(device)


class DeleteUserRolesCommand(DeleteCommand):
    """Command to delete all user-role associations for a user."""

    def __init__(
        self,
        session: Session,
        user_id: int,
        user_role_repo: "UserRoleRepository",
    ) -> None:
        """Initialize command to delete user roles.

        Parameters
        ----------
        session : Session
            Database session for executing the deletion.
        user_id : int
            User identifier.
        user_role_repo : UserRoleRepository
            User role repository for finding and deleting roles.
        """
        self._session = session
        self._user_id = user_id
        self._user_role_repo = user_role_repo
        self._deleted_roles: list = []

    def execute(self) -> None:
        """Execute deletion of all user roles.

        Finds and deletes all UserRole records for the user.
        Stores deleted roles for potential undo.
        """
        user_roles = list(
            self._session.exec(
                select(UserRole).where(UserRole.user_id == self._user_id)
            ).all()
        )
        self._deleted_roles = user_roles.copy()
        for user_role in user_roles:
            self._user_role_repo.delete(user_role)
        if user_roles:
            logger.debug(
                "Deleted %d role(s) for user %d",
                len(user_roles),
                self._user_id,
            )

    def undo(self) -> None:
        """Restore all deleted user roles.

        Re-adds all previously deleted user roles to the session.
        """
        if self._deleted_roles:
            logger.debug(
                "Restoring %d role(s) for user %d",
                len(self._deleted_roles),
                self._user_id,
            )
            for user_role in self._deleted_roles:
                self._session.add(user_role)


class DeleteUserSettingsCommand(DeleteCommand):
    """Command to delete all user settings for a user."""

    def __init__(self, session: Session, user_id: int) -> None:
        """Initialize command to delete user settings.

        Parameters
        ----------
        session : Session
            Database session for executing the deletion.
        user_id : int
            User identifier.
        """
        self._session = session
        self._user_id = user_id
        self._deleted_settings: list = []

    def execute(self) -> None:
        """Execute deletion of all user settings.

        Finds and deletes all UserSetting records for the user.
        Stores deleted settings for potential undo.
        """
        user_settings = list(
            self._session.exec(
                select(UserSetting).where(UserSetting.user_id == self._user_id)
            ).all()
        )
        self._deleted_settings = user_settings.copy()
        for setting in user_settings:
            self._session.delete(setting)
        if user_settings:
            logger.debug(
                "Deleted %d setting(s) for user %d",
                len(user_settings),
                self._user_id,
            )

    def undo(self) -> None:
        """Restore all deleted user settings.

        Re-adds all previously deleted settings to the session.
        """
        if self._deleted_settings:
            logger.debug(
                "Restoring %d setting(s) for user %d",
                len(self._deleted_settings),
                self._user_id,
            )
            for setting in self._deleted_settings:
                self._session.add(setting)


class DeleteRefreshTokensCommand(DeleteCommand):
    """Command to delete all refresh tokens for a user."""

    def __init__(self, session: Session, user_id: int) -> None:
        """Initialize command to delete refresh tokens.

        Parameters
        ----------
        session : Session
            Database session for executing the deletion.
        user_id : int
            User identifier.
        """
        self._session = session
        self._user_id = user_id
        self._deleted_tokens: list = []

    def execute(self) -> None:
        """Execute deletion of all refresh tokens.

        Finds and deletes all RefreshToken records for the user.
        Stores deleted tokens for potential undo.
        """
        refresh_tokens = list(
            self._session.exec(
                select(RefreshToken).where(RefreshToken.user_id == self._user_id)
            ).all()
        )
        self._deleted_tokens = refresh_tokens.copy()
        for token in refresh_tokens:
            self._session.delete(token)
        if refresh_tokens:
            logger.debug(
                "Deleted %d refresh token(s) for user %d",
                len(refresh_tokens),
                self._user_id,
            )

    def undo(self) -> None:
        """Restore all deleted refresh tokens.

        Re-adds all previously deleted tokens to the session.
        """
        if self._deleted_tokens:
            logger.debug(
                "Restoring %d refresh token(s) for user %d",
                len(self._deleted_tokens),
                self._user_id,
            )
            for token in self._deleted_tokens:
                self._session.add(token)


class DeleteUserReadingDataCommand(DeleteCommand):
    """Command to delete all reading-related data for a user.

    Deletes ReadingProgress, ReadingSession, ReadStatus, and Annotation records
    associated with the user. These must be deleted before the user can be deleted
    due to foreign key constraints.
    """

    def __init__(self, session: Session, user_id: int) -> None:
        """Initialize command to delete user reading data.

        Parameters
        ----------
        session : Session
            Database session for executing the deletion.
        user_id : int
            User identifier.
        """
        self._session = session
        self._user_id = user_id
        self._deleted_reading_progress: list[ReadingProgress] = []
        self._deleted_reading_sessions: list[ReadingSession] = []
        self._deleted_read_statuses: list[ReadStatus] = []
        self._deleted_annotations: list[Annotation] = []

    def execute(self) -> None:
        """Execute deletion of all reading-related data.

        Finds and deletes all ReadingProgress, ReadingSession, ReadStatus,
        and Annotation records for the user. Stores deleted records for potential undo.
        """
        # Delete ReadingProgress records
        reading_progress = list(
            self._session.exec(
                select(ReadingProgress).where(ReadingProgress.user_id == self._user_id)
            ).all()
        )
        self._deleted_reading_progress = reading_progress.copy()
        for progress in reading_progress:
            self._session.delete(progress)

        # Delete ReadingSession records
        reading_sessions = list(
            self._session.exec(
                select(ReadingSession).where(ReadingSession.user_id == self._user_id)
            ).all()
        )
        self._deleted_reading_sessions = reading_sessions.copy()
        for session in reading_sessions:
            self._session.delete(session)

        # Delete ReadStatus records
        read_statuses = list(
            self._session.exec(
                select(ReadStatus).where(ReadStatus.user_id == self._user_id)
            ).all()
        )
        self._deleted_read_statuses = read_statuses.copy()
        for status in read_statuses:
            self._session.delete(status)

        # Delete Annotation records
        annotations = list(
            self._session.exec(
                select(Annotation).where(Annotation.user_id == self._user_id)
            ).all()
        )
        self._deleted_annotations = annotations.copy()
        for annotation in annotations:
            self._session.delete(annotation)

        total_deleted = (
            len(reading_progress)
            + len(reading_sessions)
            + len(read_statuses)
            + len(annotations)
        )
        if total_deleted > 0:
            logger.debug(
                "Deleted reading data for user %d: %d progress, %d sessions, "
                "%d statuses, %d annotations",
                self._user_id,
                len(reading_progress),
                len(reading_sessions),
                len(read_statuses),
                len(annotations),
            )

    def undo(self) -> None:
        """Restore all deleted reading-related data.

        Re-adds all previously deleted reading records to the session.
        """
        if (
            self._deleted_reading_progress
            or self._deleted_reading_sessions
            or self._deleted_read_statuses
            or self._deleted_annotations
        ):
            logger.debug(
                "Restoring reading data for user %d: %d progress, %d sessions, "
                "%d statuses, %d annotations",
                self._user_id,
                len(self._deleted_reading_progress),
                len(self._deleted_reading_sessions),
                len(self._deleted_read_statuses),
                len(self._deleted_annotations),
            )
            for progress in self._deleted_reading_progress:
                self._session.add(progress)
            for session in self._deleted_reading_sessions:
                self._session.add(session)
            for status in self._deleted_read_statuses:
                self._session.add(status)
            for annotation in self._deleted_annotations:
                self._session.add(annotation)


class DeleteUserDataDirectoryCommand(DeleteCommand):
    """Command to delete a user's data directory recursively."""

    def __init__(self, user_data_dir: Path) -> None:
        """Initialize command to delete user data directory.

        Parameters
        ----------
        user_data_dir : Path
            Path to the user's data directory to delete.
        """
        self._user_data_dir = user_data_dir
        self._dir_existed = False
        self._backup_path: Path | None = None

    def execute(self) -> None:
        """Execute deletion of the user data directory.

        If the directory exists, creates a backup snapshot for potential
        undo, then recursively deletes the directory.

        Notes
        -----
        For large directories, undo may not be practical. This command
        prioritizes deletion safety over undo capability.
        """
        if self._user_data_dir.exists() and self._user_data_dir.is_dir():
            self._dir_existed = True
            logger.debug("Deleting user data directory: %r", self._user_data_dir)
            # Note: Full undo would require backing up entire directory tree
            # For now, we mark it as deleted but don't backup (too expensive)
            shutil.rmtree(self._user_data_dir)
        else:
            logger.debug(
                "User data directory does not exist, skipping: %r",
                self._user_data_dir,
            )

    def undo(self) -> None:
        """Restore the deleted user data directory.

        Notes
        -----
        This is a no-op as we don't backup large directory trees.
        Filesystem undo for recursive directory deletion is not practical.
        """
        if self._dir_existed:
            logger.warning(
                "Cannot undo recursive directory deletion: %r",
                self._user_data_dir,
            )


class DeleteUserCommand(DeleteCommand):
    """Command to delete the user record itself."""

    def __init__(self, session: Session, user: "User") -> None:
        """Initialize command to delete the user record.

        Parameters
        ----------
        session : Session
            Database session for executing the deletion.
        user : User
            User instance to delete.
        """
        self._session = session
        self._user = user
        self._user_snapshot: dict | None = None

    def execute(self) -> None:
        """Execute deletion of the user record.

        Creates a snapshot of essential user fields for potential undo,
        then deletes the user record from the session.
        """
        # Create snapshot for undo
        self._user_snapshot = {
            "id": self._user.id,
            "username": self._user.username,
            "email": self._user.email,
            "password_hash": self._user.password_hash,
            "full_name": self._user.full_name,
            "is_admin": self._user.is_admin,
            "is_active": self._user.is_active,
            "profile_picture": self._user.profile_picture,
            "created_at": self._user.created_at,
            "updated_at": self._user.updated_at,
            "last_login": self._user.last_login,
        }
        logger.debug(
            "Deleting user record: id=%d, username=%r",
            self._user.id,
            self._user.username,
        )
        self._session.delete(self._user)

    def undo(self) -> None:
        """Restore the deleted user record.

        Recreates the user from the stored snapshot and adds it back
        to the session. Idempotent operation.
        """
        if self._user_snapshot is not None:
            logger.debug(
                "Restoring user record: id=%d, username=%r",
                self._user_snapshot["id"],
                self._user_snapshot["username"],
            )
            restored_user = User(**self._user_snapshot)
            self._session.add(restored_user)
