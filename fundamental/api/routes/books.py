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

import hashlib
import io
import math
import tempfile
from pathlib import Path
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import FileResponse
from PIL import Image
from sqlmodel import Session

from fundamental.api.deps import get_db_session
from fundamental.api.schemas import (
    BookFilterRequest,
    BookListResponse,
    BookRead,
    BookUpdate,
    CoverFromUrlRequest,
    CoverFromUrlResponse,
    FilterSuggestionsResponse,
    SearchSuggestionItem,
    SearchSuggestionsResponse,
)
from fundamental.repositories.config_repository import LibraryRepository
from fundamental.services.book_service import BookService
from fundamental.services.config_service import LibraryService

router = APIRouter(prefix="/books", tags=["books"])

SessionDep = Annotated[Session, Depends(get_db_session)]

# Media types mapping for book file formats
FILE_FORMAT_MEDIA_TYPES = {
    "EPUB": "application/epub+zip",
    "PDF": "application/pdf",
    "MOBI": "application/x-mobipocket-ebook",
    "AZW3": "application/vnd.amazon.ebook",
    "FB2": "application/x-fictionbook+xml",
    "LIT": "application/x-ms-reader",
    "LRF": "application/x-sony-bbeb",
    "ODT": "application/vnd.oasis.opendocument.text",
    "RTF": "application/rtf",
    "TXT": "text/plain",
    "HTML": "text/html",
    "HTM": "text/html",
}


def _find_format_data(
    formats: list[dict[str, str | int]], requested_format: str
) -> tuple[dict[str, str | int] | None, list[str]]:
    """Find format data matching the requested format.

    Parameters
    ----------
    formats : list[dict[str, str | int]]
        List of format dictionaries from book data.
    requested_format : str
        Requested file format (e.g., 'EPUB', 'PDF').

    Returns
    -------
    tuple[dict[str, str | int] | None, list[str]]
        Tuple of (format data if found, list of available formats).
    """
    format_upper = requested_format.upper()
    available_formats = []
    format_data = None
    for fmt in formats:
        fmt_format = fmt.get("format", "")
        available_formats.append(str(fmt_format))
        if isinstance(fmt_format, str) and fmt_format.upper() == format_upper:
            format_data = fmt
    return format_data, available_formats


def _get_file_name(
    format_data: dict[str, str | int],
    book_id: int,
    file_format: str,
) -> str:
    """Get filename for the book file.

    Parameters
    ----------
    format_data : dict[str, str | int]
        Format data dictionary, may contain 'name' field.
    book_id : int
        Book ID for fallback naming.
    file_format : str
        File format extension.

    Returns
    -------
    str
        Filename for the book file.
    """
    file_name = format_data.get("name", "")
    if not file_name or not isinstance(file_name, str):
        # Calibre standard naming: {book_id}.{format_lower}
        return f"{book_id}.{file_format.lower()}"

    # Ensure filename has the correct extension
    expected_suffix = f".{file_format.lower()}"
    if not file_name.lower().endswith(expected_suffix):
        return f"{file_name}{expected_suffix}"
    return file_name


