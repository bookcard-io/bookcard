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

"""Service for Calibre author operations.

Follows SRP by focusing solely on Calibre-specific author operations,
separating these concerns from the main merge service.
"""

import logging

from sqlmodel import select

from bookcard.models.core import Author, BookAuthorLink
from bookcard.repositories.calibre_book_repository import CalibreBookRepository

logger = logging.getLogger(__name__)


class CalibreAuthorService:
    """Service for Calibre author operations.

    Handles all operations related to Calibre authors, including
    book reassignment and author deletion.
    """

    def __init__(self, calibre_repo: CalibreBookRepository) -> None:
        """Initialize Calibre author service.

        Parameters
        ----------
        calibre_repo : CalibreBookRepository
            Calibre book repository instance.
        """
        self._calibre_repo = calibre_repo

    def get_book_count(self, calibre_author_id: int) -> int:
        """Get book count for a Calibre author.

        Parameters
        ----------
        calibre_author_id : int
            Calibre author ID.

        Returns
        -------
        int
            Number of books associated with the author.
        """
        with self._calibre_repo.get_session() as calibre_session:
            count_stmt = select(BookAuthorLink).where(
                BookAuthorLink.author == calibre_author_id
            )
            links = calibre_session.exec(count_stmt).all()
            return len(links)

    def reassign_books(
        self,
        from_author_id: int,
        to_author_id: int,
    ) -> None:
        """Reassign books from one Calibre author to another.

        Parameters
        ----------
        from_author_id : int
            Source Calibre author ID.
        to_author_id : int
            Target Calibre author ID.
        """
        logger.info(
            "Reassigning books from Calibre author %s to %s",
            from_author_id,
            to_author_id,
        )

        with self._calibre_repo.get_session() as calibre_session:
            # Get all book links for merge author
            merge_links = calibre_session.exec(
                select(BookAuthorLink).where(BookAuthorLink.author == from_author_id)
            ).all()

            # Update each link to point to keep author
            for link in merge_links:
                # Check if book already has keep author
                existing_link = calibre_session.exec(
                    select(BookAuthorLink).where(
                        BookAuthorLink.book == link.book,
                        BookAuthorLink.author == to_author_id,
                    )
                ).first()

                if existing_link:
                    # Book already has keep author, just delete the merge link
                    calibre_session.delete(link)
                else:
                    # Update link to point to keep author
                    link.author = to_author_id
                    calibre_session.add(link)

            calibre_session.commit()

    def delete_author(self, calibre_author_id: int) -> None:
        """Delete a Calibre author.

        Parameters
        ----------
        calibre_author_id : int
            Calibre author ID to delete.
        """
        logger.info("Deleting Calibre author %s", calibre_author_id)

        with self._calibre_repo.get_session() as calibre_session:
            calibre_author = calibre_session.exec(
                select(Author).where(Author.id == calibre_author_id)
            ).first()
            if calibre_author:
                calibre_session.delete(calibre_author)
                calibre_session.commit()
