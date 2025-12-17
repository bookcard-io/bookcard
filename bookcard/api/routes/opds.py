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

"""OPDS feed endpoints.

Routes handle only HTTP concerns: request/response, status codes, exceptions.
Business logic is delegated to services following SOLID principles.
"""

import json
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import FileResponse
from fastapi.responses import Response as FastAPIResponse
from sqlmodel import Session, col, func, select

from bookcard.api.deps import get_db_session, get_opds_user
from bookcard.api.schemas.opds import OpdsFeedRequest
from bookcard.models.auth import User
from bookcard.models.config import Library
from bookcard.models.core import Book, BookAuthorLink, BookSeriesLink, BookTagLink
from bookcard.repositories.config_repository import LibraryRepository
from bookcard.services.book_permission_helper import BookPermissionHelper
from bookcard.services.book_service import BookService
from bookcard.services.config_service import LibraryService
from bookcard.services.opds.feed_service import OpdsFeedService
from bookcard.services.permission_service import PermissionService

router = APIRouter(prefix="/opds", tags=["opds"])

SessionDep = Annotated[Session, Depends(get_db_session)]
OpdsUserDep = Annotated[User | None, Depends(get_opds_user)]


def _check_opds_read_permission(
    user: User | None,
    session: Session,
) -> None:
    """Check books:read permission for OPDS user.

    Parameters
    ----------
    user : User | None
        Authenticated user.
    session : Session
        Database session.

    Raises
    ------
    HTTPException
        If user is None (401) or lacks books:read permission (403).
    """
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="authentication_required",
            headers={"WWW-Authenticate": "Basic"},
        )

    permission_service = PermissionService(session)
    if not permission_service.has_permission(user, "books", "read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="permission_denied: books:read",
        )


def _get_opds_feed_service(
    session: SessionDep,
) -> OpdsFeedService:
    """Get OPDS feed service for the active library.

    Parameters
    ----------
    session : SessionDep
        Database session.

    Returns
    -------
    OpdsFeedService
        OPDS feed service instance.

    Raises
    ------
    HTTPException
        If no active library is configured (404).
    """
    library_repo = LibraryRepository(session)
    library_service = LibraryService(session, library_repo)
    library = library_service.get_active_library()

    if library is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no_active_library",
        )

    return OpdsFeedService(session, library)


@router.get("/", response_class=FastAPIResponse)
def feed_index(
    request: Request,
    session: SessionDep,
    opds_user: OpdsUserDep,
) -> Response:
    """Return the root OPDS catalog feed with navigation links.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session.
    opds_user : User | None
        Authenticated user.

    Returns
    -------
    Response
        OPDS XML feed.
    """
    _check_opds_read_permission(opds_user, session)
    feed_service = _get_opds_feed_service(session)
    feed_response = feed_service.generate_catalog_feed(request)

    return Response(
        content=feed_response.xml_content,
        media_type=feed_response.content_type,
    )


@router.get("/books", response_class=FastAPIResponse)
def feed_books(
    request: Request,
    session: SessionDep,
    opds_user: OpdsUserDep,
    offset: int = Query(default=0, ge=0),
    page_size: int = Query(default=20, ge=1, le=100),
) -> Response:
    """Book listings feed.

    Returns paginated list of all books.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session.
    opds_user : User | None
        Authenticated user (required for book access).
    offset : int
        Pagination offset (OPDS standard).
    page_size : int
        Number of items per page.

    Returns
    -------
    Response
        OPDS XML feed.

    Raises
    ------
    HTTPException
        If user is not authenticated (401).
    """
    _check_opds_read_permission(opds_user, session)
    feed_service = _get_opds_feed_service(session)
    feed_request = OpdsFeedRequest(offset=offset, page_size=page_size)
    feed_response = feed_service.generate_books_feed(request, opds_user, feed_request)

    return Response(
        content=feed_response.xml_content,
        media_type=feed_response.content_type,
    )


@router.get("/new", response_class=FastAPIResponse)
def feed_new(
    request: Request,
    session: SessionDep,
    opds_user: OpdsUserDep,
    offset: int = Query(default=0, ge=0),
    page_size: int = Query(default=20, ge=1, le=100),
) -> Response:
    """Recently added books feed.

    Returns paginated list of recently added books.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session.
    opds_user : User | None
        Authenticated user (required for book access).
    offset : int
        Pagination offset (OPDS standard).
    page_size : int
        Number of items per page.

    Returns
    -------
    Response
        OPDS XML feed.

    Raises
    ------
    HTTPException
        If user is not authenticated (401).
    """
    _check_opds_read_permission(opds_user, session)
    feed_service = _get_opds_feed_service(session)
    feed_request = OpdsFeedRequest(offset=offset, page_size=page_size)
    feed_response = feed_service.generate_new_feed(request, opds_user, feed_request)

    return Response(
        content=feed_response.xml_content,
        media_type=feed_response.content_type,
    )


