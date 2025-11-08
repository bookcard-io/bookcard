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
from fundamental.api.schemas import (
    BookFilterRequest,
    BookListResponse,
    BookRead,
    FilterSuggestionsResponse,
    SearchSuggestionItem,
    SearchSuggestionsResponse,
)
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


@router.get("/search/suggestions", response_model=SearchSuggestionsResponse)
def search_suggestions(
    session: SessionDep,
    q: str,
) -> SearchSuggestionsResponse:
    """Get search suggestions for autocomplete.

    Searches across book titles, authors, tags, and series.
    Returns top matches for each category.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    q : str
        Search query string.

    Returns
    -------
    SearchSuggestionsResponse
        Search suggestions grouped by type (books, authors, tags, series).

    Raises
    ------
    HTTPException
        If no active library is configured (404).
    """
    if not q or not q.strip():
        return SearchSuggestionsResponse()

    book_service = _get_active_library_service(session)
    results = book_service.search_suggestions(
        query=q,
        book_limit=5,
        author_limit=5,
        tag_limit=5,
        series_limit=5,
    )

    return SearchSuggestionsResponse(
        books=[
            SearchSuggestionItem(id=int(item["id"]), name=str(item["name"]))
            for item in results["books"]
        ],
        authors=[
            SearchSuggestionItem(id=int(item["id"]), name=str(item["name"]))
            for item in results["authors"]
        ],
        tags=[
            SearchSuggestionItem(id=int(item["id"]), name=str(item["name"]))
            for item in results["tags"]
        ],
        series=[
            SearchSuggestionItem(id=int(item["id"]), name=str(item["name"]))
            for item in results["series"]
        ],
    )


@router.get("/filter/suggestions", response_model=FilterSuggestionsResponse)
def filter_suggestions(
    session: SessionDep,
    q: str,
    filter_type: str,
    limit: int = 10,
) -> FilterSuggestionsResponse:
    """Get filter suggestions for a specific filter type.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    q : str
        Search query string.
    filter_type : str
        Type of filter: 'author', 'title', 'genre', 'publisher',
        'identifier', 'series', 'format', 'rating', 'language'.
    limit : int
        Maximum number of suggestions to return (default: 10).

    Returns
    -------
    FilterSuggestionsResponse
        Filter suggestions for the specified type.

    Raises
    ------
    HTTPException
        If no active library is configured (404).
    """
    if not q or not q.strip():
        return FilterSuggestionsResponse()

    book_service = _get_active_library_service(session)
    results = book_service.filter_suggestions(
        query=q,
        filter_type=filter_type,
        limit=limit,
    )

    return FilterSuggestionsResponse(
        suggestions=[
            SearchSuggestionItem(id=int(item["id"]), name=str(item["name"]))
            for item in results
        ]
    )


@router.post("/filter", response_model=BookListResponse)
def filter_books(
    session: SessionDep,
    filter_request: BookFilterRequest,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "timestamp",
    sort_order: str = "desc",
) -> BookListResponse:
    """Filter books with multiple criteria using OR conditions.

    Each filter type uses OR conditions (e.g., multiple authors = OR).
    Different filter types are combined with AND conditions.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    filter_request : BookFilterRequest
        Filter criteria.
    page : int
        Page number (1-indexed, default: 1).
    page_size : int
        Number of items per page (default: 20, max: 100).
    sort_by : str
        Field to sort by: 'timestamp', 'pubdate', 'title', 'author_sort',
        'series_index' (default: 'timestamp').
    sort_order : str
        Sort order: 'asc' or 'desc' (default: 'desc').

    Returns
    -------
    BookListResponse
        Paginated list of filtered books.

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
    books, total = book_service.list_books_with_filters(
        page=page,
        page_size=page_size,
        author_ids=filter_request.author_ids,
        title_ids=filter_request.title_ids,
        genre_ids=filter_request.genre_ids,
        publisher_ids=filter_request.publisher_ids,
        identifier_ids=filter_request.identifier_ids,
        series_ids=filter_request.series_ids,
        formats=filter_request.formats,
        rating_ids=filter_request.rating_ids,
        language_ids=filter_request.language_ids,
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
