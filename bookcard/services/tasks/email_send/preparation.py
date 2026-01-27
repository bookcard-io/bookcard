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

"""Send preparation service for email send task.

Handles preparation of books for sending, following SRP.
"""

from sqlmodel import Session

from bookcard.services.book_service import BookService
from bookcard.services.email_utils import build_attachment_filename
from bookcard.services.send_format_service import SendFormatService
from bookcard.services.tasks.email_send.domain import (
    SendBookRequest,
    SendPreparation,
)
from bookcard.services.tasks.email_send.exceptions import BookNotFoundError
from bookcard.services.tasks.utils import AuthorExtractor


class DefaultSendPreparationService:
    """Default implementation of send preparation service."""

    def prepare(
        self,
        request: SendBookRequest,
        book_service: BookService,
        session: Session,
        user_id: int,
    ) -> SendPreparation:
        """Prepare book for sending.

        Parameters
        ----------
        request : SendBookRequest
            Send book request.
        book_service : BookService
            Book service instance.
        session : Session
            Database session.
        user_id : int
            User ID.

        Returns
        -------
        SendPreparation
            Prepared send data.

        Raises
        ------
        BookNotFoundError
            If book is not found.
        """
        book_with_rels = book_service.get_book_full(request.book_id.value)
        if book_with_rels is None:
            raise BookNotFoundError(request.book_id.value)

        book_title = book_with_rels.book.title or "Unknown Book"
        author_name = AuthorExtractor.get_primary_author_name(book_with_rels)

        resolved_format = SendFormatService(session).select_format(
            user_id=user_id,
            to_email=request.email_target.address,
            requested_format=request.file_format.value,
            book_with_rels=book_with_rels,
        )

        attachment_filename = build_attachment_filename(
            author=author_name,
            title=book_title,
            extension=resolved_format.lower() if resolved_format else None,
        )

        return SendPreparation(
            book_title=book_title,
            attachment_filename=attachment_filename,
            resolved_format=resolved_format,
            book_with_rels=book_with_rels,
        )