@router.get("/discover", response_class=FastAPIResponse)
def feed_discover(
    request: Request,
    session: SessionDep,
    opds_user: OpdsUserDep,
    page_size: int = Query(default=20, ge=1, le=100),
) -> Response:
    """Random book discovery feed.

    Returns a random selection of books.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session.
    opds_user : User | None
        Authenticated user (required for book access).
    page_size : int
        Number of items to return.

    Returns
    -------
    Response
        OPDS XML feed.

    Raises
    ------
    HTTPException
        If user is not authenticated (401).
    """
    _check_opds_read_permission(opds_user, session)
    feed_service = _get_opds_feed_service(session)
    feed_request = OpdsFeedRequest(offset=0, page_size=page_size)
    feed_response = feed_service.generate_discover_feed(
        request, opds_user, feed_request
    )

    return Response(
        content=feed_response.xml_content,
        media_type=feed_response.content_type,
    )


@router.get("/search", response_class=FastAPIResponse)
def feed_search(
    request: Request,
    session: SessionDep,
    opds_user: OpdsUserDep,
    query: str = Query(..., min_length=1),
    offset: int = Query(default=0, ge=0),
    page_size: int = Query(default=20, ge=1, le=100),
) -> Response:
    """Search functionality feed.

    Returns search results for the given query.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session.
    opds_user : User | None
        Authenticated user (required for book access).
    query : str
        Search query string.
    offset : int
        Pagination offset (OPDS standard).
    page_size : int
        Number of items per page.

    Returns
    -------
    Response
        OPDS XML feed.

    Raises
    ------
    HTTPException
        If user is not authenticated (401).
    """
    _check_opds_read_permission(opds_user, session)
    feed_service = _get_opds_feed_service(session)
    feed_request = OpdsFeedRequest(offset=offset, page_size=page_size)
    feed_response = feed_service.generate_search_feed(
        request, opds_user, query, feed_request
    )

    return Response(
        content=feed_response.xml_content,
        media_type=feed_response.content_type,
    )


@router.get("/osd", response_class=FastAPIResponse)
def feed_osd(
    request: Request,
    session: SessionDep,
    opds_user: OpdsUserDep,
) -> Response:
    """OpenSearch description XML.

    Returns OpenSearch description document for OPDS search.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session.
    opds_user : User | None
        Authenticated user.

    Returns
    -------
    Response
        OpenSearch description XML.
    """
    _check_opds_read_permission(opds_user, session)
    feed_service = _get_opds_feed_service(session)
    feed_response = feed_service.generate_opensearch_description(request)

    return Response(
        content=feed_response.xml_content,
        media_type=feed_response.content_type,
    )


@router.get("/search/{query:path}", response_class=FastAPIResponse)
def feed_search_path(
    request: Request,
    session: SessionDep,
    opds_user: OpdsUserDep,
    query: str,
    offset: int = Query(default=0, ge=0),
    page_size: int = Query(default=20, ge=1, le=100),
) -> Response:
    """Alternative search route with path parameter.

    Handles search queries from e-readers that use path-based search URLs.
    Handles + instead of spaces in query string.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session.
    opds_user : User | None
        Authenticated user (required for book access).
    query : str
        Search query string (may contain + instead of spaces).
    offset : int
        Pagination offset (OPDS standard).
    page_size : int
        Number of items per page.

    Returns
    -------
    Response
        OPDS XML feed.
    """
    # Replace + with spaces (common in e-reader queries)
    normalized_query = query.replace("+", " ").strip()

    if not normalized_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="query_required",
        )

    _check_opds_read_permission(opds_user, session)
    feed_service = _get_opds_feed_service(session)
    feed_request = OpdsFeedRequest(offset=offset, page_size=page_size)
    feed_response = feed_service.generate_search_feed(
        request, opds_user, normalized_query, feed_request
    )

    return Response(
        content=feed_response.xml_content,
        media_type=feed_response.content_type,
    )


@router.get("/books/letter/{letter}", response_class=FastAPIResponse)
def feed_books_letter(
    request: Request,
    session: SessionDep,
    opds_user: OpdsUserDep,
    letter: str,
    offset: int = Query(default=0, ge=0),
    page_size: int = Query(default=20, ge=1, le=100),
) -> Response:
    """Books by first letter feed.

    Returns books starting with the specified letter (or "00" for all).

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session.
    opds_user : User | None
        Authenticated user (required for book access).
    letter : str
        First letter of book title sort (or "00" for all).
    offset : int
        Pagination offset (OPDS standard).
    page_size : int
        Number of items per page.

    Returns
    -------
    Response
        OPDS XML feed.
    """
    _check_opds_read_permission(opds_user, session)
    feed_service = _get_opds_feed_service(session)
    feed_request = OpdsFeedRequest(offset=offset, page_size=page_size)
    feed_response = feed_service.generate_books_by_letter_feed(
        request, opds_user, letter, feed_request
    )

    return Response(
        content=feed_response.xml_content,
        media_type=feed_response.content_type,
    )


