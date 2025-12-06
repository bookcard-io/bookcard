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

"""Comic book endpoints for page access and metadata.

Routes handle comic book archive page extraction and serving.
Follows the same permission and authentication patterns as book endpoints.
"""

import io
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from PIL import Image  # type: ignore[import-untyped]
from sqlmodel import Session

from fundamental.api.deps import get_current_user, get_db_session
from fundamental.models.auth import User
from fundamental.repositories.config_repository import LibraryRepository
from fundamental.services.book_permission_helper import BookPermissionHelper
from fundamental.services.book_service import BookService
from fundamental.services.comic.comic_archive_service import (
    ComicArchiveService,
)
from fundamental.services.config_service import LibraryService

router = APIRouter(prefix="/comic", tags=["comic"])

SessionDep = Annotated[Session, Depends(get_db_session)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]


def _get_book_service(session: SessionDep) -> BookService:
    """Get book service with active library.

    Parameters
    ----------
    session : Session
        Database session.

    Returns
    -------
    BookService
        Book service instance.

    Raises
    ------
    HTTPException
        If no active library found.
    """
    library_repo = LibraryRepository(session)
    library_service = LibraryService(session, library_repo)
    library = library_service.get_active_library()

    if library is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="no_active_library",
        )

    return BookService(library, session=session)


def _find_format_data(
    formats: list[dict],
    file_format: str,
) -> dict:
    """Find format data matching the requested format.

    Parameters
    ----------
    formats : list[dict]
        List of format dictionaries from book.
    file_format : str
        File format to find (CBZ, CBR, CB7, CBC).

    Returns
    -------
    dict
        Format data dictionary.

    Raises
    ------
    HTTPException
        If format not found.
    """
    format_upper = file_format.upper()
    for fmt in formats:
        fmt_format = fmt.get("format")
        if isinstance(fmt_format, str) and fmt_format.upper() == format_upper:
            return fmt

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"format_not_found: {format_upper}",
    )


def _get_library_path(book_service: BookService) -> Path:
    """Get the library root path.

    Parameters
    ----------
    book_service : BookService
        Book service instance.

    Returns
    -------
    Path
        Library root path.
    """
    lib_root = getattr(book_service._library, "library_root", None)  # type: ignore[attr-defined]  # noqa: SLF001
    if lib_root:
        return Path(lib_root)

    library_db_path = book_service._library.calibre_db_path  # type: ignore[attr-defined]  # noqa: SLF001
    library_db_path_obj = Path(library_db_path)
    if library_db_path_obj.is_dir():
        return library_db_path_obj

    return library_db_path_obj.parent


def _find_comic_file(
    book_path: Path,
    format_data: dict,
    book_id: int,
    file_format: str,
) -> Path:
    """Find the comic file on disk.

    Parameters
    ----------
    book_path : Path
        Path to the book directory.
    format_data : dict
        Format data dictionary.
    book_id : int
        Book ID.
    file_format : str
        File format (CBZ, CBR, CB7, CBC).

    Returns
    -------
    Path
        Path to the comic file.

    Raises
    ------
    HTTPException
        If file not found.
    """
    name = format_data.get("name")
    if name:
        file_name = f"{name}.{file_format.lower()}"
    else:
        file_name = f"{book_id}.{file_format.lower()}"

    file_path = book_path / file_name

    if file_path.exists():
        return file_path

    # Try alternative: just the format extension
    alt_file_name = f"{book_id}.{file_format.lower()}"
    alt_file_path = book_path / alt_file_name
    if alt_file_path.exists():
        return alt_file_path

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"file_not_found: {file_path}",
    )


def _get_comic_file_path(
    book_service: BookService,
    book_id: int,
    file_format: str,
) -> Path:
    """Get path to comic book file.

    Parameters
    ----------
    book_service : BookService
        Book service instance.
    book_id : int
        Book ID.
    file_format : str
        File format (CBZ, CBR, CB7, CBC).

    Returns
    -------
    Path
        Path to comic file.

    Raises
    ------
    HTTPException
        If book or format not found.
    """
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

    format_data = _find_format_data(book_with_rels.formats, file_format)
    library_path = _get_library_path(book_service)
    book_path = library_path / book.path

    return _find_comic_file(book_path, format_data, book_id, file_format)


