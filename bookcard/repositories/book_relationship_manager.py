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

"""Book relationship manager for managing book relationships.

This module handles all book relationship operations following SRP.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlmodel import Session, select

from bookcard.models.core import (
    Author,
    BookAuthorLink,
    BookLanguageLink,
    BookPublisherLink,
    BookRatingLink,
    BookSeriesLink,
    BookTagLink,
    Comment,
    Identifier,
    Language,
    Publisher,
    Rating,
    Series,
    Tag,
)
from bookcard.repositories.interfaces import IBookRelationshipManager

if TYPE_CHECKING:
    from bookcard.services.book_metadata import BookMetadata


class BookRelationshipManager(IBookRelationshipManager):
    """Manages book relationships (authors, tags, series, etc.).

    Handles all relationship updates following SRP by focusing solely
    on relationship management concerns.
    """

    def _normalize_string_set(self, strings: list[str]) -> set[str]:
        """Normalize a list of strings for comparison.

        Parameters
        ----------
        strings : list[str]
            List of strings to normalize.

        Returns
        -------
        set[str]
            Set of normalized (lowercased, stripped) strings, excluding empty ones.
        """
        return {s.strip().lower() for s in strings if s.strip()}

    def _delete_links_and_flush(self, session: Session, links: list[object]) -> None:
        """Delete multiple links and flush the session.

        Helper method to delete multiple link relationships and immediately flush
        the session to ensure the deletes are processed before inserting new links.
        This prevents UNIQUE constraint violations when updating relationships.

        Parameters
        ----------
        session : Session
            Database session.
        links : list[object]
            List of link objects to delete. Can be empty.

        Notes
        -----
        This method is idempotent - if links is empty, it does nothing.
        """
        if links:
            for link in links:
                session.delete(link)
            session.flush()

    def update_authors(
        self,
        session: Session,
        book_id: int,
        author_names: list[str],
    ) -> None:
        """Update book authors.

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Calibre book ID.
        author_names : list[str]
            List of author names to set (replaces existing).
        """
        # Get current authors
        current_authors_stmt = (
            select(Author.name)
            .join(BookAuthorLink, Author.id == BookAuthorLink.author)
            .where(BookAuthorLink.book == book_id)
            .order_by(BookAuthorLink.id)
        )
        current_author_names = self._normalize_string_set(
            list(session.exec(current_authors_stmt).all())
        )

        # Normalize new author names
        normalized_new_authors = self._normalize_string_set(author_names)

        # Check if authors are actually changing
        if current_author_names == normalized_new_authors:
            # Authors haven't changed, no update needed
            return

        # Authors are changing - delete existing author links
        delete_links_stmt = select(BookAuthorLink).where(BookAuthorLink.book == book_id)
        existing_links = list(session.exec(delete_links_stmt).all())
        self._delete_links_and_flush(session, existing_links)

        # Create or get authors and create links
        for author_name in author_names:
            if not author_name.strip():
                continue
            # Find or create author
            author_stmt = select(Author).where(Author.name == author_name)
            author = session.exec(author_stmt).first()
            if author is None:
                author = Author(name=author_name)
                session.add(author)
                session.flush()
            if author.id is None:
                continue
            # Recreate link (we removed all links above)
            link = BookAuthorLink(book=book_id, author=author.id)
            session.add(link)

    def update_series(
        self,
        session: Session,
        book_id: int,
        series_name: str | None = None,
        series_id: int | None = None,
    ) -> None:
        """Update book series.

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Calibre book ID.
        series_name : str | None
            Series name to set (creates if doesn't exist).
        series_id : int | None
            Series ID to set (if provided, series_name is ignored).
        """
        # Get current series link
        current_link_stmt = select(BookSeriesLink).where(BookSeriesLink.book == book_id)
        current_link = session.exec(current_link_stmt).first()

        # Determine if we should remove series or set a new one
        should_remove = series_name == "" or (
            series_id is None and series_name is not None and not series_name.strip()
        )

        if should_remove:
            # Remove series - delete link if present
            self._delete_links_and_flush(
                session, [current_link] if current_link is not None else []
            )
            return

        # Determine target series ID
        target_series_id = series_id
        if target_series_id is None and series_name is not None and series_name.strip():
            # Find or create series
            series_stmt = select(Series).where(Series.name == series_name)
            series = session.exec(series_stmt).first()
            if series is None:
                series = Series(name=series_name)
                session.add(series)
                session.flush()
            if series.id is not None:
                target_series_id = series.id

        # Check if series is actually changing
        current_series_id = current_link.series if current_link else None
        if current_series_id == target_series_id:
            # Series hasn't changed, no update needed
            return

        # Series is changing - delete existing link if present
        self._delete_links_and_flush(
            session, [current_link] if current_link is not None else []
        )

        # Add new link if target series is specified
        if target_series_id is not None:
            link = BookSeriesLink(book=book_id, series=target_series_id)
            session.add(link)

    def update_tags(
        self,
        session: Session,
        book_id: int,
        tag_names: list[str],
    ) -> None:
        """Update book tags.

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Calibre book ID.
        tag_names : list[str]
            List of tag names to set (replaces existing).
        """
        # Get current tags
        current_tags_stmt = (
            select(Tag.name)
            .join(BookTagLink, Tag.id == BookTagLink.tag)
            .where(BookTagLink.book == book_id)
        )
        current_tag_names = self._normalize_string_set(
            list(session.exec(current_tags_stmt).all())
        )

        # Normalize new tag names
        normalized_new_tags = self._normalize_string_set(tag_names)

        # Check if tags are actually changing
        if current_tag_names == normalized_new_tags:
            # Tags haven't changed, no update needed
            return

        # Tags are changing - delete existing tag links
        delete_tags_stmt = select(BookTagLink).where(BookTagLink.book == book_id)
        existing_tag_links = list(session.exec(delete_tags_stmt).all())
        self._delete_links_and_flush(session, existing_tag_links)

        # Create or get tags and create links
        for tag_name in tag_names:
            if not tag_name.strip():
                continue
            tag_stmt = select(Tag).where(Tag.name == tag_name)
            tag = session.exec(tag_stmt).first()
            if tag is None:
                tag = Tag(name=tag_name)
                session.add(tag)
                session.flush()
            if tag.id is None:
                continue
            link = BookTagLink(book=book_id, tag=tag.id)
            session.add(link)

    def update_identifiers(
        self,
        session: Session,
        book_id: int,
        identifiers: list[dict[str, str]],
    ) -> None:
        """Update book identifiers.

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Calibre book ID.
        identifiers : list[dict[str, str]]
            List of identifiers with 'type' and 'val' keys (replaces existing).
        """
        # Get current identifiers
        current_identifiers_stmt = select(Identifier).where(Identifier.book == book_id)
        current_identifiers = session.exec(current_identifiers_stmt).all()
        current_identifiers_set = {
            (ident.type.lower().strip(), ident.val.strip())
            for ident in current_identifiers
            if ident.val.strip()
        }

        # Normalize new identifiers (type and val, filter empty)
        normalized_new_identifiers = {
            (
                ident_data.get("type", "isbn").lower().strip(),
                ident_data.get("val", "").strip(),
            )
            for ident_data in identifiers
            if ident_data.get("val", "").strip()
        }

        # Check if identifiers are actually changing
        if current_identifiers_set == normalized_new_identifiers:
            # Identifiers haven't changed, no update needed
            return

        # Identifiers are changing - delete existing identifiers
        self._delete_links_and_flush(session, list(current_identifiers))

        # Create new identifiers
        for ident_data in identifiers:
            ident_type = ident_data.get("type", "isbn")
            ident_val = ident_data.get("val", "")
            if ident_val.strip():
                ident = Identifier(book=book_id, type=ident_type, val=ident_val)
                session.add(ident)

    def update_publisher(
        self,
        session: Session,
        book_id: int,
        publisher_name: str | None = None,
        publisher_id: int | None = None,
    ) -> None:
        """Update book publisher.

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Calibre book ID.
        publisher_name : str | None
            Publisher name to set (creates if doesn't exist).
        publisher_id : int | None
            Publisher ID to set (if provided, publisher_name is ignored).
        """
        # Get current publisher link
        current_link_stmt = select(BookPublisherLink).where(
            BookPublisherLink.book == book_id
        )
        current_link = session.exec(current_link_stmt).first()

        # Determine target publisher ID
        target_publisher_id = publisher_id
        if target_publisher_id is None and publisher_name is not None:
            # Find or create publisher
            publisher_stmt = select(Publisher).where(Publisher.name == publisher_name)
            publisher = session.exec(publisher_stmt).first()
            if publisher is None:
                publisher = Publisher(name=publisher_name)
                session.add(publisher)
                session.flush()
            if publisher.id is not None:
                target_publisher_id = publisher.id

        # Check if publisher is actually changing
        current_publisher_id = current_link.publisher if current_link else None
        if current_publisher_id == target_publisher_id:
            # Publisher hasn't changed, no update needed
            return

        # Publisher is changing - delete existing link if present
        self._delete_links_and_flush(
            session, [current_link] if current_link is not None else []
        )

        # Add new link if target publisher is specified
        if target_publisher_id is not None:
            link = BookPublisherLink(book=book_id, publisher=target_publisher_id)
            session.add(link)

    def _get_current_language_ids(
        self, session: Session, book_id: int
    ) -> tuple[list[BookLanguageLink], set[int]]:
        """Get current language links and their IDs.

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Calibre book ID.

        Returns
        -------
        tuple[list[BookLanguageLink], set[int]]
            Tuple of (current links, set of language IDs).
        """
        current_links_stmt = select(BookLanguageLink).where(
            BookLanguageLink.book == book_id
        )
        current_links = list(session.exec(current_links_stmt).all())
        current_language_ids = {link.lang_code for link in current_links}
        return current_links, current_language_ids

    def _find_or_create_language(
        self, session: Session, lang_code: str
    ) -> Language | None:
        """Find or create a language by code.

        Parameters
        ----------
        session : Session
            Database session.
        lang_code : str
            Language code (ISO 639-1).

        Returns
        -------
        Language | None
            Language instance, or None if creation failed.
        """
        language_stmt = select(Language).where(Language.lang_code == lang_code)
        language = session.exec(language_stmt).first()
        if language is None:
            language = Language(lang_code=lang_code)
            session.add(language)
            session.flush()
        return language

    def _resolve_language_ids(
        self,
        session: Session,
        language_ids: list[int] | None = None,
        language_codes: list[str] | None = None,
    ) -> list[int]:
        """Resolve language_ids or language_codes to a list of language IDs.

        Parameters
        ----------
        session : Session
            Database session.
        language_ids : list[int] | None
            List of language IDs (takes priority).
        language_codes : list[str] | None
            List of language codes to resolve.

        Returns
        -------
        list[int]
            List of resolved language IDs.
        """
        if language_ids is not None:
            return language_ids

        if language_codes is None:
            return []

        target_language_ids: list[int] = []
        for lang_code in language_codes:
            language = self._find_or_create_language(session, lang_code)
            if language is not None and language.id is not None:
                target_language_ids.append(language.id)

        return target_language_ids

    def _remove_duplicate_ids(self, ids: list[int]) -> list[int]:
        """Remove duplicates from a list while preserving order.

        Parameters
        ----------
        ids : list[int]
            List of IDs that may contain duplicates.

        Returns
        -------
        list[int]
            List of unique IDs in original order.
        """
        seen: set[int] = set()
        unique_ids: list[int] = []
        for item_id in ids:
            if item_id not in seen:
                seen.add(item_id)
                unique_ids.append(item_id)
        return unique_ids

    def _delete_existing_language_links(
        self, session: Session, current_links: list[BookLanguageLink]
    ) -> None:
        """Delete existing language links.

        Parameters
        ----------
        session : Session
            Database session.
        current_links : list[BookLanguageLink]
            List of existing language links to delete.
        """
        for link in current_links:
            session.delete(link)
        session.flush()

    def _create_language_links(
        self, session: Session, book_id: int, language_ids: list[int]
    ) -> None:
        """Create new language links.

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Calibre book ID.
        language_ids : list[int]
            List of language IDs to create links for.
        """
        for order, target_language_id in enumerate(language_ids):
            existing_link_stmt = select(BookLanguageLink).where(
                BookLanguageLink.book == book_id,
                BookLanguageLink.lang_code == target_language_id,
            )
            existing_link = session.exec(existing_link_stmt).first()
            if existing_link is None:
                link = BookLanguageLink(
                    book=book_id,
                    lang_code=target_language_id,
                    item_order=order,
                )
                session.add(link)

    def update_languages(
        self,
        session: Session,
        book_id: int,
        language_codes: list[str] | None = None,
        language_ids: list[int] | None = None,
    ) -> None:
        """Update book languages.

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Calibre book ID.
        language_codes : list[str] | None
            List of language codes to set (creates if doesn't exist).
        language_ids : list[int] | None
            List of language IDs to set (if provided, language_codes is ignored).
        """
        current_links, current_language_ids = self._get_current_language_ids(
            session, book_id
        )

        target_language_ids = self._resolve_language_ids(
            session, language_ids, language_codes
        )
        target_language_ids = self._remove_duplicate_ids(target_language_ids)

        if set(target_language_ids) == current_language_ids:
            return

        self._delete_existing_language_links(session, current_links)
        self._create_language_links(session, book_id, target_language_ids)

    def update_rating(
        self,
        session: Session,
        book_id: int,
        rating_value: int | None = None,
        rating_id: int | None = None,
    ) -> None:
        """Update book rating.

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Calibre book ID.
        rating_value : int | None
            Rating value to set (creates if doesn't exist).
        rating_id : int | None
            Rating ID to set (if provided, rating_value is ignored).
        """
        # Get current rating link
        current_link_stmt = select(BookRatingLink).where(BookRatingLink.book == book_id)
        current_link = session.exec(current_link_stmt).first()

        # Determine target rating ID
        target_rating_id = rating_id
        if target_rating_id is None and rating_value is not None:
            # Find or create rating
            rating_stmt = select(Rating).where(Rating.rating == rating_value)
            rating = session.exec(rating_stmt).first()
            if rating is None:
                rating = Rating(rating=rating_value)
                session.add(rating)
                session.flush()
            if rating.id is not None:
                target_rating_id = rating.id

        # Check if rating is actually changing
        current_rating_id = current_link.rating if current_link else None
        if current_rating_id == target_rating_id:
            # Rating hasn't changed, no update needed
            return

        # Rating is changing - delete existing link if present
        self._delete_links_and_flush(
            session, [current_link] if current_link is not None else []
        )

        # Add new link if target rating is specified
        if target_rating_id is not None:
            link = BookRatingLink(book=book_id, rating=target_rating_id)
            session.add(link)

    def add_metadata(
        self,
        session: Session,
        book_id: int,
        metadata: BookMetadata,
    ) -> None:
        """Add all metadata relationships to a book.

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Book ID.
        metadata : BookMetadata
            Extracted book metadata.
        """
        # Add description if available
        if metadata.description:
            comment = Comment(book=book_id, text=metadata.description)
            session.add(comment)

        # Add tags if available
        if metadata.tags:
            self._add_book_tags(session, book_id, metadata.tags)

        # Add publisher if available
        if metadata.publisher:
            self._add_book_publisher(session, book_id, metadata.publisher)

        # Add identifiers if available
        if metadata.identifiers:
            self._add_book_identifiers(session, book_id, metadata.identifiers)

        # Add languages if available
        if metadata.languages:
            self._add_book_languages(session, book_id, metadata.languages)

        # Add series if available
        if metadata.series:
            self._add_book_series(session, book_id, metadata.series)

        # Add additional contributors
        if metadata.contributors:
            self._add_book_contributors(session, book_id, metadata.contributors)

    def _add_book_tags(
        self, session: Session, book_id: int, tag_names: list[str]
    ) -> None:
        """Add tags to a book.

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Book ID.
        tag_names : list[str]
            List of tag names to add.
        """
        for tag_name in tag_names:
            if not tag_name.strip():
                continue
            tag_stmt = select(Tag).where(Tag.name == tag_name)
            tag = session.exec(tag_stmt).first()
            if tag is None:
                tag = Tag(name=tag_name)
                session.add(tag)
                session.flush()
            if tag.id is not None:
                link_stmt = select(BookTagLink).where(
                    BookTagLink.book == book_id, BookTagLink.tag == tag.id
                )
                existing_link = session.exec(link_stmt).first()
                if existing_link is None:
                    link = BookTagLink(book=book_id, tag=tag.id)
                    session.add(link)

    def _add_book_publisher(
        self, session: Session, book_id: int, publisher_name: str
    ) -> None:
        """Add publisher to a book.

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Book ID.
        publisher_name : str
            Publisher name.
        """
        pub_stmt = select(Publisher).where(Publisher.name == publisher_name)
        publisher = session.exec(pub_stmt).first()
        if publisher is None:
            publisher = Publisher(name=publisher_name, sort=publisher_name)
            session.add(publisher)
            session.flush()
        if publisher.id is not None:
            link_stmt = select(BookPublisherLink).where(
                BookPublisherLink.book == book_id,
                BookPublisherLink.publisher == publisher.id,
            )
            existing_link = session.exec(link_stmt).first()
            if existing_link is None:
                link = BookPublisherLink(book=book_id, publisher=publisher.id)
                session.add(link)

    def _add_book_identifiers(
        self, session: Session, book_id: int, identifiers: list[dict[str, str]]
    ) -> None:
        """Add identifiers to a book.

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Book ID.
        identifiers : list[dict[str, str]]
            List of identifiers with 'type' and 'val' keys.
        """
        # Deduplicate by type - keep the first occurrence of each type
        # to avoid UNIQUE constraint violations
        # Note: Calibre allows multiple identifier types (isbn10, isbn13, asin, etc.)
        # but only one identifier per type per book (UNIQUE constraint on book+type)
        seen_types: set[str] = set()
        unique_identifiers: list[dict[str, str]] = []
        for ident_data in identifiers:
            ident_type = ident_data.get("type", "isbn")
            if ident_type not in seen_types:
                seen_types.add(ident_type)
                unique_identifiers.append(ident_data)

        for ident_data in unique_identifiers:
            ident_type = ident_data.get("type", "isbn")
            ident_val = ident_data.get("val", "")
            if not ident_val.strip():
                continue

            # Check if identifier with this type already exists for this book
            # (UNIQUE constraint on book+type)
            existing_stmt = select(Identifier).where(
                Identifier.book == book_id, Identifier.type == ident_type
            )
            existing = session.exec(existing_stmt).first()

            if existing is None:
                # Create new identifier
                ident = Identifier(book=book_id, type=ident_type, val=ident_val)
                session.add(ident)
            else:
                # Update existing identifier value
                existing.val = ident_val

    def _add_book_languages(
        self, session: Session, book_id: int, language_codes: list[str]
    ) -> None:
        """Add languages to a book.

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Book ID.
        language_codes : list[str]
            List of language codes.
        """
        for lang_code in language_codes:
            if not lang_code.strip():
                continue
            lang = self._find_or_create_language(session, lang_code)
            if lang is None or lang.id is None:
                continue
            link_stmt = select(BookLanguageLink).where(
                BookLanguageLink.book == book_id,
                BookLanguageLink.lang_code == lang.id,
            )
            existing_link = session.exec(link_stmt).first()
            if existing_link is None:
                link = BookLanguageLink(book=book_id, lang_code=lang.id, item_order=0)
                session.add(link)

    def _add_book_series(
        self, session: Session, book_id: int, series_name: str
    ) -> None:
        """Add series to a book.

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Book ID.
        series_name : str
            Series name.
        """
        series_stmt = select(Series).where(Series.name == series_name)
        series = session.exec(series_stmt).first()
        if series is None:
            series = Series(name=series_name, sort=series_name)
            session.add(series)
            session.flush()
        if series.id is not None:
            link_stmt = select(BookSeriesLink).where(
                BookSeriesLink.book == book_id, BookSeriesLink.series == series.id
            )
            existing_link = session.exec(link_stmt).first()
            if existing_link is None:
                link = BookSeriesLink(book=book_id, series=series.id)
                session.add(link)

    def _add_book_contributors(
        self, session: Session, book_id: int, contributors: list
    ) -> None:
        """Add additional contributors as authors.

        Calibre doesn't have separate contributor roles, so we add
        non-author contributors as additional authors.

        Parameters
        ----------
        session : Session
            Database session.
        book_id : int
            Book ID.
        contributors : list
            List of Contributor objects from metadata.
        """
        for contributor in contributors:
            # Skip if already added as primary author or if role is 'author'
            if contributor.role and contributor.role != "author" and contributor.name:
                # Add as additional author (Calibre limitation)
                author = self._get_or_create_author(session, contributor.name)
                # Check if link already exists
                link_stmt = select(BookAuthorLink).where(
                    BookAuthorLink.book == book_id, BookAuthorLink.author == author.id
                )
                existing_link = session.exec(link_stmt).first()
                if existing_link is None:
                    link = BookAuthorLink(book=book_id, author=author.id)
                    session.add(link)

    def _get_or_create_author(self, session: Session, author_name: str) -> Author:
        """Get existing author or create a new one.

        Parameters
        ----------
        session : Session
            Database session.
        author_name : str
            Author name.

        Returns
        -------
        Author
            Author instance with valid ID.

        Raises
        ------
        ValueError
            If author creation fails.
        """
        author_stmt = select(Author).where(Author.name == author_name)
        author = session.exec(author_stmt).first()
        if author is None:
            author = Author(name=author_name, sort=author_name)
            session.add(author)
            session.flush()

        if author.id is None:
            msg = "Failed to create author"
            raise ValueError(msg)

        return author