@router.get("/rated", response_class=FastAPIResponse)
def feed_rated(
    request: Request,
    session: SessionDep,
    opds_user: OpdsUserDep,
    offset: int = Query(default=0, ge=0),
    page_size: int = Query(default=20, ge=1, le=100),
) -> Response:
    """Best rated books feed.

    Returns books with high ratings (>= 4.5 stars).

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session.
    opds_user : User | None
        Authenticated user (required for book access).
    offset : int
        Pagination offset (OPDS standard).
    page_size : int
        Number of items per page.

    Returns
    -------
    Response
        OPDS XML feed.
    """
    _check_opds_read_permission(opds_user, session)
    feed_service = _get_opds_feed_service(session)
    feed_request = OpdsFeedRequest(offset=offset, page_size=page_size)
    feed_response = feed_service.generate_rated_feed(request, opds_user, feed_request)

    return Response(
        content=feed_response.xml_content,
        media_type=feed_response.content_type,
    )


def _get_opds_library_path(library: Library) -> Path:
    """Get library path from library configuration.

    Parameters
    ----------
    library : object
        Library configuration object.

    Returns
    -------
    Path
        Library root path.
    """
    lib_root = getattr(library, "library_root", None)
    if lib_root:
        return Path(lib_root)

    library_db_path = Path(library.calibre_db_path)
    return library_db_path.parent if library_db_path.is_file() else library_db_path


def _find_opds_format_data(
    formats: list[dict[str, str | int]] | None, format_name: str
) -> dict[str, str | int] | None:
    """Find format data in book formats list.

    Parameters
    ----------
    formats : list[dict[str, object]] | None
        List of format dictionaries.
    format_name : str
        Format name to find (case-insensitive).

    Returns
    -------
    dict[str, object] | None
        Format data if found, None otherwise.
    """
    if not formats:
        return None

    format_upper = format_name.upper()
    for fmt in formats:
        fmt_str = str(fmt.get("format", "")).upper()
        if fmt_str == format_upper:
            return fmt

    return None


def _get_opds_media_type(format_name: str) -> str:
    """Get media type for book format.

    Parameters
    ----------
    format_name : str
        Format name (e.g., 'EPUB', 'PDF').

    Returns
    -------
    str
        Media type string.
    """
    media_types = {
        "EPUB": "application/epub+zip",
        "PDF": "application/pdf",
        "MOBI": "application/x-mobipocket-ebook",
        "AZW3": "application/vnd.amazon.ebook",
    }
    return media_types.get(format_name.upper(), "application/octet-stream")


def _sanitize_opds_filename(
    authors: list[str], title: str, book_id: int, format_name: str
) -> str:
    """Sanitize filename for OPDS download.

    Parameters
    ----------
    authors : list[str]
        List of author names.
    title : str
        Book title.
    book_id : int
        Book ID.
    format_name : str
        File format name.

    Returns
    -------
    str
        Sanitized filename.
    """
    authors_str = ", ".join(authors) if authors else ""
    safe_author = (
        "".join(
            c for c in authors_str if c.isalnum() or c in (" ", "-", "_", ",")
        ).strip()
        or "Unknown"
    )
    safe_title = (
        "".join(c for c in title if c.isalnum() or c in (" ", "-", "_")).strip()
        or f"book_{book_id}"
    )
    return f"{safe_author} - {safe_title}.{format_name.lower()}"


def _find_opds_file_path(
    library_path: Path,
    book_path: str,
    format_data: dict[str, str | int],
    book_id: int,
    format_name: str,
) -> Path:
    """Find book file path with fallback.

    Parameters
    ----------
    library_path : Path
        Library root path.
    book_path : str
        Book relative path.
    format_data : dict[str, object]
        Format data dictionary.
    book_id : int
        Book ID.
    format_name : str
        Format name.

    Returns
    -------
    Path
        File path.

    Raises
    ------
    HTTPException
        If file not found.
    """
    full_book_path = library_path / book_path
    file_name = format_data.get("name") or f"{book_id}.{format_name.lower()}"
    file_path = full_book_path / file_name

    if file_path.exists():
        return file_path

    # Try alternative
    alt_file_name = f"{book_id}.{format_name.lower()}"
    alt_file_path = full_book_path / alt_file_name
    if alt_file_path.exists():
        return alt_file_path

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="file_not_found",
    )


