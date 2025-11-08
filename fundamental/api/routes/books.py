# The MIT License (MIT)

# Copyright (c) 2025 knguyen and others

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Book endpoints: list, search, and retrieve books from Calibre library."""

from __future__ import annotations

import math
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import FileResponse
from sqlmodel import Session

from fundamental.api.deps import get_db_session
from fundamental.api.schemas import BookListResponse, BookRead
from fundamental.repositories.config_repository import LibraryRepository
from fundamental.services.book_service import BookService
from fundamental.services.config_service import LibraryService

router = APIRouter(prefix="/books", tags=["books"])

SessionDep = Annotated[Session, Depends(get_db_session)]


def _get_active_library_service(
    session: SessionDep,
) -> BookService:
    """Get book service for the active library.

    Parameters
    ----------
    session : SessionDep
        Database session.

    Returns
    -------
    BookService
        Book service instance.

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

    return BookService(library)


@router.get("", response_model=BookListResponse)
def list_books(
    session: SessionDep,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    sort_by: str = "timestamp",
    sort_order: str = "desc",
) -> BookListResponse:
    """List books with pagination and optional search.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    page : int
        Page number (1-indexed, default: 1).
    page_size : int
        Number of items per page (default: 20, max: 100).
    search : str | None
        Optional search query to filter by title or author.
    sort_by : str
        Field to sort by: 'timestamp', 'pubdate', 'title', 'author_sort',
        'series_index' (default: 'timestamp').
    sort_order : str
        Sort order: 'asc' or 'desc' (default: 'desc').

    Returns
    -------
    BookListResponse
        Paginated list of books.

    Raises
    ------
    HTTPException
        If no active library is configured (404).
    """
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 20
    if page_size > 100:
        page_size = 100

    book_service = _get_active_library_service(session)
    books, total = book_service.list_books(
        page=page,
        page_size=page_size,
        search_query=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    # Convert to BookRead with thumbnail URLs
    book_reads = []
    for book_with_rels in books:
        book = book_with_rels.book
        # Skip books without IDs (should not happen in Calibre, but type safety)
        if book.id is None:
            continue
        thumbnail_url = book_service.get_thumbnail_url(book_with_rels)
        book_read = BookRead(
            id=book.id,
            title=book.title,
            authors=book_with_rels.authors,
            author_sort=book.author_sort,
            pubdate=book.pubdate,
            timestamp=book.timestamp,
            series=book_with_rels.series,
            series_index=book.series_index,
            isbn=book.isbn,
            uuid=book.uuid or "",
            thumbnail_url=thumbnail_url,
            has_cover=book.has_cover,
        )
        book_reads.append(book_read)

    total_pages = math.ceil(total / page_size) if page_size > 0 else 0

    return BookListResponse(
        items=book_reads,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{book_id}", response_model=BookRead)
def get_book(
    session: SessionDep,
    book_id: int,
) -> BookRead:
    """Get a book by ID.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    book_id : int
        Calibre book ID.

    Returns
    -------
    BookRead
        Book data.

    Raises
    ------
    HTTPException
        If book not found (404) or no active library (404).
    """
    book_service = _get_active_library_service(session)
    book_with_rels = book_service.get_book(book_id)

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
    thumbnail_url = book_service.get_thumbnail_url(book_with_rels)
    return BookRead(
        id=book.id,
        title=book.title,
        authors=book_with_rels.authors,
        author_sort=book.author_sort,
        pubdate=book.pubdate,
        timestamp=book.timestamp,
        series=book_with_rels.series,
        series_index=book.series_index,
        isbn=book.isbn,
        uuid=book.uuid or "",
        thumbnail_url=thumbnail_url,
        has_cover=book.has_cover,
    )


@router.get("/{book_id}/cover", response_model=None)
def get_book_cover(
    session: SessionDep,
    book_id: int,
) -> FileResponse | Response:
    """Get book cover thumbnail image.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    book_id : int
        Calibre book ID.

    Returns
    -------
    FileResponse | Response
        Cover image file or 404 response.

    Raises
    ------
    HTTPException
        If book not found (404) or no active library (404).
    """
    book_service = _get_active_library_service(session)
    book_with_rels = book_service.get_book(book_id)

    if book_with_rels is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="book_not_found",
        )

    cover_path = book_service.get_thumbnail_path(book_with_rels)
    book_id_for_filename = book_with_rels.book.id
    if cover_path is None or not cover_path.exists():
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    return FileResponse(
        path=str(cover_path),
        media_type="image/jpeg",
        filename=f"cover_{book_id_for_filename}.jpg",
    )