def _get_media_type(format_upper: str) -> str:
    """Get media type for file format.

    Parameters
    ----------
    format_upper : str
        File format in uppercase.

    Returns
    -------
    str
        Media type string.
    """
    return FILE_FORMAT_MEDIA_TYPES.get(format_upper, "application/octet-stream")


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
    full: bool = False,
) -> BookRead:
    """Get a book by ID.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    book_id : int
        Calibre book ID.
    full : bool
        If True, return full book details with all metadata (default: False).

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

    if full:
        book_with_rels = book_service.get_book_full(book_id)
    else:
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

    # Build base BookRead
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

    # Add full details if requested
    if full and hasattr(book_with_rels, "tags"):
        from fundamental.repositories.models import BookWithFullRelations

        if isinstance(book_with_rels, BookWithFullRelations):
            book_read.tags = book_with_rels.tags
            book_read.identifiers = book_with_rels.identifiers
            book_read.description = book_with_rels.description
            book_read.publisher = book_with_rels.publisher
            book_read.publisher_id = book_with_rels.publisher_id
            book_read.languages = book_with_rels.languages
            book_read.language_ids = book_with_rels.language_ids
            book_read.rating = book_with_rels.rating
            book_read.rating_id = book_with_rels.rating_id
            book_read.series_id = book_with_rels.series_id
            book_read.formats = book_with_rels.formats

    return book_read


@router.put("/{book_id}", response_model=BookRead)
def update_book(
    session: SessionDep,
    book_id: int,
    update: BookUpdate,
) -> BookRead:
    """Update book metadata.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    book_id : int
        Calibre book ID.
    update : BookUpdate
        Book update payload.

    Returns
    -------
    BookRead
        Updated book data with all metadata.

    Raises
    ------
    HTTPException
        If book not found (404) or no active library (404).
    """
    book_service = _get_active_library_service(session)

    # Check if book exists
    existing_book = book_service.get_book(book_id)
    if existing_book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="book_not_found",
        )

    # Update book
    updated_book = book_service.update_book(
        book_id=book_id,
        title=update.title,
        pubdate=update.pubdate,
        author_names=update.author_names,
        series_name=update.series_name,
        series_id=update.series_id,
        series_index=update.series_index,
        tag_names=update.tag_names,
        identifiers=update.identifiers,
        description=update.description,
        publisher_name=update.publisher_name,
        publisher_id=update.publisher_id,
        language_codes=update.language_codes,
        language_ids=update.language_ids,
        rating_value=update.rating_value,
        rating_id=update.rating_id,
    )

    if updated_book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="book_not_found",
        )

    book = updated_book.book
    if book.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="book_missing_id",
        )

    thumbnail_url = book_service.get_thumbnail_url(updated_book)

    return BookRead(
        id=book.id,
        title=book.title,
        authors=updated_book.authors,
        author_sort=book.author_sort,
        pubdate=book.pubdate,
        timestamp=book.timestamp,
        series=updated_book.series,
        series_id=updated_book.series_id,
        series_index=book.series_index,
        isbn=book.isbn,
        uuid=book.uuid or "",
        thumbnail_url=thumbnail_url,
        has_cover=book.has_cover,
        tags=updated_book.tags,
        identifiers=updated_book.identifiers,
        description=updated_book.description,
        publisher=updated_book.publisher,
        publisher_id=updated_book.publisher_id,
        languages=updated_book.languages,
        language_ids=updated_book.language_ids,
        rating=updated_book.rating,
        rating_id=updated_book.rating_id,
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


@router.get("/{book_id}/download/{file_format}", response_model=None)
def download_book_file(
    session: SessionDep,
    book_id: int,
    file_format: str,
) -> FileResponse | Response:
    """Download a book file in the specified format.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    book_id : int
        Calibre book ID.
    file_format : str
        File format (e.g., 'EPUB', 'PDF', 'MOBI').

    Returns
    -------
    FileResponse | Response
        Book file or 404 response.

    Raises
    ------
    HTTPException
        If book not found (404), format not found (404), or no active library (404).
    """
    from pathlib import Path

    book_service = _get_active_library_service(session)
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

    # Find the format in the book's formats
    format_upper = file_format.upper()
    format_data, available_formats = _find_format_data(
        book_with_rels.formats, file_format
    )

    if format_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"format_not_found: requested '{format_upper}', available: {available_formats}",
        )

    # Construct file path: library_root / book.path / file_name
    # Prefer explicit library_root from config when provided
    lib_root = getattr(book_service._library, "library_root", None)  # type: ignore[attr-defined]  # noqa: SLF001
    if lib_root:
        library_path = Path(lib_root)
    else:
        # Determine library root robustly from configured calibre_db_path
        library_db_path = book_service._library.calibre_db_path  # type: ignore[attr-defined]  # noqa: SLF001
        library_db_path_obj = Path(library_db_path)
        # If calibre_db_path points to a directory, use it directly.
        # If it points to a file (e.g., metadata.db), use its parent directory.
        if library_db_path_obj.is_dir():
            library_path = library_db_path_obj
        else:
            library_path = library_db_path_obj.parent
    book_path = library_path / book.path
    file_name = _get_file_name(format_data, book_id, file_format)
    file_path = book_path / file_name

    if not file_path.exists():
        # Try alternative: just the format extension
        alt_file_name = f"{book_id}.{file_format.lower()}"
        alt_file_path = book_path / alt_file_name
        if alt_file_path.exists():
            file_path = alt_file_path
            file_name = alt_file_name
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"file_not_found: tried {file_path} and {alt_file_path}",
            )

    # Determine media type based on format
    media_type = _get_media_type(format_upper)

    # Sanitize author name(s)
    authors_str = ", ".join(book_with_rels.authors) if book_with_rels.authors else ""
    safe_author = "".join(
        c for c in authors_str if c.isalnum() or c in (" ", "-", "_", ",")
    ).strip()
    if not safe_author:
        safe_author = "Unknown"

    # Use book title for filename, sanitized
    safe_title = "".join(
        c for c in book.title if c.isalnum() or c in (" ", "-", "_")
    ).strip()
    if not safe_title:
        safe_title = f"book_{book_id}"
    filename = f"{safe_author} - {safe_title}.{file_format.lower()}"

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename,
    )


# Temporary cover storage (in-memory for now, could be moved to disk/DB)
_temp_cover_storage: dict[str, Path] = {}


def _validate_cover_url_request(
    session: SessionDep,
    book_id: int,
    url: str,
) -> None:
    """Validate book existence and URL format.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    book_id : int
        Calibre book ID.
    url : str
        Image URL to validate.

    Raises
    ------
    HTTPException
        If book not found (404) or URL is invalid (400).
    """
    book_service = _get_active_library_service(session)
    book_with_rels = book_service.get_book(book_id)

    if book_with_rels is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="book_not_found",
        )

    if not url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="url_required",
        )

    if not url.startswith(("http://", "https://")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_url_format",
        )


def _download_and_validate_image(url: str) -> tuple[bytes, Image.Image]:
    """Download image from URL and validate it.

    Parameters
    ----------
    url : str
        Image URL to download.

    Returns
    -------
    tuple[bytes, Image.Image]
        Image content bytes and PIL Image object.

    Raises
    ------
    HTTPException
        If download fails (400) or image is invalid (400).
    """
    try:
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "").lower()
            if not content_type.startswith("image/"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="url_not_an_image",
                )

            try:
                image = Image.open(io.BytesIO(response.content))
                image.verify()
            except Exception as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="invalid_image_format",
                ) from exc
            else:
                # Reopen image after verify() closes it
                image = Image.open(io.BytesIO(response.content))
                return response.content, image
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"failed_to_download_image: {exc!s}",
        ) from exc


def _save_image_to_temp(content: bytes, image: Image.Image) -> str:
    """Save image to temporary location and return URL.

    Parameters
    ----------
    content : bytes
        Image content bytes.
    image : Image.Image
        PIL Image object.

    Returns
    -------
    str
        Temporary URL to access the image.
    """
    content_hash = hashlib.sha256(content).hexdigest()[:16]
    file_extension = image.format.lower() if image.format else "jpg"
    if file_extension not in ("jpg", "jpeg", "png", "webp"):
        file_extension = "jpg"

    temp_dir = Path(tempfile.gettempdir()) / "calibre_covers"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_filename = f"{content_hash}.{file_extension}"
    temp_path = temp_dir / temp_filename

    temp_path.write_bytes(content)
    _temp_cover_storage[content_hash] = temp_path

    return f"/api/books/temp-covers/{content_hash}.{file_extension}"


@router.post("/{book_id}/cover-from-url", response_model=CoverFromUrlResponse)
def download_cover_from_url(
    session: SessionDep,
    book_id: int,
    request: CoverFromUrlRequest,
) -> CoverFromUrlResponse:
    """Download cover image from URL and save to temporary location.

    Downloads an image from the provided URL, validates it's an image,
    saves it to a temporary location with a hash-based filename, and
    returns a URL to access it.

    Parameters
    ----------
    session : SessionDep
        Database session dependency.
    book_id : int
        Calibre book ID.
    request : CoverFromUrlRequest
        Request containing the image URL.

    Returns
    -------
    CoverFromUrlResponse
        Response containing temporary URL to access the downloaded image.

    Raises
    ------
    HTTPException
        If book not found (404), URL is invalid (400), image download fails (400),
        or image validation fails (400).
    """
    url = request.url.strip()
    _validate_cover_url_request(session, book_id, url)

    try:
        content, image = _download_and_validate_image(url)
        temp_url = _save_image_to_temp(content, image)
        return CoverFromUrlResponse(temp_url=temp_url)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"internal_error: {exc!s}",
        ) from exc


@router.get("/temp-covers/{hash_and_ext}", response_model=None)
def get_temp_cover(
    hash_and_ext: str,
) -> FileResponse | Response:
    """Serve temporary cover image.

    Parameters
    ----------
    hash_and_ext : str
        Hash and extension (e.g., "abc123def456.jpg").

    Returns
    -------
    FileResponse | Response
        Cover image file or 404 response.
    """
    # Extract hash from filename
    if "." not in hash_and_ext:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    content_hash = hash_and_ext.rsplit(".", 1)[0]

    if content_hash not in _temp_cover_storage:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    temp_path = _temp_cover_storage[content_hash]
    if not temp_path.exists():
        # Clean up stale entry
        _temp_cover_storage.pop(content_hash, None)
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    return FileResponse(
        path=str(temp_path),
        media_type="image/jpeg",
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