@router.get("/download/{book_id}/{book_format}", response_class=FastAPIResponse)
def opds_download(
    session: SessionDep,
    opds_user: OpdsUserDep,
    book_id: int,
    book_format: str,
) -> Response:
    """Download book file via OPDS.

    Parameters
    ----------
    session : SessionDep
        Database session.
    opds_user : User | None
        Authenticated user (required for download).
    book_id : int
        Book ID.
    book_format : str
        File format (e.g., 'EPUB', 'PDF').

    Returns
    -------
    Response
        Book file or error response.
    """
    _check_opds_read_permission(opds_user, session)

    library_repo = LibraryRepository(session)
    library_service = LibraryService(session, library_repo)
    library = library_service.get_active_library()

    if library is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no_active_library",
        )

    book_service = BookService(library, session=session)
    book_with_rels = book_service.get_book_full(book_id)

    if book_with_rels is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="book_not_found",
        )

    book = book_with_rels.book
    if book.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="book_missing_id",
        )

    format_data = _find_opds_format_data(book_with_rels.formats, book_format)
    if format_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"format_not_found: {book_format.upper()}",
        )

    library_path = _get_opds_library_path(library)
    file_path = _find_opds_file_path(
        library_path, book.path, format_data, book_id, book_format
    )

    media_type = _get_opds_media_type(book_format)
    filename = _sanitize_opds_filename(
        book_with_rels.authors, book.title, book_id, book_format
    )

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename,
    )


@router.get("/cover/{book_id}", response_class=FastAPIResponse)
@router.get("/cover_90_90/{book_id}", response_class=FastAPIResponse)
@router.get("/cover_240_240/{book_id}", response_class=FastAPIResponse)
@router.get("/thumb_240_240/{book_id}", response_class=FastAPIResponse)
def opds_cover(
    session: SessionDep,
    opds_user: OpdsUserDep,
    book_id: int,
) -> Response:
    """Get book cover image via OPDS.

    Parameters
    ----------
    session : SessionDep
        Database session.
    opds_user : User | None
        Authenticated user (required for book access).
    book_id : int
        Book ID.

    Returns
    -------
    Response
        Cover image file or 404 response.
    """
    _check_opds_read_permission(opds_user, session)

    # Get library and services
    library_repo = LibraryRepository(session)
    library_service = LibraryService(session, library_repo)
    library = library_service.get_active_library()

    if library is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no_active_library",
        )

    book_service = BookService(library, session=session)
    book_with_rels = book_service.get_book(book_id)

    if book_with_rels is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    # Check permission
    permission_service = PermissionService(session)
    context = BookPermissionHelper.build_permission_context(book_with_rels)
    if not permission_service.has_permission(opds_user, "books", "read", context):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="permission_denied",
        )

    cover_path = book_service.get_thumbnail_path(book_with_rels)
    if cover_path is None or not cover_path.exists():
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    book_id_for_filename = book_with_rels.book.id or book_id

    return FileResponse(
        path=str(cover_path),
        media_type="image/jpeg",
        filename=f"cover_{book_id_for_filename}.jpg",
    )


@router.get("/stats", response_class=FastAPIResponse)
def opds_stats(
    session: SessionDep,
    opds_user: OpdsUserDep,
) -> Response:
    """Get database statistics.

    Returns JSON with library statistics.

    Parameters
    ----------
    session : SessionDep
        Database session.
    opds_user : User | None
        Authenticated user.

    Returns
    -------
    Response
        JSON response with statistics.
    """
    _check_opds_read_permission(opds_user, session)

    # Count books
    books_stmt = select(func.count(Book.id))
    total_books = session.exec(books_stmt).one() or 0

    # Count authors
    authors_stmt = select(func.count(func.distinct(BookAuthorLink.author)))
    total_authors = session.exec(authors_stmt).one() or 0

    # Count tags
    tags_stmt = select(func.count(func.distinct(BookTagLink.tag)))
    total_tags = session.exec(tags_stmt).one() or 0

    # Count series
    series_stmt = select(func.count(func.distinct(BookSeriesLink.series)))
    total_series = session.exec(series_stmt).one() or 0

    stats = {
        "books": total_books,
        "authors": total_authors,
        "categories": total_tags,
        "series": total_series,
    }

    return Response(
        content=json.dumps(stats),
        media_type="application/json",
    )


# Author routes
@router.get("/author", response_class=FastAPIResponse)
def feed_author_index(
    request: Request,
    session: SessionDep,
    opds_user: OpdsUserDep,
    offset: int = Query(default=0, ge=0),
    page_size: int = Query(default=20, ge=1, le=100),
) -> Response:
    """Return author index feed.

    Returns list of authors for browsing.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session.
    opds_user : User | None
        Authenticated user.
    offset : int
        Pagination offset.
    page_size : int
        Number of items per page.

    Returns
    -------
    Response
        OPDS XML feed.
    """
    _check_opds_read_permission(opds_user, session)
    feed_service = _get_opds_feed_service(session)
    feed_request = OpdsFeedRequest(offset=offset, page_size=page_size)
    feed_response = feed_service.generate_author_index_feed(request, feed_request)

    return Response(
        content=feed_response.xml_content,
        media_type=feed_response.content_type,
    )


