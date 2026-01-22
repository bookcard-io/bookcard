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

"""Domain models for email send task.

Value objects and domain entities following Domain-Driven Design principles.
Addresses primitive obsession by encapsulating validation and behavior.
"""

from dataclasses import dataclass
from typing import Any

from bookcard.repositories import BookWithFullRelations


@dataclass(frozen=True)
class BookId:
    """Value object representing a book identifier.

    Encapsulates validation logic for book IDs.
    """

    value: int

    def __post_init__(self) -> None:
        """Validate book ID.

        Raises
        ------
        ValueError
            If book ID is not positive.
        """
        if self.value <= 0:
            msg = "Book ID must be positive"
            raise ValueError(msg)

    @classmethod
    def from_metadata(cls, metadata: dict[str, Any], key: str = "book_id") -> "BookId":
        """Create BookId from metadata dictionary.

        Parameters
        ----------
        metadata : dict[str, Any]
            Metadata dictionary.
        key : str
            Key to extract book ID from.

        Returns
        -------
        BookId
            Book ID value object.

        Raises
        ------
        ValueError
            If key is missing.
        TypeError
            If value is not an integer.
        """
        value = metadata.get(key)
        if value is None:
            msg = f"{key} is required in task metadata"
            raise ValueError(msg)
        if not isinstance(value, int):
            msg = f"{key} must be an integer"
            raise TypeError(msg)
        return cls(value)


@dataclass(frozen=True)
class EncryptionKey:
    """Value object representing an encryption key.

    Encapsulates validation logic for encryption keys.
    """

    value: str

    def __post_init__(self) -> None:
        """Validate encryption key.

        Raises
        ------
        ValueError
            If encryption key is empty.
        """
        if not self.value:
            msg = "Encryption key is required"
            raise ValueError(msg)

    @classmethod
    def from_metadata(
        cls, metadata: dict[str, Any], key: str = "encryption_key"
    ) -> "EncryptionKey":
        """Create EncryptionKey from metadata dictionary.

        Parameters
        ----------
        metadata : dict[str, Any]
            Metadata dictionary.
        key : str
            Key to extract encryption key from.

        Returns
        -------
        EncryptionKey
            Encryption key value object.

        Raises
        ------
        ValueError
            If key is missing or empty.
        TypeError
            If value is not a string.
        """
        value = metadata.get(key)
        if not value:
            msg = f"{key} is required in task metadata"
            raise ValueError(msg)
        if not isinstance(value, str):
            msg = f"{key} must be a string"
            raise TypeError(msg)
        return cls(value)


@dataclass(frozen=True)
class FileFormat:
    """Value object representing a file format.

    Provides normalized format handling.
    """

    value: str | None

    def is_epub(self) -> bool:
        """Check if format is EPUB.

        Returns
        -------
        bool
            True if format is EPUB, False otherwise.
        """
        return self.value is not None and self.value.upper() == "EPUB"

    def lower(self) -> str | None:
        """Get lowercase format string.

        Returns
        -------
        str | None
            Lowercase format or None.
        """
        return self.value.lower() if self.value else None


@dataclass(frozen=True)
class EmailTarget:
    """Target for email delivery.

    Makes the semantics of None (default device) explicit.
    """

    address: str | None = None

    def __str__(self) -> str:
        """Return string representation.

        Returns
        -------
        str
            Email address or "default device" if None.
        """
        return self.address or "default device"


@dataclass(frozen=True)
class SendBookRequest:
    """Request to send a book via email.

    Value object encapsulating all request parameters.
    """

    book_id: BookId
    email_target: EmailTarget
    file_format: FileFormat
    encryption_key: EncryptionKey

    @classmethod
    def from_metadata(cls, metadata: dict[str, Any]) -> "SendBookRequest":
        """Create SendBookRequest from metadata dictionary.

        Parameters
        ----------
        metadata : dict[str, Any]
            Task metadata dictionary.

        Returns
        -------
        SendBookRequest
            Send book request value object.

        Raises
        ------
        ValueError
            If required fields are missing.
        TypeError
            If field types are incorrect.
        """
        return cls(
            book_id=BookId.from_metadata(metadata),
            email_target=EmailTarget(metadata.get("to_email")),
            file_format=FileFormat(metadata.get("file_format")),
            encryption_key=EncryptionKey.from_metadata(metadata),
        )


@dataclass(frozen=True)
class SendPreparation:
    """Prepared data for sending a book via email.

    Bundles the resolved format and metadata with domain behavior.
    """

    book_title: str
    attachment_filename: str
    resolved_format: str | None
    book_with_rels: BookWithFullRelations

    def requires_epub_fixing(self) -> bool:
        """Check if EPUB fixing is required.

        Returns
        -------
        bool
            True if resolved format is EPUB, False otherwise.
        """
        return (
            self.resolved_format is not None and self.resolved_format.upper() == "EPUB"
        )

    def validate(self) -> None:
        """Validate preparation data.

        Raises
        ------
        ValueError
            If required fields are missing.
        """
        if not self.book_title:
            msg = "Book title required"
            raise ValueError(msg)
        if not self.attachment_filename:
            msg = "Attachment filename required"
            raise ValueError(msg)


@dataclass(frozen=True)
class SendMetadata:
    """Metadata for completed email send.

    Encapsulates completion metadata following Single Responsibility Principle.
    """

    book_title: str
    attachment_filename: str
