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

"""OPDS feed service.

Orchestrates feed generation by coordinating book queries and XML building.
"""

import logging
from datetime import UTC, datetime

from fastapi import Request
from sqlmodel import Session

from bookcard.api.schemas.opds import (
    OpdsEntry,
    OpdsFeedRequest,
    OpdsFeedResponse,
    OpdsLink,
)
from bookcard.models.auth import User
from bookcard.models.config import Library
from bookcard.services.book_service import BookService
from bookcard.services.opds.book_query_service import OpdsBookQueryService
from bookcard.services.opds.interfaces import IOpdsFeedService
from bookcard.services.opds.url_builder import OpdsUrlBuilder
from bookcard.services.opds.xml_builder import OpdsXmlBuilder

logger = logging.getLogger(__name__)


class OpdsFeedService(IOpdsFeedService):
    """Service for generating OPDS feeds.

    Orchestrates book queries and XML generation to produce OPDS-compliant feeds.
    Follows SRP by coordinating specialized services.
    """

    def __init__(
        self,
        session: Session,  # type: ignore[type-arg]
        library: Library,
        xml_builder: OpdsXmlBuilder | None = None,
        book_query_service: OpdsBookQueryService | None = None,
    ) -> None:
        """Initialize OPDS feed service.

        Parameters
        ----------
        session : Session
            Database session.
        library : Library
            Active Calibre library configuration.
        xml_builder : OpdsXmlBuilder | None
            Optional XML builder (creates default if None).
        book_query_service : OpdsBookQueryService | None
            Optional book query service (creates default if None).
        """
        self._session = session
        self._library = library
        self._xml_builder = xml_builder or OpdsXmlBuilder()
        self._book_query_service = book_query_service or OpdsBookQueryService(
            session, library
        )
        self._book_service = BookService(library, session=session)

    def generate_catalog_feed(
        self,
        request: Request,
        user: User | None,
    ) -> OpdsFeedResponse:
        """Generate main catalog feed.

        Parameters
        ----------
        request : Request
            FastAPI request object.
        user : User | None
            Authenticated user.

        Returns
        -------
        OpdsFeedResponse
            Generated feed response.
        """
        url_builder = OpdsUrlBuilder(request)
        base_url = str(request.base_url).rstrip("/")

        # Build navigation links
        links = [
            {
                "href": url_builder.build_opds_url("/opds/books"),
                "rel": "subsection",
                "type": "application/atom+xml;profile=opds-catalog",
                "title": "All Books",
            },
            {
                "href": url_builder.build_opds_url("/opds/new"),
                "rel": "subsection",
                "type": "application/atom+xml;profile=opds-catalog",
                "title": "Recently Added",
            },
            {
                "href": url_builder.build_opds_url("/opds/discover"),
                "rel": "subsection",
                "type": "application/atom+xml;profile=opds-catalog",
                "title": "Discover",
            },
            {
                "href": url_builder.build_opds_url("/opds/search?query={searchTerms}"),
                "rel": "search",
                "type": "application/atom+xml",
                "title": "Search",
            },
        ]

        # Fetch recent books for the acquisition feed (top 20)
        books, _ = self._book_query_service.get_recent_books(
            user=user,
            page=1,
            page_size=20,
        )
        entries = self._build_entries(request, books)

        feed_id = f"{base_url}/opds/"
        title = f"Calibre Library - {self._library.name}"
        updated = datetime.now(UTC).isoformat()

        xml_content = self._xml_builder.build_feed(
            title=title,
            feed_id=feed_id,
            updated=updated,
            entries=entries,
            links=links,
        )

        return OpdsFeedResponse(xml_content=xml_content)

    def generate_books_feed(
        self, request: Request, user: User | None, feed_request: OpdsFeedRequest
    ) -> OpdsFeedResponse:
        """Generate books listing feed.

        Parameters
        ----------
        request : Request
            FastAPI request object.
        user : User | None
            Authenticated user or None.
        feed_request : OpdsFeedRequest
            Feed request parameters.

        Returns
        -------
        OpdsFeedResponse
            Generated feed response.
        """
        # Calculate page from offset
        page = (feed_request.offset // feed_request.page_size) + 1

        books, total = self._book_query_service.get_books(
            user=user,
            page=page,
            page_size=feed_request.page_size,
        )

        return self._build_books_feed(
            request, books, total, feed_request, "/opds/books", "All Books"
        )

    def generate_new_feed(
        self, request: Request, user: User | None, feed_request: OpdsFeedRequest
    ) -> OpdsFeedResponse:
        """Generate recently added books feed.

        Parameters
        ----------
        request : Request
            FastAPI request object.
        user : User | None
            Authenticated user or None.
        feed_request : OpdsFeedRequest
            Feed request parameters.

        Returns
        -------
        OpdsFeedResponse
            Generated feed response.
        """
        page = (feed_request.offset // feed_request.page_size) + 1

        books, total = self._book_query_service.get_recent_books(
            user=user,
            page=page,
            page_size=feed_request.page_size,
        )

        return self._build_books_feed(
            request, books, total, feed_request, "/opds/new", "Recently Added"
        )

    def generate_discover_feed(
        self, request: Request, user: User | None, feed_request: OpdsFeedRequest
    ) -> OpdsFeedResponse:
        """Generate random book discovery feed.

        Parameters
        ----------
        request : Request
            FastAPI request object.
        user : User | None
            Authenticated user or None.
        feed_request : OpdsFeedRequest
            Feed request parameters.

        Returns
        -------
        OpdsFeedResponse
            Generated feed response.
        """
        books = self._book_query_service.get_random_books(
            user=user,
            limit=feed_request.page_size,
        )

        entries = self._build_entries(request, books)
        base_url = str(request.base_url).rstrip("/")

        feed_id = f"{base_url}/opds/discover"
        title = "Discover - Random Books"
        updated = datetime.now(UTC).isoformat()

        xml_content = self._xml_builder.build_feed(
            title=title,
            feed_id=feed_id,
            updated=updated,
            entries=entries,
            links=None,
        )

        return OpdsFeedResponse(xml_content=xml_content)

    def generate_search_feed(
        self,
        request: Request,
        user: User | None,
        query: str | None,
        feed_request: OpdsFeedRequest,
    ) -> OpdsFeedResponse:
        """Generate search results feed.

        Parameters
        ----------
        request : Request
            FastAPI request object.
        user : User | None
            Authenticated user or None.
        query : str | None
            Search query string.
        feed_request : OpdsFeedRequest
            Feed request parameters.

        Returns
        -------
        OpdsFeedResponse
            Generated feed response.
        """
        # Handle empty query by returning empty feed
        if not query or not query.strip():
            return self._build_books_feed(
                request,
                books=[],
                total=0,
                feed_request=feed_request,
                path="/opds/search",
                title="Search",
                query=None,
            )

        page = (feed_request.offset // feed_request.page_size) + 1

        books, total = self._book_query_service.search_books(
            user=user,
            query=query,
            page=page,
            page_size=feed_request.page_size,
        )

        return self._build_books_feed(
            request,
            books,
            total,
            feed_request,
            "/opds/search",
            f"Search: {query}",
            query=query,
        )

    def generate_opensearch_description(self, request: Request) -> OpdsFeedResponse:
        """Generate OpenSearch description XML.

        Parameters
        ----------
        request : Request
            FastAPI request object.

        Returns
        -------
        OpdsFeedResponse
            OpenSearch description XML.
        """
        base_url = str(request.base_url).rstrip("/")

        # OpenSearch Description XML
        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">
    <ShortName>Calibre Library Search</ShortName>
    <Description>Search books in Calibre library</Description>
    <Url type="application/atom+xml;profile=opds-catalog" template="{base_url}/opds/search?query={{searchTerms}}"/>
    <Url type="text/html" template="{base_url}/opds/search?query={{searchTerms}}"/>
</OpenSearchDescription>"""

        return OpdsFeedResponse(
            xml_content=xml_content,
            content_type="application/opensearchdescription+xml",
        )

    def _build_books_feed(
        self,
        request: Request,
        books: list,
        total: int,
        feed_request: OpdsFeedRequest,
        path: str,
        title: str,
        query: str | None = None,
    ) -> OpdsFeedResponse:
        """Build books feed with pagination.

        Parameters
        ----------
        request : Request
            FastAPI request object.
        books : list
            List of books.
        total : int
            Total number of books.
        feed_request : OpdsFeedRequest
            Feed request parameters.
        path : str
            Feed path.
        title : str
            Feed title.
        query : str | None
            Optional search query.

        Returns
        -------
        OpdsFeedResponse
            Generated feed response.
        """
        entries = self._build_entries(request, books)
        url_builder = OpdsUrlBuilder(request)
        base_url = str(request.base_url).rstrip("/")

        # Build pagination links
        links = []
        current_page = (feed_request.offset // feed_request.page_size) + 1
        total_pages = (total + feed_request.page_size - 1) // feed_request.page_size

        # Self link
        query_params: dict[str, str | int] = {
            "offset": feed_request.offset,
            "page_size": feed_request.page_size,
        }
        if query:
            query_params["query"] = query
        links.append({
            "href": url_builder.build_opds_url(path, query_params),
            "rel": "self",
            "type": "application/atom+xml;profile=opds-catalog",
        })

        # First page
        if current_page > 1:
            first_offset = 0
            first_params = {"offset": first_offset, "page_size": feed_request.page_size}
            if query:
                first_params["query"] = query
            links.append({
                "href": url_builder.build_opds_url(path, first_params),
                "rel": "first",
                "type": "application/atom+xml;profile=opds-catalog",
            })

        # Previous page
        if current_page > 1:
            prev_offset = feed_request.offset - feed_request.page_size
            prev_params = {"offset": prev_offset, "page_size": feed_request.page_size}
            if query:
                prev_params["query"] = query
            links.append({
                "href": url_builder.build_opds_url(path, prev_params),
                "rel": "previous",
                "type": "application/atom+xml;profile=opds-catalog",
            })

        # Next page
        if current_page < total_pages:
            next_offset = feed_request.offset + feed_request.page_size
            next_params = {"offset": next_offset, "page_size": feed_request.page_size}
            if query:
                next_params["query"] = query
            links.append({
                "href": url_builder.build_opds_url(path, next_params),
                "rel": "next",
                "type": "application/atom+xml;profile=opds-catalog",
            })

        feed_id = f"{base_url}{path}"
        updated = datetime.now(UTC).isoformat()

        xml_content = self._xml_builder.build_feed(
            title=title,
            feed_id=feed_id,
            updated=updated,
            entries=entries,
            links=links,
        )

        return OpdsFeedResponse(xml_content=xml_content)

    def _build_entries(self, request: Request, books: list) -> list[OpdsEntry]:
        """Build OPDS entries from books.

        Parameters
        ----------
        request : Request
            FastAPI request object.
        books : list
            List of BookWithRelations.

        Returns
        -------
        list[OpdsEntry]
            List of OPDS entries.
        """
        url_builder = OpdsUrlBuilder(request)
        base_url = str(request.base_url).rstrip("/")
        entries: list[OpdsEntry] = []

        logger.info("Building OPDS entries for %s books", len(books))

        for book_with_rels in books:
            book = book_with_rels.book
            if book.id is None:
                continue

            # Log book title for debugging
            logger.info(
                "OPDS Entry: id=%s, title='%s', virtual=%s",
                book.id,
                book.title,
                getattr(book_with_rels, "is_virtual", False),
            )

            # Build entry ID using URN UUID to match Calibre-Web-Automated
            # This prevents browsers/readers from trying to navigate to it as a URL
            if book.uuid:
                entry_id = f"urn:uuid:{book.uuid}"
            else:
                # Fallback to URL-based ID if UUID missing (should be rare)
                entry_id = f"{base_url}/opds/books/{book.id}"

            # Build links
            links: list[OpdsLink] = []

            # Cover image link
            if book.has_cover:
                cover_url = url_builder.build_cover_url(book.id)
                links.append(
                    OpdsLink(
                        href=cover_url,
                        rel="http://opds-spec.org/image",
                        type="image/jpeg",
                    )
                )
                links.append(
                    OpdsLink(
                        href=cover_url,
                        rel="http://opds-spec.org/image/thumbnail",
                        type="image/jpeg",
                    )
                )

            # Download links
            if book_with_rels.formats:
                for fmt in book_with_rels.formats:
                    fmt_name = str(fmt.get("format", "")).upper()
                    if not fmt_name:
                        continue

                    download_url = url_builder.build_download_url(book.id, fmt_name)
                    # Get media type for format (you might want to import helper or duplicate logic)
                    # Simple mapping for common formats
                    media_type_map = {
                        "EPUB": "application/epub+zip",
                        "PDF": "application/pdf",
                        "MOBI": "application/x-mobipocket-ebook",
                        "AZW3": "application/vnd.amazon.ebook",
                        "CBZ": "application/vnd.comicbook+zip",
                        "CBR": "application/vnd.comicbook-rar",
                    }
                    media_type = media_type_map.get(
                        fmt_name, "application/octet-stream"
                    )

                    links.append(
                        OpdsLink(
                            href=download_url,
                            rel="http://opds-spec.org/acquisition",
                            type=media_type,
                            title=f"Download {fmt_name}",
                        )
                    )

            # Build published date
            published = None
            if book.pubdate:
                published = book.pubdate.isoformat()

            # Build updated date
            updated = (
                book.last_modified.isoformat()
                if book.last_modified
                else datetime.now(UTC).isoformat()
            )

            # Build summary (description)
            # Try to get description from relations if available (BookWithFullRelations)
            summary = getattr(book_with_rels, "description", None)

            # Build identifier (ISBN)
            identifier = book.isbn if book.isbn else None

            # Ensure title is populated (fallback to Unknown if empty/None)
            title = book.title if book.title else "Unknown"

            entry = OpdsEntry(
                id=entry_id,
                title=title,
                authors=book_with_rels.authors,
                updated=updated,
                summary=summary,
                links=links,
                published=published,
                identifier=identifier,
                series=book_with_rels.series,
                series_index=book.series_index,
            )

            entries.append(entry)

        return entries

    def generate_books_by_letter_feed(
        self,
        request: Request,
        user: User | None,
        letter: str,
        feed_request: OpdsFeedRequest,
    ) -> OpdsFeedResponse:
        """Generate books feed filtered by first letter.

        Parameters
        ----------
        request : Request
            FastAPI request object.
        user : User | None
            Authenticated user or None.
        letter : str
            First letter of book title sort (or "00" for all).
        feed_request : OpdsFeedRequest
            Feed request parameters.

        Returns
        -------
        OpdsFeedResponse
            Generated feed response.
        """
        # Convert offset to page
        page = (feed_request.offset // feed_request.page_size) + 1

        # Get books - for letter filtering, we'd need to filter by title_sort
        # For now, get all books and filter client-side (not ideal but works)
        books, total = self._book_query_service.get_books(
            user=user,
            page=page,
            page_size=feed_request.page_size,
            sort_by="title_sort",
            sort_order="asc",
        )

        # Filter by first letter if not "00"
        if letter != "00":
            filtered_books = []
            letter_upper = letter.upper()
            for book in books:
                title_sort = getattr(book.book, "title_sort", None)
                if title_sort:
                    first_char = title_sort[0].upper()
                    if first_char == letter_upper:
                        filtered_books.append(book)
            books = filtered_books
            total = len(filtered_books)

        entries = self._build_entries(request, books)
        url_builder = OpdsUrlBuilder(request)
        base_url = str(request.base_url).rstrip("/")

        feed_id = f"{base_url}/opds/books/letter/{letter}"
        title = f"Books - {letter if letter != '00' else 'All'}"
        updated = datetime.now(UTC).isoformat()

        # Build pagination links
        links = self._build_pagination_links(
            url_builder,
            f"/opds/books/letter/{letter}",
            feed_request.offset,
            feed_request.page_size,
            total,
        )

        xml_content = self._xml_builder.build_feed(
            title=title,
            feed_id=feed_id,
            updated=updated,
            entries=entries,
            links=links,
        )

        return OpdsFeedResponse(xml_content=xml_content)

    def generate_rated_feed(
        self,
        request: Request,
        user: User | None,
        feed_request: OpdsFeedRequest,
    ) -> OpdsFeedResponse:
        """Generate best rated books feed.

        Parameters
        ----------
        request : Request
            FastAPI request object.
        user : User | None
            Authenticated user or None.
        feed_request : OpdsFeedRequest
            Feed request parameters.

        Returns
        -------
        OpdsFeedResponse
            Generated feed response.
        """
        # Convert offset to page
        page = (feed_request.offset // feed_request.page_size) + 1

        # Get best rated books (rating >= 9, which is 4.5 stars)
        books, total = self._book_query_service.get_best_rated_books(
            user=user,
            page=page,
            page_size=feed_request.page_size,
        )

        entries = self._build_entries(request, books)
        url_builder = OpdsUrlBuilder(request)
        base_url = str(request.base_url).rstrip("/")

        feed_id = f"{base_url}/opds/rated"
        title = "Best Rated Books"
        updated = datetime.now(UTC).isoformat()

        # Build pagination links
        links = self._build_pagination_links(
            url_builder,
            "/opds/rated",
            feed_request.offset,
            feed_request.page_size,
            total,
        )

        xml_content = self._xml_builder.build_feed(
            title=title,
            feed_id=feed_id,
            updated=updated,
            entries=entries,
            links=links,
        )

        return OpdsFeedResponse(xml_content=xml_content)

    def _build_pagination_links(
        self,
        url_builder: OpdsUrlBuilder,
        base_path: str,
        offset: int,
        page_size: int,
        total: int,
    ) -> list[dict[str, str]]:
        """Build pagination links for OPDS feed.

        Parameters
        ----------
        url_builder : OpdsUrlBuilder
            URL builder instance.
        base_path : str
            Base path for the feed.
        offset : int
            Current offset.
        page_size : int
            Page size.
        total : int
            Total number of items.

        Returns
        -------
        list[dict[str, str]]
            List of pagination link dictionaries.
        """
        links: list[dict[str, str]] = []

        # First page
        if offset > 0:
            links.append({
                "href": url_builder.build_opds_url(
                    f"{base_path}?offset=0&page_size={page_size}"
                ),
                "rel": "first",
                "type": "application/atom+xml;profile=opds-catalog",
            })

        # Previous page
        if offset >= page_size:
            prev_offset = offset - page_size
            links.append({
                "href": url_builder.build_opds_url(
                    f"{base_path}?offset={prev_offset}&page_size={page_size}"
                ),
                "rel": "previous",
                "type": "application/atom+xml;profile=opds-catalog",
            })

        # Next page
        if offset + page_size < total:
            next_offset = offset + page_size
            links.append({
                "href": url_builder.build_opds_url(
                    f"{base_path}?offset={next_offset}&page_size={page_size}"
                ),
                "rel": "next",
                "type": "application/atom+xml;profile=opds-catalog",
            })

        # Last page
        if offset + page_size < total:
            last_offset = ((total - 1) // page_size) * page_size
            links.append({
                "href": url_builder.build_opds_url(
                    f"{base_path}?offset={last_offset}&page_size={page_size}"
                ),
                "rel": "last",
                "type": "application/atom+xml;profile=opds-catalog",
            })

        return links

    # Index feed methods (lists of entities for browsing)
    def generate_author_index_feed(
        self,
        request: Request,
        feed_request: OpdsFeedRequest,
    ) -> OpdsFeedResponse:
        """Generate author index feed."""
        from sqlmodel import select

        from bookcard.models.core import Author, BookAuthorLink

        offset = feed_request.offset

        # Get distinct authors linked to books
        stmt = (
            select(Author)
            .join(BookAuthorLink, Author.id == BookAuthorLink.author)
            .group_by(Author.id)
            .order_by(Author.sort if Author.sort else Author.name)
            .limit(feed_request.page_size)
            .offset(offset)
        )
        authors = list(self._session.exec(stmt).all())

        # Build entries for authors (navigation entries)
        entries = self._build_author_entries(request, authors)
        url_builder = OpdsUrlBuilder(request)
        base_url = str(request.base_url).rstrip("/")

        feed_id = f"{base_url}/opds/author"
        title = "Authors"
        updated = datetime.now(UTC).isoformat()

        url_builder = OpdsUrlBuilder(request)
        links = self._build_pagination_links(
            url_builder,
            "/opds/author",
            feed_request.offset,
            feed_request.page_size,
            len(authors),
        )

        xml_content = self._xml_builder.build_feed(
            title=title, feed_id=feed_id, updated=updated, entries=entries, links=links
        )

        return OpdsFeedResponse(xml_content=xml_content)

    def generate_author_letter_feed(
        self,
        request: Request,
        letter: str,
        feed_request: OpdsFeedRequest,
    ) -> OpdsFeedResponse:
        """Generate authors by letter feed."""
        from sqlmodel import func, select, true

        from bookcard.models.core import Author, BookAuthorLink

        offset = feed_request.offset

        # Filter by first letter
        if letter == "00":
            letter_filter = true()
        else:
            letter_filter = func.upper(
                func.coalesce(Author.sort, Author.name)
            ).startswith(letter.upper())

        stmt = (
            select(Author)
            .join(BookAuthorLink, Author.id == BookAuthorLink.author)
            .where(letter_filter)
            .group_by(Author.id)
            .order_by(Author.sort if Author.sort else Author.name)
            .limit(feed_request.page_size)
            .offset(offset)
        )
        authors = list(self._session.exec(stmt).all())

        entries = self._build_author_entries(request, authors)
        url_builder = OpdsUrlBuilder(request)
        base_url = str(request.base_url).rstrip("/")

        feed_id = f"{base_url}/opds/author/letter/{letter}"
        title = f"Authors - {letter if letter != '00' else 'All'}"
        updated = datetime.now(UTC).isoformat()

        links = self._build_pagination_links(
            url_builder,
            f"/opds/author/letter/{letter}",
            feed_request.offset,
            feed_request.page_size,
            len(authors),
        )

        xml_content = self._xml_builder.build_feed(
            title=title, feed_id=feed_id, updated=updated, entries=entries, links=links
        )

        return OpdsFeedResponse(xml_content=xml_content)

    def generate_books_by_author_feed(
        self,
        request: Request,
        user: User | None,
        author_id: int,
        feed_request: OpdsFeedRequest,
    ) -> OpdsFeedResponse:
        """Generate books by author feed."""
        page = (feed_request.offset // feed_request.page_size) + 1

        books, total = self._book_query_service.get_books_by_filter(
            user=user,
            page=page,
            page_size=feed_request.page_size,
            author_ids=[author_id],
            sort_by="timestamp",
            sort_order="desc",
        )

        entries = self._build_entries(request, books)
        url_builder = OpdsUrlBuilder(request)
        base_url = str(request.base_url).rstrip("/")

        feed_id = f"{base_url}/opds/author/{author_id}"
        title = f"Books by Author {author_id}"
        updated = datetime.now(UTC).isoformat()

        links = self._build_pagination_links(
            url_builder,
            f"/opds/author/{author_id}",
            feed_request.offset,
            feed_request.page_size,
            total,
        )

        xml_content = self._xml_builder.build_feed(
            title=title, feed_id=feed_id, updated=updated, entries=entries, links=links
        )

        return OpdsFeedResponse(xml_content=xml_content)

    def _build_author_entries(self, request: Request, authors: list) -> list[OpdsEntry]:
        """Build OPDS entries for author index."""
        base_url = str(request.base_url).rstrip("/")
        entries: list[OpdsEntry] = []

        for author in authors:
            if author.id is None:
                continue

            entry_id = f"{base_url}/opds/author/{author.id}"
            author_name = author.name

            # Build link to author's books
            links = [
                OpdsLink(
                    href=f"{base_url}/opds/author/{author.id}",
                    rel="subsection",
                    type="application/atom+xml;profile=opds-catalog",
                    title=f"Books by {author_name}",
                )
            ]

            entry = OpdsEntry(
                id=entry_id,
                title=author_name,
                authors=[author_name],
                updated=datetime.now(UTC).isoformat(),
                summary=None,
                links=links,
            )

            entries.append(entry)

        return entries

    # Placeholder methods for other index feeds - implement similarly
    def generate_publisher_index_feed(self, request: Request) -> OpdsFeedResponse:
        """Generate publisher index feed."""
        # Similar to author index - implement with Publisher model
        return self._generate_generic_index_feed(request, "publisher", "Publishers")

    def generate_books_by_publisher_feed(
        self,
        request: Request,
        user: User | None,
        publisher_id: int,
        feed_request: OpdsFeedRequest,
    ) -> OpdsFeedResponse:
        """Generate books by publisher feed."""
        page = (feed_request.offset // feed_request.page_size) + 1

        books, total = self._book_query_service.get_books_by_filter(
            user=user,
            page=page,
            page_size=feed_request.page_size,
            publisher_ids=[publisher_id],
            sort_by="timestamp",
            sort_order="desc",
        )

        entries = self._build_entries(request, books)
        url_builder = OpdsUrlBuilder(request)
        base_url = str(request.base_url).rstrip("/")

        feed_id = f"{base_url}/opds/publisher/{publisher_id}"
        title = f"Books by Publisher {publisher_id}"
        updated = datetime.now(UTC).isoformat()

        links = self._build_pagination_links(
            url_builder,
            f"/opds/publisher/{publisher_id}",
            feed_request.offset,
            feed_request.page_size,
            total,
        )

        xml_content = self._xml_builder.build_feed(
            title=title, feed_id=feed_id, updated=updated, entries=entries, links=links
        )

        return OpdsFeedResponse(xml_content=xml_content)

    def generate_category_index_feed(self, request: Request) -> OpdsFeedResponse:
        """Generate category/tag index feed."""
        return self._generate_generic_index_feed(request, "category", "Categories")

    def generate_category_letter_feed(
        self,
        request: Request,
        letter: str,
    ) -> OpdsFeedResponse:
        """Generate categories by letter feed."""
        # Similar to author letter feed - implement with Tag model
        return self._generate_generic_letter_feed(
            request, letter, "category", "Categories"
        )

    def generate_books_by_category_feed(
        self,
        request: Request,
        user: User | None,
        category_id: int,
        feed_request: OpdsFeedRequest,
    ) -> OpdsFeedResponse:
        """Generate books by category/tag feed."""
        page = (feed_request.offset // feed_request.page_size) + 1

        books, total = self._book_query_service.get_books_by_filter(
            user=user,
            page=page,
            page_size=feed_request.page_size,
            genre_ids=[category_id],
            sort_by="timestamp",
            sort_order="desc",
        )

        entries = self._build_entries(request, books)
        url_builder = OpdsUrlBuilder(request)
        base_url = str(request.base_url).rstrip("/")

        feed_id = f"{base_url}/opds/category/{category_id}"
        title = f"Books in Category {category_id}"
        updated = datetime.now(UTC).isoformat()

        links = self._build_pagination_links(
            url_builder,
            f"/opds/category/{category_id}",
            feed_request.offset,
            feed_request.page_size,
            total,
        )

        xml_content = self._xml_builder.build_feed(
            title=title, feed_id=feed_id, updated=updated, entries=entries, links=links
        )

        return OpdsFeedResponse(xml_content=xml_content)

    def generate_series_index_feed(self, request: Request) -> OpdsFeedResponse:
        """Generate series index feed."""
        return self._generate_generic_index_feed(request, "series", "Series")

    def generate_series_letter_feed(
        self,
        request: Request,
        letter: str,
    ) -> OpdsFeedResponse:
        """Generate series by letter feed."""
        return self._generate_generic_letter_feed(request, letter, "series", "Series")

    def generate_books_by_series_feed(
        self,
        request: Request,
        user: User | None,
        series_id: int,
        feed_request: OpdsFeedRequest,
    ) -> OpdsFeedResponse:
        """Generate books by series feed."""
        page = (feed_request.offset // feed_request.page_size) + 1

        books, total = self._book_query_service.get_books_by_filter(
            user=user,
            page=page,
            page_size=feed_request.page_size,
            series_ids=[series_id],
            sort_by="series_index",
            sort_order="asc",
        )

        entries = self._build_entries(request, books)
        url_builder = OpdsUrlBuilder(request)
        base_url = str(request.base_url).rstrip("/")

        feed_id = f"{base_url}/opds/series/{series_id}"
        title = f"Books in Series {series_id}"
        updated = datetime.now(UTC).isoformat()

        links = self._build_pagination_links(
            url_builder,
            f"/opds/series/{series_id}",
            feed_request.offset,
            feed_request.page_size,
            total,
        )

        xml_content = self._xml_builder.build_feed(
            title=title, feed_id=feed_id, updated=updated, entries=entries, links=links
        )

        return OpdsFeedResponse(xml_content=xml_content)

    def generate_rating_index_feed(self, request: Request) -> OpdsFeedResponse:
        """Generate rating index feed."""
        return self._generate_generic_index_feed(request, "ratings", "Ratings")

    def generate_books_by_rating_feed(
        self,
        request: Request,
        user: User | None,
        rating_id: int,
        feed_request: OpdsFeedRequest,
    ) -> OpdsFeedResponse:
        """Generate books by rating feed."""
        page = (feed_request.offset // feed_request.page_size) + 1

        books, total = self._book_query_service.get_books_by_filter(
            user=user,
            page=page,
            page_size=feed_request.page_size,
            rating_ids=[rating_id],
            sort_by="timestamp",
            sort_order="desc",
        )

        entries = self._build_entries(request, books)
        url_builder = OpdsUrlBuilder(request)
        base_url = str(request.base_url).rstrip("/")

        feed_id = f"{base_url}/opds/ratings/{rating_id}"
        title = f"Books with Rating {rating_id}"
        updated = datetime.now(UTC).isoformat()

        links = self._build_pagination_links(
            url_builder,
            f"/opds/ratings/{rating_id}",
            feed_request.offset,
            feed_request.page_size,
            total,
        )

        xml_content = self._xml_builder.build_feed(
            title=title, feed_id=feed_id, updated=updated, entries=entries, links=links
        )

        return OpdsFeedResponse(xml_content=xml_content)

    def generate_format_index_feed(self, request: Request) -> OpdsFeedResponse:
        """Generate format index feed."""
        return self._generate_generic_index_feed(request, "formats", "Formats")

    def generate_books_by_format_feed(
        self,
        request: Request,
        user: User | None,
        format_name: str,
        feed_request: OpdsFeedRequest,
    ) -> OpdsFeedResponse:
        """Generate books by format feed."""
        page = (feed_request.offset // feed_request.page_size) + 1

        books, total = self._book_query_service.get_books_by_filter(
            user=user,
            page=page,
            page_size=feed_request.page_size,
            formats=[format_name.upper()],
            sort_by="timestamp",
            sort_order="desc",
        )

        entries = self._build_entries(request, books)
        url_builder = OpdsUrlBuilder(request)
        base_url = str(request.base_url).rstrip("/")

        feed_id = f"{base_url}/opds/formats/{format_name}"
        title = f"Books in {format_name.upper()} Format"
        updated = datetime.now(UTC).isoformat()

        links = self._build_pagination_links(
            url_builder,
            f"/opds/formats/{format_name}",
            feed_request.offset,
            feed_request.page_size,
            total,
        )

        xml_content = self._xml_builder.build_feed(
            title=title, feed_id=feed_id, updated=updated, entries=entries, links=links
        )

        return OpdsFeedResponse(xml_content=xml_content)

    def generate_language_index_feed(self, request: Request) -> OpdsFeedResponse:
        """Generate language index feed."""
        return self._generate_generic_index_feed(request, "language", "Languages")

    def generate_books_by_language_feed(
        self,
        request: Request,
        user: User | None,
        language_id: int,
        feed_request: OpdsFeedRequest,
    ) -> OpdsFeedResponse:
        """Generate books by language feed."""
        page = (feed_request.offset // feed_request.page_size) + 1

        books, total = self._book_query_service.get_books_by_filter(
            user=user,
            page=page,
            page_size=feed_request.page_size,
            language_ids=[language_id],
            sort_by="timestamp",
            sort_order="desc",
        )

        entries = self._build_entries(request, books)
        url_builder = OpdsUrlBuilder(request)
        base_url = str(request.base_url).rstrip("/")

        feed_id = f"{base_url}/opds/language/{language_id}"
        title = f"Books in Language {language_id}"
        updated = datetime.now(UTC).isoformat()

        links = self._build_pagination_links(
            url_builder,
            f"/opds/language/{language_id}",
            feed_request.offset,
            feed_request.page_size,
            total,
        )

        xml_content = self._xml_builder.build_feed(
            title=title, feed_id=feed_id, updated=updated, entries=entries, links=links
        )

        return OpdsFeedResponse(xml_content=xml_content)

    def generate_shelf_index_feed(self, request: Request) -> OpdsFeedResponse:
        """Generate shelf index feed."""
        # Implement with Shelf model from shelf repository
        return self._generate_generic_index_feed(request, "shelfindex", "Shelves")

    def generate_books_by_shelf_feed(
        self,
        request: Request,
        shelf_id: int,
    ) -> OpdsFeedResponse:
        """Generate books in shelf feed."""
        # Implement with Shelf repository to get books in shelf
        # For now, return empty feed
        entries: list[OpdsEntry] = []
        base_url = str(request.base_url).rstrip("/")

        feed_id = f"{base_url}/opds/shelf/{shelf_id}"
        title = f"Books in Shelf {shelf_id}"
        updated = datetime.now(UTC).isoformat()

        links: list[dict[str, str]] = []

        xml_content = self._xml_builder.build_feed(
            title=title, feed_id=feed_id, updated=updated, entries=entries, links=links
        )

        return OpdsFeedResponse(xml_content=xml_content)

    def generate_hot_feed(
        self, request: Request, user: User | None, feed_request: OpdsFeedRequest
    ) -> OpdsFeedResponse:
        """Generate hot/popular books feed (most downloaded)."""
        # For now, return recent books as placeholder
        # Full implementation would query download statistics
        return self.generate_new_feed(request, user, feed_request)

    def generate_read_books_feed(self, request: Request) -> OpdsFeedResponse:
        """Generate read books feed."""
        # Implement with ReadStatus repository
        # For now, return empty feed
        entries: list[OpdsEntry] = []
        base_url = str(request.base_url).rstrip("/")

        feed_id = f"{base_url}/opds/readbooks"
        title = "Read Books"
        updated = datetime.now(UTC).isoformat()

        links: list[dict[str, str]] = []

        xml_content = self._xml_builder.build_feed(
            title=title, feed_id=feed_id, updated=updated, entries=entries, links=links
        )

        return OpdsFeedResponse(xml_content=xml_content)

    def generate_unread_books_feed(self, request: Request) -> OpdsFeedResponse:
        """Generate unread books feed."""
        # Implement with ReadStatus repository
        # For now, return empty feed
        entries: list[OpdsEntry] = []
        base_url = str(request.base_url).rstrip("/")

        feed_id = f"{base_url}/opds/unreadbooks"
        title = "Unread Books"
        updated = datetime.now(UTC).isoformat()

        links: list[dict[str, str]] = []

        xml_content = self._xml_builder.build_feed(
            title=title, feed_id=feed_id, updated=updated, entries=entries, links=links
        )

        return OpdsFeedResponse(xml_content=xml_content)

    # Helper methods
    def _generate_generic_index_feed(
        self,
        request: Request,
        path: str,
        title: str,
    ) -> OpdsFeedResponse:
        """Generate generic index feed."""
        entries: list[OpdsEntry] = []
        base_url = str(request.base_url).rstrip("/")

        feed_id = f"{base_url}/opds/{path}"
        updated = datetime.now(UTC).isoformat()

        links: list[dict[str, str]] = []

        xml_content = self._xml_builder.build_feed(
            title=title, feed_id=feed_id, updated=updated, entries=entries, links=links
        )

        return OpdsFeedResponse(xml_content=xml_content)

    def _generate_generic_letter_feed(
        self,
        request: Request,
        letter: str,
        path: str,
        title: str,
    ) -> OpdsFeedResponse:
        """Generate generic letter-based index feed."""
        entries: list[OpdsEntry] = []
        base_url = str(request.base_url).rstrip("/")

        feed_id = f"{base_url}/opds/{path}/letter/{letter}"
        feed_title = f"{title} - {letter if letter != '00' else 'All'}"
        updated = datetime.now(UTC).isoformat()

        links: list[dict[str, str]] = []

        xml_content = self._xml_builder.build_feed(
            title=feed_title,
            feed_id=feed_id,
            updated=updated,
            entries=entries,
            links=links,
        )

        return OpdsFeedResponse(xml_content=xml_content)