@router.get("/author/letter/{letter}", response_class=FastAPIResponse)
def feed_author_letter(
    request: Request,
    session: SessionDep,
    opds_user: OpdsUserDep,
    letter: str,
    offset: int = Query(default=0, ge=0),
    page_size: int = Query(default=20, ge=1, le=100),
) -> Response:
    """Return authors by letter feed.

    Returns authors starting with the specified letter.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session.
    opds_user : User | None
        Authenticated user.
    letter : str
        First letter of author sort name.
    offset : int
        Pagination offset.
    page_size : int
        Number of items per page.

    Returns
    -------
    Response
        OPDS XML feed.
    """
    _check_opds_read_permission(opds_user, session)
    feed_service = _get_opds_feed_service(session)
    feed_request = OpdsFeedRequest(offset=offset, page_size=page_size)
    feed_response = feed_service.generate_author_letter_feed(
        request, letter, feed_request
    )

    return Response(
        content=feed_response.xml_content,
        media_type=feed_response.content_type,
    )


@router.get("/author/{author_id}", response_class=FastAPIResponse)
def feed_author(
    request: Request,
    session: SessionDep,
    opds_user: OpdsUserDep,
    author_id: int,
    offset: int = Query(default=0, ge=0),
    page_size: int = Query(default=20, ge=1, le=100),
) -> Response:
    """Books by author feed.

    Returns books by the specified author.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session.
    opds_user : User | None
        Authenticated user.
    author_id : int
        Author ID.
    offset : int
        Pagination offset.
    page_size : int
        Number of items per page.

    Returns
    -------
    Response
        OPDS XML feed.
    """
    _check_opds_read_permission(opds_user, session)
    feed_service = _get_opds_feed_service(session)
    feed_request = OpdsFeedRequest(offset=offset, page_size=page_size)
    feed_response = feed_service.generate_books_by_author_feed(
        request, opds_user, author_id, feed_request
    )

    return Response(
        content=feed_response.xml_content,
        media_type=feed_response.content_type,
    )


# Publisher routes
@router.get("/publisher", response_class=FastAPIResponse)
def feed_publisher_index(
    request: Request,
    session: SessionDep,
    opds_user: OpdsUserDep,
) -> Response:
    """Return publisher index feed.

    Returns list of publishers for browsing.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session.
    opds_user : User | None
        Authenticated user.
    offset : int
        Pagination offset.
    page_size : int
        Number of items per page.

    Returns
    -------
    Response
        OPDS XML feed.
    """
    _check_opds_read_permission(opds_user, session)
    feed_service = _get_opds_feed_service(session)
    feed_response = feed_service.generate_publisher_index_feed(request)

    return Response(
        content=feed_response.xml_content,
        media_type=feed_response.content_type,
    )


@router.get("/publisher/{publisher_id}", response_class=FastAPIResponse)
def feed_publisher(
    request: Request,
    session: SessionDep,
    opds_user: OpdsUserDep,
    publisher_id: int,
    offset: int = Query(default=0, ge=0),
    page_size: int = Query(default=20, ge=1, le=100),
) -> Response:
    """Books by publisher feed.

    Returns books by the specified publisher.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session.
    opds_user : User | None
        Authenticated user.
    publisher_id : int
        Publisher ID.
    offset : int
        Pagination offset.
    page_size : int
        Number of items per page.

    Returns
    -------
    Response
        OPDS XML feed.
    """
    _check_opds_read_permission(opds_user, session)
    feed_service = _get_opds_feed_service(session)
    feed_request = OpdsFeedRequest(offset=offset, page_size=page_size)
    feed_response = feed_service.generate_books_by_publisher_feed(
        request, opds_user, publisher_id, feed_request
    )

    return Response(
        content=feed_response.xml_content,
        media_type=feed_response.content_type,
    )


# Category/Tag routes
@router.get("/category", response_class=FastAPIResponse)
def feed_category_index(
    request: Request,
    session: SessionDep,
    opds_user: OpdsUserDep,
) -> Response:
    """Category/Tag index feed.

    Returns list of tags/categories for browsing.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session.
    opds_user : User | None
        Authenticated user.
    offset : int
        Pagination offset.
    page_size : int
        Number of items per page.

    Returns
    -------
    Response
        OPDS XML feed.
    """
    _check_opds_read_permission(opds_user, session)
    feed_service = _get_opds_feed_service(session)
    feed_response = feed_service.generate_category_index_feed(request)

    return Response(
        content=feed_response.xml_content,
        media_type=feed_response.content_type,
    )