@router.get("/{book_id}/pages")
def list_comic_pages(
    book_id: int,
    session: SessionDep,
    current_user: CurrentUserDep,
    file_format: str = Query(..., description="Comic format (CBZ, CBR, CB7, CBC)"),
) -> list[dict]:
    """List all pages in a comic book archive.

    Parameters
    ----------
    book_id : int
        Book ID.
    file_format : str
        Comic format (CBZ, CBR, CB7, CBC).
    session : Session
        Database session.
    current_user : User
        Current authenticated user.

    Returns
    -------
    list[dict]
        List of page information dictionaries.

    Raises
    ------
    HTTPException
        If book not found, format not found, or permission denied.
    """
    book_service = _get_book_service(session)
    book_with_rels = book_service.get_book_full(book_id)

    if book_with_rels is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="book_not_found",
        )

    # Check permission
    permission_helper = BookPermissionHelper(session)
    permission_helper.check_read_permission(current_user, book_with_rels)

    # Get file path
    file_path = _get_comic_file_path(book_service, book_id, file_format)

    # List pages
    archive_service = ComicArchiveService()
    try:
        pages = archive_service.list_pages(file_path)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    # Return page info
    return [
        {
            "page_number": page.page_number,
            "filename": page.filename,
            "width": page.width,
            "height": page.height,
            "file_size": page.file_size,
        }
        for page in pages
    ]


@router.get("/{book_id}/pages/{page_number}")
def get_comic_page(
    book_id: int,
    page_number: int,
    session: SessionDep,
    current_user: CurrentUserDep,
    file_format: str = Query(..., description="Comic format (CBZ, CBR, CB7, CBC)"),
    thumbnail: bool = Query(
        False,
        description="Return thumbnail instead of full image",
    ),
    max_width: int | None = Query(
        None,
        description="Maximum width for thumbnail (pixels)",
    ),
) -> Response:
    """Get a specific page image from a comic book archive.

    Parameters
    ----------
    book_id : int
        Book ID.
    page_number : int
        Page number (1-based).
    file_format : str
        Comic format (CBZ, CBR, CB7, CBC).
    thumbnail : bool
        Whether to return thumbnail.
    max_width : int | None
        Maximum width for thumbnail.
    session : Session
        Database session.
    current_user : User
        Current authenticated user.

    Returns
    -------
    Response
        Image response with appropriate content type.

    Raises
    ------
    HTTPException
        If book not found, format not found, page not found, or permission denied.
    """
    book_service = _get_book_service(session)
    book_with_rels = book_service.get_book_full(book_id)

    if book_with_rels is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="book_not_found",
        )

    # Check permission
    permission_helper = BookPermissionHelper(session)
    permission_helper.check_read_permission(current_user, book_with_rels)

    # Get file path
    file_path = _get_comic_file_path(book_service, book_id, file_format)

    # Extract page
    archive_service = ComicArchiveService()
    try:
        page = archive_service.get_page(file_path, page_number)
    except (ValueError, IndexError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    # Process image
    image_data = page.image_data
    content_type = "image/jpeg"

    # Create thumbnail if requested
    if thumbnail or max_width:
        try:
            img = Image.open(io.BytesIO(image_data))

            # Calculate thumbnail size
            if max_width and img.width > max_width:
                ratio = max_width / img.width
                new_width = max_width
                new_height = int(img.height * ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Convert to JPEG for response
            buffer = io.BytesIO()
            if img.mode != "RGB":
                img = img.convert("RGB")
            img.save(buffer, format="JPEG", quality=85)
            image_data = buffer.getvalue()
            content_type = "image/jpeg"
        except (OSError, ValueError):
            # If thumbnail generation fails, return original
            # OSError: file operations and I/O errors, ValueError: invalid image data
            pass

    return Response(
        content=image_data,
        media_type=content_type,
        headers={
            "Cache-Control": "public, max-age=3600",
        },
    )


@router.get("/{book_id}/pages/{page_number}/thumbnail")
def get_comic_page_thumbnail(
    book_id: int,
    page_number: int,
    session: SessionDep,
    current_user: CurrentUserDep,
    file_format: str = Query(..., description="Comic format (CBZ, CBR, CB7, CBC)"),
    max_width: int = Query(240, description="Maximum width for thumbnail (pixels)"),
) -> Response:
    """Get a thumbnail of a specific page.

    Convenience endpoint that calls get_comic_page with thumbnail=True.

    Parameters
    ----------
    book_id : int
        Book ID.
    page_number : int
        Page number (1-based).
    file_format : str
        Comic format (CBZ, CBR, CB7, CBC).
    max_width : int
        Maximum width for thumbnail.
    session : Session
        Database session.
    current_user : User
        Current authenticated user.

    Returns
    -------
    Response
        Thumbnail image response.
    """
    return get_comic_page(
        book_id=book_id,
        page_number=page_number,
        file_format=file_format,
        thumbnail=True,
        max_width=max_width,
        session=session,
        current_user=current_user,
    )