@router.get("/category/letter/{letter}", response_class=FastAPIResponse)
def feed_category_letter(
    request: Request,
    session: SessionDep,
    opds_user: OpdsUserDep,
    letter: str,
) -> Response:
    """Categories by letter feed.

    Returns categories starting with the specified letter.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session.
    opds_user : User | None
        Authenticated user.
    letter : str
        First letter of category name.
    offset : int
        Pagination offset.
    page_size : int
        Number of items per page.

    Returns
    -------
    Response
        OPDS XML feed.
    """
    _check_opds_read_permission(opds_user, session)
    feed_service = _get_opds_feed_service(session)
    feed_response = feed_service.generate_category_letter_feed(request, letter)

    return Response(
        content=feed_response.xml_content,
        media_type=feed_response.content_type,
    )


@router.get("/category/{category_id}", response_class=FastAPIResponse)
def feed_category(
    request: Request,
    session: SessionDep,
    opds_user: OpdsUserDep,
    category_id: int,
    offset: int = Query(default=0, ge=0),
    page_size: int = Query(default=20, ge=1, le=100),
) -> Response:
    """Books by category/tag feed.

    Returns books with the specified tag/category.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session.
    opds_user : User | None
        Authenticated user.
    category_id : int
        Tag/Category ID.
    offset : int
        Pagination offset.
    page_size : int
        Number of items per page.

    Returns
    -------
    Response
        OPDS XML feed.
    """
    _check_opds_read_permission(opds_user, session)
    feed_service = _get_opds_feed_service(session)
    feed_request = OpdsFeedRequest(offset=offset, page_size=page_size)
    feed_response = feed_service.generate_books_by_category_feed(
        request, opds_user, category_id, feed_request
    )

    return Response(
        content=feed_response.xml_content,
        media_type=feed_response.content_type,
    )


# Series routes
@router.get("/series", response_class=FastAPIResponse)
def feed_series_index(
    request: Request,
    session: SessionDep,
    opds_user: OpdsUserDep,
) -> Response:
    """Series index feed.

    Returns list of series for browsing.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session.
    opds_user : User | None
        Authenticated user.
    offset : int
        Pagination offset.
    page_size : int
        Number of items per page.

    Returns
    -------
    Response
        OPDS XML feed.
    """
    _check_opds_read_permission(opds_user, session)
    feed_service = _get_opds_feed_service(session)
    feed_response = feed_service.generate_series_index_feed(request)

    return Response(
        content=feed_response.xml_content,
        media_type=feed_response.content_type,
    )


@router.get("/series/letter/{letter}", response_class=FastAPIResponse)
def feed_series_letter(
    request: Request,
    session: SessionDep,
    opds_user: OpdsUserDep,
    letter: str,
) -> Response:
    """Series by letter feed.

    Returns series starting with the specified letter.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session.
    opds_user : User | None
        Authenticated user.
    letter : str
        First letter of series sort name.
    offset : int
        Pagination offset.
    page_size : int
        Number of items per page.

    Returns
    -------
    Response
        OPDS XML feed.
    """
    _check_opds_read_permission(opds_user, session)
    feed_service = _get_opds_feed_service(session)
    feed_response = feed_service.generate_series_letter_feed(request, letter)

    return Response(
        content=feed_response.xml_content,
        media_type=feed_response.content_type,
    )


@router.get("/series/{series_id}", response_class=FastAPIResponse)
def feed_series(
    request: Request,
    session: SessionDep,
    opds_user: OpdsUserDep,
    series_id: int,
    offset: int = Query(default=0, ge=0),
    page_size: int = Query(default=20, ge=1, le=100),
) -> Response:
    """Books by series feed.

    Returns books in the specified series.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session.
    opds_user : User | None
        Authenticated user.
    series_id : int
        Series ID.
    offset : int
        Pagination offset.
    page_size : int
        Number of items per page.

    Returns
    -------
    Response
        OPDS XML feed.
    """
    _check_opds_read_permission(opds_user, session)
    feed_service = _get_opds_feed_service(session)
    feed_request = OpdsFeedRequest(offset=offset, page_size=page_size)
    feed_response = feed_service.generate_books_by_series_feed(
        request, opds_user, series_id, feed_request
    )

    return Response(
        content=feed_response.xml_content,
        media_type=feed_response.content_type,
    )


# Ratings routes
@router.get("/ratings", response_class=FastAPIResponse)
def feed_rating_index(
    request: Request,
    session: SessionDep,
    opds_user: OpdsUserDep,
) -> Response:
    """Rating index feed.

    Returns list of ratings for browsing.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session.
    opds_user : User | None
        Authenticated user.
    offset : int
        Pagination offset.
    page_size : int
        Number of items per page.

    Returns
    -------
    Response
        OPDS XML feed.
    """
    _check_opds_read_permission(opds_user, session)
    feed_service = _get_opds_feed_service(session)
    feed_response = feed_service.generate_rating_index_feed(request)

    return Response(
        content=feed_response.xml_content,
        media_type=feed_response.content_type,
    )


@router.get("/ratings/{rating_id}", response_class=FastAPIResponse)
def feed_ratings(
    request: Request,
    session: SessionDep,
    opds_user: OpdsUserDep,
    rating_id: int,
    offset: int = Query(default=0, ge=0),
    page_size: int = Query(default=20, ge=1, le=100),
) -> Response:
    """Books by rating feed.

    Returns books with the specified rating.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session.
    opds_user : User | None
        Authenticated user.
    rating_id : int
        Rating ID.
    offset : int
        Pagination offset.
    page_size : int
        Number of items per page.

    Returns
    -------
    Response
        OPDS XML feed.
    """
    _check_opds_read_permission(opds_user, session)
    feed_service = _get_opds_feed_service(session)
    feed_request = OpdsFeedRequest(offset=offset, page_size=page_size)
    feed_response = feed_service.generate_books_by_rating_feed(
        request, opds_user, rating_id, feed_request
    )

    return Response(
        content=feed_response.xml_content,
        media_type=feed_response.content_type,
    )


# Format routes
@router.get("/formats", response_class=FastAPIResponse)
def feed_format_index(
    request: Request,
    session: SessionDep,
    opds_user: OpdsUserDep,
) -> Response:
    """Format index feed.

    Returns list of available formats for browsing.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session.
    opds_user : User | None
        Authenticated user.
    offset : int
        Pagination offset.
    page_size : int
        Number of items per page.

    Returns
    -------
    Response
        OPDS XML feed.
    """
    _check_opds_read_permission(opds_user, session)
    feed_service = _get_opds_feed_service(session)
    feed_response = feed_service.generate_format_index_feed(request)

    return Response(
        content=feed_response.xml_content,
        media_type=feed_response.content_type,
    )


@router.get("/formats/{format_name}", response_class=FastAPIResponse)
def feed_format(
    request: Request,
    session: SessionDep,
    opds_user: OpdsUserDep,
    format_name: str,
    offset: int = Query(default=0, ge=0),
    page_size: int = Query(default=20, ge=1, le=100),
) -> Response:
    """Books by format feed.

    Returns books in the specified format.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session.
    opds_user : User | None
        Authenticated user.
    format_name : str
        Format name (e.g., 'EPUB', 'PDF').
    offset : int
        Pagination offset.
    page_size : int
        Number of items per page.

    Returns
    -------
    Response
        OPDS XML feed.
    """
    _check_opds_read_permission(opds_user, session)
    feed_service = _get_opds_feed_service(session)
    feed_request = OpdsFeedRequest(offset=offset, page_size=page_size)
    feed_response = feed_service.generate_books_by_format_feed(
        request, opds_user, format_name, feed_request
    )

    return Response(
        content=feed_response.xml_content,
        media_type=feed_response.content_type,
    )


# Language routes
@router.get("/language", response_class=FastAPIResponse)
def feed_language_index(
    request: Request,
    session: SessionDep,
    opds_user: OpdsUserDep,
) -> Response:
    """Language index feed.

    Returns list of languages for browsing.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session.
    opds_user : User | None
        Authenticated user.
    offset : int
        Pagination offset.
    page_size : int
        Number of items per page.

    Returns
    -------
    Response
        OPDS XML feed.
    """
    _check_opds_read_permission(opds_user, session)
    feed_service = _get_opds_feed_service(session)
    feed_response = feed_service.generate_language_index_feed(request)

    return Response(
        content=feed_response.xml_content,
        media_type=feed_response.content_type,
    )


@router.get("/language/{language_id}", response_class=FastAPIResponse)
def feed_language(
    request: Request,
    session: SessionDep,
    opds_user: OpdsUserDep,
    language_id: int,
    offset: int = Query(default=0, ge=0),
    page_size: int = Query(default=20, ge=1, le=100),
) -> Response:
    """Books by language feed.

    Returns books in the specified language.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session.
    opds_user : User | None
        Authenticated user.
    language_id : int
        Language ID.
    offset : int
        Pagination offset.
    page_size : int
        Number of items per page.

    Returns
    -------
    Response
        OPDS XML feed.
    """
    _check_opds_read_permission(opds_user, session)
    feed_service = _get_opds_feed_service(session)
    feed_request = OpdsFeedRequest(offset=offset, page_size=page_size)
    feed_response = feed_service.generate_books_by_language_feed(
        request, opds_user, language_id, feed_request
    )

    return Response(
        content=feed_response.xml_content,
        media_type=feed_response.content_type,
    )


# Shelf routes
@router.get("/shelfindex", response_class=FastAPIResponse)
def feed_shelf_index(
    request: Request,
    session: SessionDep,
    opds_user: OpdsUserDep,
) -> Response:
    """Shelf index feed.

    Returns list of shelves for browsing.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session.
    opds_user : User | None
        Authenticated user.
    offset : int
        Pagination offset.
    page_size : int
        Number of items per page.

    Returns
    -------
    Response
        OPDS XML feed.
    """
    _check_opds_read_permission(opds_user, session)
    feed_service = _get_opds_feed_service(session)
    feed_response = feed_service.generate_shelf_index_feed(request)

    return Response(
        content=feed_response.xml_content,
        media_type=feed_response.content_type,
    )


@router.get("/shelf/{shelf_id}", response_class=FastAPIResponse)
def feed_shelf(
    request: Request,
    session: SessionDep,
    opds_user: OpdsUserDep,
    shelf_id: int,
) -> Response:
    """Books in shelf feed.

    Returns books in the specified shelf.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session.
    opds_user : User | None
        Authenticated user.
    shelf_id : int
        Shelf ID.
    offset : int
        Pagination offset.
    page_size : int
        Number of items per page.

    Returns
    -------
    Response
        OPDS XML feed.
    """
    _check_opds_read_permission(opds_user, session)
    feed_service = _get_opds_feed_service(session)
    feed_response = feed_service.generate_books_by_shelf_feed(request, shelf_id)

    return Response(
        content=feed_response.xml_content,
        media_type=feed_response.content_type,
    )


# Other routes
@router.get("/hot", response_class=FastAPIResponse)
def feed_hot(
    request: Request,
    session: SessionDep,
    opds_user: OpdsUserDep,
    offset: int = Query(default=0, ge=0),
    page_size: int = Query(default=20, ge=1, le=100),
) -> Response:
    """Hot/popular books feed.

    Returns most downloaded books.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session.
    opds_user : User | None
        Authenticated user.
    offset : int
        Pagination offset.
    page_size : int
        Number of items per page.

    Returns
    -------
    Response
        OPDS XML feed.
    """
    _check_opds_read_permission(opds_user, session)
    feed_service = _get_opds_feed_service(session)
    feed_request = OpdsFeedRequest(offset=offset, page_size=page_size)
    feed_response = feed_service.generate_hot_feed(request, opds_user, feed_request)

    return Response(
        content=feed_response.xml_content,
        media_type=feed_response.content_type,
    )


@router.get("/readbooks", response_class=FastAPIResponse)
def feed_read_books(
    request: Request,
    session: SessionDep,
    opds_user: OpdsUserDep,
) -> Response:
    """Read books feed.

    Returns books marked as read by the user.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session.
    opds_user : User | None
        Authenticated user (required).
    offset : int
        Pagination offset.
    page_size : int
        Number of items per page.

    Returns
    -------
    Response
        OPDS XML feed.
    """
    _check_opds_read_permission(opds_user, session)
    feed_service = _get_opds_feed_service(session)
    feed_response = feed_service.generate_read_books_feed(request)

    return Response(
        content=feed_response.xml_content,
        media_type=feed_response.content_type,
    )


@router.get("/unreadbooks", response_class=FastAPIResponse)
def feed_unread_books(
    request: Request,
    session: SessionDep,
    opds_user: OpdsUserDep,
) -> Response:
    """Unread books feed.

    Returns books not yet read by the user.

    Parameters
    ----------
    request : Request
        FastAPI request object.
    session : SessionDep
        Database session.
    opds_user : User | None
        Authenticated user (required).
    offset : int
        Pagination offset.
    page_size : int
        Number of items per page.

    Returns
    -------
    Response
        OPDS XML feed.
    """
    _check_opds_read_permission(opds_user, session)
    feed_service = _get_opds_feed_service(session)
    feed_response = feed_service.generate_unread_books_feed(request)

    return Response(
        content=feed_response.xml_content,
        media_type=feed_response.content_type,
    )


# Calibre Companion endpoint
@router.get("/ajax/book/{uuid}", response_class=FastAPIResponse)
def get_metadata_calibre_companion(
    session: SessionDep,
    opds_user: OpdsUserDep,
    uuid: str,
) -> Response:
    """Calibre Companion metadata endpoint.

    Returns book metadata in JSON format for Calibre Companion app.

    Parameters
    ----------
    session : SessionDep
        Database session.
    opds_user : User | None
        Authenticated user.
    uuid : str
        Book UUID (partial match supported).

    Returns
    -------
    Response
        JSON response with book metadata.
    """
    _check_opds_read_permission(opds_user, session)

    # Find book by UUID (partial match)
    stmt = select(Book).where(col(Book.uuid).like(f"%{uuid}%"))
    book = session.exec(stmt).first()

    if book is None:
        return Response(
            content="",
            media_type="application/json",
        )

    # Build JSON response (simplified - full implementation would include all metadata)
    book_data = {
        "id": book.id,
        "title": book.title,
        "uuid": book.uuid,
        "timestamp": book.timestamp.isoformat() if book.timestamp else None,
        "pubdate": book.pubdate.isoformat() if book.pubdate else None,
    }

    return Response(
        content=json.dumps(book_data),
        media_type="application/json; charset=utf-8",
    )
